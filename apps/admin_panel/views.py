from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.conf import settings
from django.db import models
from django.forms import modelform_factory
from django.forms.widgets import HiddenInput, CheckboxInput
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.core.files.storage import default_storage
from django.conf import settings
import uuid
import os

from apps.bookings.models import Booking
from apps.payments.models import Payment, Status as PaymentStatus, Methods as PaymentMethods
from apps.users.models import User
from apps.tours.forms import TourStopAdminForm
from apps.tours.models.categories import Category
from apps.tours.models.continent import Continent
from apps.tours.models.country import Country
from apps.tours.models.tours import Tour
from apps.tours.models.tour_schedules import TourSchedule
from apps.tours.models.tour_stop import TourStop
from apps.tours.models.route_stop import RouteStop
from apps.tours.models.tour_image import TourImage
from apps.home.models import ContactMessage

from .forms import (
    TourScheduleAdminForm,
    TourDurationRangeAdminForm,
    UserAdminForm,
    ExcelUploadForm,
)


@dataclass(frozen=True)
class ModelConfig:
    key: str
    model: type[models.Model]
    label: str
    list_display: list[str]  # attribute paths. Special: 'latitude'/'longitude' for TourStop.
    search_fields: list[str]
    exclude_form_fields: tuple[str, ...] = ()
    # Optional custom ModelForm class for create/update.
    form_class: Any | None = None


def _perm_code(model: type[models.Model], action: str) -> str:
    # action: view/add/change/delete
    return f"{model._meta.app_label}.{action}_{model._meta.model_name}"


class StaffRequiredMixin(LoginRequiredMixin):
    login_url = "/login/"
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        # Allow access for users with `is_staff` flag or whose `role` field
        # indicates staff/admin. This covers cases where the `role` wasn't
        # synced to `is_staff` for legacy users.
        try:
            user_role = getattr(request.user, 'role', None)
            is_role_staff = user_role in (getattr(User, 'ROLE_STAFF', None), getattr(User, 'ROLE_ADMIN', None))
        except Exception:
            is_role_staff = False

        if not (getattr(request.user, 'is_staff', False) or is_role_staff):
            raise PermissionDenied("Bạn không có quyền truy cập admin.")

        return super().dispatch(request, *args, **kwargs)

    def require_perm(self, request: HttpRequest, model: type[models.Model], action: str) -> None:
        # Superusers bypass checks entirely.
        if getattr(request.user, 'is_superuser', False):
            return

        # Resolve whether the current user should be treated as staff even
        # if `is_staff` flag wasn't synced (fallback to `role`).
        try:
            user_role = getattr(request.user, 'role', None)
            is_role_staff = user_role in (getattr(User, 'ROLE_STAFF', None), getattr(User, 'ROLE_ADMIN', None))
        except Exception:
            is_role_staff = False

        is_staff_user = getattr(request.user, 'is_staff', False) or is_role_staff

        # Allow staff users to perform admin actions (view/add/change/delete)
        # on models that are exposed by this admin panel.
        try:
            admin_models = {cfg.model for cfg in get_model_configs()}
        except Exception:
            admin_models = set()

        if is_staff_user and model in admin_models and action in ('view', 'add', 'change', 'delete'):
            return

        # Fallback: require explicit Django permission.
        if not request.user.has_perm(_perm_code(model, action)):
            raise PermissionDenied("Bạn không có quyền thực hiện thao tác này.")


class AdminDashboardView(StaffRequiredMixin, TemplateView):
    template_name = "admin_panel/dashboard.html"

    @cached_property
    def menu(self) -> list[ModelConfig]:
        return get_model_configs()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["menu"] = self.menu
        return ctx


def get_model_configs() -> list[ModelConfig]:
    # Keep ordering stable and intuitive.
    return [
        ModelConfig(
            key="categories",
            model=Category,
            label="Danh mục",
            list_display=["id", "name"],
            search_fields=["name"],
        ),
        ModelConfig(
            key="continents",
            model=Continent,
            label="Châu lục",
            list_display=["id", "name", "code"],
            search_fields=["name", "code"],
        ),
        ModelConfig(
            key="countries",
            model=Country,
            label="Quốc gia",
            list_display=["id", "name", "code", "continent.name"],
            search_fields=["name", "code", "continent__name"],
        ),
        ModelConfig(
            key="tours",
            model=Tour,
            label="Tour",
            list_display=[
                "id",
                "title",
                "category.name",
                "country.name",
                "price",
                "duration_days",
                "max_people",
                "status",
                "create_at",
            ],
            search_fields=["title", "description", "category__name", "country__name", "status"],
            form_class=TourDurationRangeAdminForm,
        ),
        ModelConfig(
            key="tour_schedules",
            model=TourSchedule,
            label="Lịch trình Tour",
            list_display=["id", "tour.title", "start_day", "end_day", "total_slots"],
            search_fields=["tour__title"],
            form_class=TourScheduleAdminForm,
        ),
        ModelConfig(
            key="tour_stops",
            model=TourStop,
            label="Điểm dừng",
            list_display=["id", "name", "description", "latitude", "longitude"],
            search_fields=["name", "description"],
            form_class=TourStopAdminForm,
        ),
        ModelConfig(
            key="route_stops",
            model=RouteStop,
            label="Điểm tuyến",
            list_display=["id", "tour.title", "stop.name", "order", "stay_minutes"],
            search_fields=["tour__title", "stop__name"],
        ),
        ModelConfig(
            key="users",
            model=User,
            label="Người dùng",
            list_display=["id", "username", "email", "role", "is_active", "last_login"],
            search_fields=["username", "email"],
            form_class=UserAdminForm,
        ),
        ModelConfig(
            key="bookings",
            model=Booking,
            label="Đặt chỗ",
            list_display=[
                "id",
                "user.username",
                "tour_schedule.tour.title",
                "total_people",
                "total_price",
                "status",
                "payment_method",
                "payment_verified",
                "create_at",
            ],
            search_fields=["user__username", "note", "status", "tour_schedule__tour__title"],
        ),
        ModelConfig(
            key="payments",
            model=Payment,
            label="Thanh toán",
            list_display=[
                "id",
                "transaction_id",
                "booking.id",
                "booking.user.username",
                "payment_method",
                "status",
                "amount",
                "paid_at",
            ],
            search_fields=["transaction_id", "booking__user__username", "booking__tour_schedule__tour__title"],
        ),
        ModelConfig(
            key="revenue",
            model=Booking,
            label="Doanh thu",
            list_display=["id", "tour_schedule.tour.title", "total_people", "total_price", "payment_method", "create_at"],
            search_fields=["tour_schedule__tour__title", "user__username"],
        ),
        ModelConfig(
            key="contacts",
            model=ContactMessage,
            label="Tin nhắn liên hệ",
            list_display=["id", "name", "email", "subject", "status", "created_at"],
            search_fields=["name", "email", "subject", "message"],
        ),
    ]


def get_model_config(model_key: str) -> ModelConfig:
    for cfg in get_model_configs():
        if cfg.key == model_key:
            return cfg
    raise PermissionDenied("Không tồn tại module admin này.")


def _get_attr_path(obj: Any, attr_path: str) -> Any:
    # Special computed columns for GIS.
    if attr_path == "latitude":
        loc = getattr(obj, "location", None)
        return getattr(loc, "y", None)
    if attr_path == "longitude":
        loc = getattr(obj, "location", None)
        return getattr(loc, "x", None)

    # For role field, prefer the human-readable display value if available
    if attr_path == 'role' and hasattr(obj, 'get_role_display'):
        try:
            return obj.get_role_display()
        except Exception:
            pass

    current = obj
    for part in attr_path.split("."):
        current = getattr(current, part, None)
        if current is None:
            return None
    return current


def _get_list_display_rows(config: ModelConfig, object_list: list[models.Model]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for obj in object_list:
        row: dict[str, Any] = {}
        for col in config.list_display:
            value = _get_attr_path(obj, col)
            row[col] = value
        rows.append(row)
    return rows


def _column_label(col: str) -> str:
    # Full-path mappings
    full_map = {
        'category.name': 'Danh mục',
        'country.name': 'Quốc gia',
        'continent.name': 'Châu lục',
        'tour.title': 'Tour',
        'tour_schedule.tour.title': 'Tour',
        'user.username': 'Người dùng',
        'booking.user.username': 'Người đặt',
        'booking.id': 'Mã booking',
    }
    if col in full_map:
        return full_map[col]

    if col == "latitude":
        return "Vĩ độ"
    if col == "longitude":
        return "Kinh độ"

    if col == "role":
        return "Vai trò"

    # Show last part of dotted attribute, e.g. `category.name` => `name`.
    last = col.split(".")[-1]

    last_map = {
        'id': 'Mã',
        'name': 'Tên',
        'title': 'Tiêu đề',
        'description': 'Mô tả',
        'price': 'Giá',
        'duration_days': 'Thời lượng',
        'max_people': 'Số lượng',
        'status': 'Trạng thái',
        'create_at': 'Thời gian',
        'created_at': 'Thời gian',
        'start_day': 'Từ ngày',
        'end_day': 'Đến ngày',
        'total_slots': 'Số chỗ',
        'payment_verified': 'Đã thanh toán',
        'total_people': 'Số người',
        'total_price': 'Tổng tiền',
        'payment_method': 'Phương thức thanh toán',
        'transaction_id': 'Mã giao dịch',
        'amount': 'Số tiền',
        'paid_at': 'Thời gian thanh toán',
        'is_active': 'Hoạt động',
        'is_staff': 'Nhân viên',
        'is_active': 'Hoạt động',
        'username': 'Tên đăng nhập',
        'email': 'Email',
        'last_login': 'Đăng nhập cuối',
        'order': 'Thứ tự',
        'distance_km': 'Khoảng cách (km)',
        'stay_minutes': 'Thời gian dừng (phút)',
        'code': 'Mã',
    }

    if last in last_map:
        return last_map[last]

    return last.replace("_", " ").strip().title()


def _build_form_class(config: ModelConfig):
    if config.form_class is not None:
        return config.form_class
    return modelform_factory(config.model, exclude=config.exclude_form_fields)


def _apply_bootstrap_form_widgets(form) -> list[str]:
    """
    Add consistent Bootstrap classes for widgets so templates stay simple.
    Returns list of checkbox field names for special rendering.
    """
    checkbox_fields: list[str] = []
    from django.forms.widgets import Select

    for name, field in form.fields.items():
        widget = field.widget
        if isinstance(widget, HiddenInput):
            continue

        existing = widget.attrs.get("class", "")
        if isinstance(widget, CheckboxInput):
            checkbox_fields.append(name)
            widget.attrs["class"] = " ".join([existing, "form-check-input"]).strip()
        elif isinstance(widget, Select):
            widget.attrs["class"] = " ".join([existing, "form-select"]).strip()
        else:
            widget.attrs["class"] = " ".join([existing, "form-control"]).strip()

    return checkbox_fields


class AdminModelListView(StaffRequiredMixin, View):
    template_name = "admin_panel/model_list.html"
    paginate_by = 10

    def get(self, request: HttpRequest, model_key: str) -> HttpResponse:
        config = get_model_config(model_key)
        self.require_perm(request, config.model, "view")

        qs = config.model.objects.all()

        # Special page: revenue dashboard
        if config.key == 'revenue':
            from django.db.models import Sum, Count
            from django.utils import timezone
            from datetime import date
            from decimal import Decimal

            now = timezone.now()

            bookings_qs = Booking.objects.select_related('user', 'tour_schedule__tour')

            # Filter params
            selected_year = request.GET.get('year', '').strip()
            selected_month = request.GET.get('month', '').strip()

            # Available years for filter dropdown
            try:
                years_qs = Booking.objects.dates('create_at', 'year')
                years = sorted({d.year for d in years_qs}, reverse=True)
            except Exception:
                years = [now.year]

            # Apply filters
            bookings = bookings_qs
            if selected_year:
                try:
                    y = int(selected_year)
                    bookings = bookings.filter(create_at__year=y)
                except Exception:
                    pass
            if selected_month and selected_month != 'all':
                try:
                    m = int(selected_month)
                    bookings = bookings.filter(create_at__month=m)
                except Exception:
                    pass

            # Compute aggregates based on (possibly) filtered queryset
            total = bookings.aggregate(total=Sum('total_price'))['total'] or 0
            today_total = bookings.filter(create_at__date=now.date()).aggregate(total=Sum('total_price'))['total'] or 0
            # If no explicit month filter provided, show current month's revenue
            if selected_year or (selected_month and selected_month != 'all'):
                month_total = bookings.aggregate(total=Sum('total_price'))['total'] or 0
            else:
                month_total = bookings_qs.filter(create_at__year=now.year, create_at__month=now.month).aggregate(total=Sum('total_price'))['total'] or 0

            total_bookings = bookings.count()
            by_status = bookings.values('status').annotate(cnt=Count('id'))

            top_tours = (
                bookings
                .annotate(title=F('tour_schedule__tour__title'))
                .values('title')
                .annotate(revenue=Sum('total_price'), bookings=Count('id'))
                .order_by('-revenue')[:10]
            )

            latest = bookings.order_by('-create_at')[:50]

            # Export filtered revenue if requested
            export = request.GET.get('export')
            if export in ('csv', 'xlsx', 'excel'):
                # Prepare headers and rows from `bookings` queryset
                headers = [
                    'Mã booking', 'Người đặt', 'Tour', 'Khởi hành', 'Số khách', 'Tổng tiền', 'Trạng thái', 'Thời gian đặt', 'Phương thức', 'Mã giao dịch', 'Thời gian thanh toán'
                ]

                if export in ('xlsx', 'excel'):
                    try:
                        from openpyxl import Workbook
                        from openpyxl.utils import get_column_letter
                        from io import BytesIO

                        wb = Workbook()
                        ws = wb.active
                        ws.title = 'Doanh thu'
                        ws.append(headers)

                        total_sum = Decimal('0.00')
                        row_idx = 2
                        for b in bookings:
                            payment = Payment.objects.filter(booking=b).first()
                            pm = getattr(payment, 'payment_method', '') if payment else (getattr(b, 'payment_method', '') or '')
                            tx = getattr(payment, 'transaction_id', '') if payment else ''
                            paid_at = getattr(payment, 'paid_at', None) if payment else None

                            start_day = None
                            try:
                                sd = getattr(b, 'tour_schedule', None)
                                if sd and getattr(sd, 'start_day', None):
                                    start_day = sd.start_day
                            except Exception:
                                start_day = None

                            ws.append([
                                b.id,
                                getattr(b.user, 'username', ''),
                                getattr(getattr(b, 'tour_schedule', None).tour, 'title', '') if getattr(b, 'tour_schedule', None) else '',
                                start_day,
                                getattr(b, 'total_people', ''),
                                float(getattr(b, 'total_price', 0) or 0),
                                getattr(b, 'status', ''),
                                getattr(b, 'create_at', None),
                                pm,
                                tx,
                                paid_at,
                            ])

                            if start_day:
                                try:
                                    cell = ws.cell(row=row_idx, column=4)
                                    cell.number_format = 'yyyy-mm-dd hh:mm'
                                except Exception:
                                    pass
                            if paid_at:
                                try:
                                    cell = ws.cell(row=row_idx, column=11)
                                    cell.number_format = 'yyyy-mm-dd hh:mm:ss'
                                except Exception:
                                    pass
                            try:
                                price_cell = ws.cell(row=row_idx, column=6)
                                price_cell.number_format = '#,##0'
                            except Exception:
                                pass

                            try:
                                total_sum += Decimal(b.total_price)
                            except Exception:
                                pass

                            row_idx += 1

                        # Totals row
                        ws.append([])
                        ws.append(['', '', '', '', 'Tổng doanh thu', float(total_sum)])

                        try:
                            widths = [12, 20, 40, 18, 12, 16, 12, 20, 16, 28, 20]
                            for i, w in enumerate(widths, start=1):
                                ws.column_dimensions[get_column_letter(i)].width = w
                        except Exception:
                            pass

                        out = BytesIO()
                        wb.save(out)
                        out.seek(0)

                        fname = 'revenue'
                        if selected_year:
                            fname += f'_{selected_year}'
                        if selected_month and selected_month != 'all':
                            fname += f'_{selected_month.zfill(2)}'
                        fname += f'_{date.today().isoformat()}.xlsx'

                        resp = HttpResponse(out.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                        resp['Content-Disposition'] = f'attachment; filename="{fname}"'
                        return resp
                    except ImportError:
                        # fall back to CSV if openpyxl isn't available
                        pass

                # CSV fallback
                from io import StringIO
                import csv

                sio = StringIO()
                writer = csv.writer(sio)
                writer.writerow(headers)

                total_sum = Decimal('0.00')
                for b in bookings:
                    payment = Payment.objects.filter(booking=b).first()
                    pm = getattr(payment, 'payment_method', '') if payment else (getattr(b, 'payment_method', '') or '')
                    tx = getattr(payment, 'transaction_id', '') if payment else ''
                    paid_at = ''
                    if payment and getattr(payment, 'paid_at', None):
                        try:
                            paid_at = payment.paid_at.strftime('%Y-%m-%d %H:%M:%S')
                        except Exception:
                            paid_at = str(payment.paid_at)

                    start_day = ''
                    try:
                        sd = getattr(b, 'tour_schedule', None)
                        if sd and getattr(sd, 'start_day', None):
                            start_day = sd.start_day.strftime('%Y-%m-%d %H:%M')
                    except Exception:
                        start_day = ''

                    writer.writerow([
                        b.id,
                        getattr(b.user, 'username', ''),
                        getattr(getattr(b, 'tour_schedule', None).tour, 'title', '') if getattr(b, 'tour_schedule', None) else '',
                        start_day,
                        getattr(b, 'total_people', ''),
                        str(getattr(b, 'total_price', '')),
                        getattr(b, 'status', ''),
                        getattr(b, 'create_at', ''),
                        pm,
                        tx,
                        paid_at,
                    ])

                    try:
                        total_sum += Decimal(b.total_price)
                    except Exception:
                        pass

                writer.writerow([])
                writer.writerow(['', '', '', '', 'Tổng doanh thu', str(total_sum)])

                content = '\ufeff' + sio.getvalue()
                fname = f"revenue{('_'+selected_year) if selected_year else ''}{('_'+selected_month) if selected_month and selected_month!='all' else ''}_{date.today().isoformat()}.csv"
                resp = HttpResponse(content, content_type='text/csv; charset=utf-8')
                resp['Content-Disposition'] = f'attachment; filename="{fname}"'
                return resp

            return render(
                request,
                'admin_panel/revenue.html',
                {
                    'menu': get_model_configs(),
                    'current_key': config.key,
                    'total_revenue': total,
                    'today_revenue': today_total,
                    'month_revenue': month_total,
                    'total_bookings': total_bookings,
                    'by_status': list(by_status),
                    'top_tours': list(top_tours),
                    'latest_bookings': latest,
                    'years': years,
                    'selected_year': selected_year,
                    'selected_month': selected_month,
                },
            )

        # Export handler for payments: generate Excel (.xlsx) or fallback CSV of revenue based on bookings
        export = request.GET.get('export')
        # Export handler for tours: generate Excel (.xlsx) or fallback CSV with headers
        if config.key == 'tours' and export in ('csv', 'xlsx', 'excel'):
            from decimal import Decimal
            from datetime import date

            # Build base queryset and apply search filter if present
            tours_qs = Tour.objects.select_related('category', 'country')
            q = request.GET.get('q', '').strip()
            if q:
                query = Q()
                for field in config.search_fields:
                    query |= Q(**{f"{field}__icontains": q})
                tours_qs = tours_qs.filter(query)

            headers = ['Title', 'Description', 'Price', 'Duration', 'Max_People', 'Category', 'Country', 'Status']

            if export in ('xlsx', 'excel'):
                try:
                    from openpyxl import Workbook
                    from openpyxl.utils import get_column_letter
                    from io import BytesIO

                    wb = Workbook()
                    ws = wb.active
                    ws.title = 'Tours'
                    ws.append(headers)

                    row_idx = 2
                    for t in tours_qs.order_by('-id'):
                        country_val = ''
                        try:
                            if getattr(t, 'country', None):
                                country_val = getattr(t.country, 'code', None) or getattr(t.country, 'name', '')
                        except Exception:
                            country_val = ''

                        price_val = None
                        try:
                            price_val = float(getattr(t, 'price', 0) or 0)
                        except Exception:
                            price_val = None

                        ws.append([
                            getattr(t, 'title', ''),
                            getattr(t, 'description', ''),
                            price_val,
                            getattr(t, 'duration_days', ''),
                            getattr(t, 'max_people', ''),
                            getattr(getattr(t, 'category', None), 'name', ''),
                            country_val,
                            getattr(t, 'status', ''),
                        ])

                        try:
                            if price_val is not None:
                                price_cell = ws.cell(row=row_idx, column=3)
                                price_cell.number_format = '#,##0.00'
                        except Exception:
                            pass

                        row_idx += 1

                    # Set reasonable column widths
                    try:
                        widths = [40, 60, 12, 18, 12, 20, 20, 12]
                        for i, w in enumerate(widths, start=1):
                            ws.column_dimensions[get_column_letter(i)].width = w
                    except Exception:
                        pass

                    out = BytesIO()
                    wb.save(out)
                    out.seek(0)

                    fname = f"tours_{date.today().isoformat()}.xlsx"
                    resp = HttpResponse(out.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    resp['Content-Disposition'] = f'attachment; filename="{fname}"'
                    return resp
                except ImportError:
                    # fall back to CSV if openpyxl isn't available
                    pass

            # CSV fallback (UTF-8 BOM so Excel shows Unicode correctly)
            from io import StringIO
            import csv

            sio = StringIO()
            writer = csv.writer(sio)
            writer.writerow(headers)

            for t in tours_qs.order_by('-id'):
                country_val = ''
                try:
                    if getattr(t, 'country', None):
                        country_val = getattr(t.country, 'code', None) or getattr(t.country, 'name', '')
                except Exception:
                    country_val = ''

                price_val = ''
                try:
                    price_val = str(getattr(t, 'price', '') or '')
                except Exception:
                    price_val = ''

                writer.writerow([
                    getattr(t, 'title', ''),
                    getattr(t, 'description', ''),
                    price_val,
                    getattr(t, 'duration_days', ''),
                    getattr(t, 'max_people', ''),
                    getattr(getattr(t, 'category', None), 'name', ''),
                    country_val,
                    getattr(t, 'status', ''),
                ])

            content = '\ufeff' + sio.getvalue()
            resp = HttpResponse(content, content_type='text/csv; charset=utf-8')
            resp['Content-Disposition'] = f'attachment; filename="tours_{date.today().isoformat()}.csv"'
            return resp
        if config.key == 'payments' and export in ('csv', 'xlsx', 'excel'):
            # Only include bookings that have been confirmed and verified (exclude pending / cancelled)
            from decimal import Decimal
            from datetime import date

            bookings = Booking.objects.filter(status='CONFIRMED', payment_verified=True).select_related('user', 'tour_schedule__tour')

            # Prefer to generate real .xlsx files (better unicode & date handling) if openpyxl is available.
            if export in ('xlsx', 'excel'):
                try:
                    from openpyxl import Workbook
                    from openpyxl.utils import get_column_letter
                    from io import BytesIO

                    wb = Workbook()
                    ws = wb.active
                    ws.title = 'Doanh thu'

                    headers = [
                        'Mã booking', 'Người đặt', 'Tour', 'Khởi hành', 'Số khách', 'Tổng tiền', 'Phương thức', 'Mã giao dịch', 'Thời gian thanh toán'
                    ]
                    ws.append(headers)

                    total = Decimal('0.00')
                    row_idx = 2
                    for b in bookings:
                        payment = Payment.objects.filter(booking=b).first()
                        pm = getattr(payment, 'payment_method', '') if payment else (getattr(b, 'payment_method', '') or '')
                        tx = getattr(payment, 'transaction_id', '') if payment else ''
                        paid_at = getattr(payment, 'paid_at', None) if payment else None

                        start_day = None
                        try:
                            sd = getattr(b, 'tour_schedule', None)
                            if sd and getattr(sd, 'start_day', None):
                                start_day = sd.start_day
                        except Exception:
                            start_day = None

                        # Write row; openpyxl will handle datetimes and unicode correctly
                        ws.append([
                            b.id,
                            getattr(b.user, 'username', ''),
                            getattr(getattr(b, 'tour_schedule', None).tour, 'title', '') if getattr(b, 'tour_schedule', None) else '',
                            start_day,
                            getattr(b, 'total_people', ''),
                            float(getattr(b, 'total_price', 0) or 0),
                            pm,
                            tx,
                            paid_at,
                        ])

                        # Apply cell formats for date/time and numbers
                        if start_day:
                            cell = ws.cell(row=row_idx, column=4)
                            cell.number_format = 'yyyy-mm-dd hh:mm'
                        if paid_at:
                            cell = ws.cell(row=row_idx, column=9)
                            cell.number_format = 'yyyy-mm-dd hh:mm:ss'
                        # price formatting
                        try:
                            price_cell = ws.cell(row=row_idx, column=6)
                            price_cell.number_format = '#,##0'
                        except Exception:
                            pass

                        try:
                            total += Decimal(b.total_price)
                        except Exception:
                            pass

                        row_idx += 1

                    # Totals row
                    ws.append([])
                    ws.append(['', '', '', '', 'Tổng doanh thu', float(total)])

                    # Set reasonable column widths
                    try:
                        widths = [12, 20, 40, 18, 12, 16, 16, 28, 20]
                        for i, w in enumerate(widths, start=1):
                            ws.column_dimensions[get_column_letter(i)].width = w
                    except Exception:
                        pass

                    out = BytesIO()
                    wb.save(out)
                    out.seek(0)

                    resp = HttpResponse(out.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    filename = f"revenue_{date.today().isoformat()}.xlsx"
                    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
                    return resp
                except ImportError:
                    # openpyxl not available: fall back to CSV below
                    pass

            # Fallback: produce a UTF-8 CSV with BOM so Excel on Windows shows Vietnamese correctly
            from io import StringIO
            import csv

            sio = StringIO()
            writer = csv.writer(sio)
            # Header row
            writer.writerow([
                'Mã booking', 'Người đặt', 'Tour', 'Khởi hành', 'Số khách', 'Tổng tiền', 'Phương thức', 'Mã giao dịch', 'Thời gian thanh toán'
            ])

            total = Decimal('0.00')
            for b in bookings:
                payment = Payment.objects.filter(booking=b).first()
                pm = getattr(payment, 'payment_method', '') if payment else (getattr(b, 'payment_method', '') or '')
                tx = getattr(payment, 'transaction_id', '') if payment else ''
                paid_at = ''
                if payment and getattr(payment, 'paid_at', None):
                    try:
                        paid_at = payment.paid_at.strftime('%Y-%m-%d %H:%M:%S')
                    except Exception:
                        paid_at = str(payment.paid_at)

                start_day = ''
                try:
                    sd = getattr(b, 'tour_schedule', None)
                    if sd and getattr(sd, 'start_day', None):
                        start_day = sd.start_day.strftime('%Y-%m-%d %H:%M')
                except Exception:
                    start_day = ''

                writer.writerow([
                    b.id,
                    getattr(b.user, 'username', ''),
                    getattr(getattr(b, 'tour_schedule', None).tour, 'title', '') if getattr(b, 'tour_schedule', None) else '',
                    start_day,
                    getattr(b, 'total_people', ''),
                    str(getattr(b, 'total_price', '')),
                    pm,
                    tx,
                    paid_at,
                ])

                try:
                    total += Decimal(b.total_price)
                except Exception:
                    pass

            # Totals row
            writer.writerow([])
            writer.writerow(['', '', '', '', 'Tổng doanh thu', str(total)])

            # Prepend UTF-8 BOM so Excel displays Unicode correctly
            content = '\ufeff' + sio.getvalue()
            resp = HttpResponse(content, content_type='text/csv; charset=utf-8')
            filename = f"revenue_{date.today().isoformat()}.csv"
            resp['Content-Disposition'] = f'attachment; filename="{filename}"'
            return resp

        # For bookings list in admin, only show bookings that have not been verified/approved yet.
        # Bookings that have been verified should appear under the Payments section instead.
        if config.key == 'bookings':
            try:
                qs = qs.filter(payment_verified=False)
            except Exception:
                # If the model doesn't have the field for some reason, fall back to all
                qs = config.model.objects.all()

        q = request.GET.get("q", "").strip()
        if q:
            query = Q()
            for field in config.search_fields:
                # Best-effort search on text fields.
                query |= Q(**{f"{field}__icontains": q})
            qs = qs.filter(query)

        # Simple ordering by GET `order` (e.g. `id` or `-id`)
        order = request.GET.get("order") or "-id"
        if order.lstrip("-").isidentifier():
            qs = qs.order_by(order)

        paginator = Paginator(qs, self.paginate_by)
        page_number = request.GET.get("page") or 1
        page_obj = paginator.get_page(page_number)

        rows = _get_list_display_rows(config, list(page_obj.object_list))
        columns = [{"key": col, "label": _column_label(col)} for col in config.list_display]

        return render(
            request,
            self.template_name,
            {
                "menu": get_model_configs(),
                "current_key": config.key,
                "config": config,
                "page_obj": page_obj,
                "rows": rows,
                "columns": columns,
                "q": q,
            },
        )


class AdminModelImportView(StaffRequiredMixin, View):
    """Simple Excel/CSV import handler for admin panel.

    Currently supports importing `tours` rows with columns like:
    Title, Description, Price, Duration, Max_People, Category, Country, Status
    """
    template_name = "admin_panel/import.html"

    def get(self, request: HttpRequest, model_key: str) -> HttpResponse:
        config = get_model_config(model_key)
        self.require_perm(request, config.model, "add")
        form = ExcelUploadForm()
        return render(request, self.template_name, {"menu": get_model_configs(), "current_key": config.key, "config": config, "form": form})

    def post(self, request: HttpRequest, model_key: str) -> HttpResponse:
        config = get_model_config(model_key)
        self.require_perm(request, config.model, "add")

        form = ExcelUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {"menu": get_model_configs(), "current_key": config.key, "config": config, "form": form})

        f = form.cleaned_data["file"]
        name = f.name.lower()

        created = 0
        errors: list[str] = []

        try:
            if name.endswith('.csv'):
                import csv
                from io import StringIO

                data = f.read().decode('utf-8-sig')
                sio = StringIO(data)
                reader = csv.reader(sio)
                rows = list(reader)
                if not rows:
                    raise ValueError("Tệp CSV trống")
                headers = [c.strip().lower() for c in rows[0]]
                data_rows = rows[1:]
                iterable = enumerate(data_rows, start=2)
                get_cell = lambda r, idx: r[idx] if idx < len(r) else None
            else:
                from openpyxl import load_workbook
                from io import BytesIO

                wb = load_workbook(filename=BytesIO(f.read()), read_only=True, data_only=True)
                ws = wb.active
                rows = list(ws.iter_rows(values_only=True))
                if not rows:
                    raise ValueError("Tệp Excel trống")
                headers = [str(c).strip().lower() if c is not None else "" for c in rows[0]]
                data_rows = rows[1:]
                iterable = enumerate(data_rows, start=2)
                get_cell = lambda r, idx: r[idx] if idx < len(r) else None

            # helper mapping
            def get_val(row, key_candidates):
                for k in key_candidates:
                    if k in headers:
                        try:
                            return get_cell(row, headers.index(k))
                        except Exception:
                            return None
                return None

            from decimal import Decimal
            from django.db import transaction
            for row_idx, row in iterable:
                try:
                    # common header candidates
                    title = get_val(row, ['title', 'tiêu đề', 'name', 'tên'])
                    description = get_val(row, ['description', 'mô tả', 'desc'])
                    price = get_val(row, ['price', 'giá'])
                    duration = get_val(row, ['duration', 'duration_days', 'thời lượng'])
                    max_people = get_val(row, ['max_people', 'số lượng', 'max people'])
                    category_name = get_val(row, ['category', 'danh mục'])
                    country_name = get_val(row, ['country', 'quốc gia'])
                    status = get_val(row, ['status', 'trạng thái'])

                    if not title:
                        errors.append(f"Dòng {row_idx}: Thiếu tiêu đề")
                        continue

                    # Normalize/convert
                    try:
                        price_val = Decimal(str(price)) if price not in (None, '') else None
                    except Exception:
                        price_val = None

                    try:
                        max_people_val = int(max_people) if max_people not in (None, '') else None
                    except Exception:
                        max_people_val = None

                    # resolve category
                    cat_obj = None
                    if category_name:
                        try:
                            cat_name = str(category_name).strip()
                            cat_obj, _ = Category.objects.get_or_create(name=cat_name)
                        except Exception:
                            cat_obj = None

                    # resolve country
                    country_obj = None
                    if country_name:
                        try:
                            cstr = str(country_name).strip()
                            if len(cstr) == 2:
                                country_obj = Country.objects.filter(code__iexact=cstr).first()
                            if not country_obj:
                                country_obj = Country.objects.filter(name__iexact=cstr).first()
                            if not country_obj:
                                country_obj = Country.objects.filter(name__icontains=cstr).first()
                        except Exception:
                            country_obj = None

                    tour_kwargs = {
                        'title': str(title).strip(),
                        'description': str(description).strip() if description not in (None, '') else '',
                    }
                    if price_val is not None:
                        tour_kwargs['price'] = price_val
                    if duration not in (None, ''):
                        tour_kwargs['duration_days'] = str(duration).strip()
                    if max_people_val is not None:
                        tour_kwargs['max_people'] = max_people_val
                    if cat_obj is not None:
                        tour_kwargs['category'] = cat_obj
                    if country_obj is not None:
                        tour_kwargs['country'] = country_obj
                    if status not in (None, ''):
                        tour_kwargs['status'] = str(status).strip()

                    # create record
                    with transaction.atomic():
                        obj = Tour.objects.create(**tour_kwargs)
                        created += 1

                except Exception as e:
                    errors.append(f"Dòng {row_idx}: {str(e)}")

        except Exception as e:
            messages.error(request, f"Lỗi khi đọc tệp: {e}")
            return redirect(reverse('admin_panel:model_list', args=[config.key]))

        if created:
            messages.success(request, f"Đã tạo {created} bản ghi cho {config.label}.")
        if errors:
            # show up to first 10 errors
            preview = '\n'.join(errors[:10])
            messages.warning(request, f"Có {len(errors)} lỗi. Một vài lỗi: {preview}")

        return redirect(reverse('admin_panel:model_list', args=[config.key]))


class AdminModelCreateView(StaffRequiredMixin, View):
    template_name = "admin_panel/model_form.html"

    def get(self, request: HttpRequest, model_key: str) -> HttpResponse:
        config = get_model_config(model_key)
        self.require_perm(request, config.model, "add")
        form_class = _build_form_class(config)
        form = form_class()
        checkbox_fields = _apply_bootstrap_form_widgets(form)
        # Hide role assignment from non-superuser staff members
        if config.key == 'users' and request.user.is_staff and not request.user.is_superuser:
            if 'role' in form.fields:
                form.fields.pop('role', None)
        return render(
            request,
            self.template_name,
            {
                "menu": get_model_configs(),
                "current_key": config.key,
                "config": config,
                "form": form,
                "mode": "create",
                "checkbox_fields": checkbox_fields,
            },
        )

    def post(self, request: HttpRequest, model_key: str) -> HttpResponse:
        config = get_model_config(model_key)
        self.require_perm(request, config.model, "add")
        form_class = _build_form_class(config)
        form = form_class(request.POST, request.FILES)
        checkbox_fields = _apply_bootstrap_form_widgets(form)
        if form.is_valid():
            # If creating a User and the current admin is not a superuser,
            # force the role to plain user so staff cannot assign roles.
            if config.key == 'users' and not request.user.is_superuser:
                try:
                    obj = form.save(commit=False)
                    if hasattr(obj, 'role'):
                        obj.role = getattr(obj, 'ROLE_USER', 'user')
                    if hasattr(obj, 'apply_role_flags'):
                        obj.apply_role_flags()
                    obj.save()
                    form.save_m2m()
                except Exception:
                    obj = form.save()
            else:
                obj = form.save()
            # If this is a Tour, handle multiple extra images uploaded via `extra_images`
            if config.key == 'tours':
                files = request.FILES.getlist('extra_images')
                for f in files:
                    try:
                        TourImage.objects.create(tour=obj, image=f)
                    except Exception:
                        # ignore individual save errors but continue
                        pass

            messages.success(request, f"Đã tạo mới {config.label} thành công.")
            return redirect(reverse("admin_panel:model_list", kwargs={"model_key": config.key}))
        return render(
            request,
            self.template_name,
            {
                "menu": get_model_configs(),
                "current_key": config.key,
                "config": config,
                "form": form,
                "mode": "create",
                "checkbox_fields": checkbox_fields,
            },
        )


class AdminModelUpdateView(StaffRequiredMixin, View):
    template_name = "admin_panel/model_form.html"

    def get(self, request: HttpRequest, model_key: str, pk: int) -> HttpResponse:
        config = get_model_config(model_key)
        self.require_perm(request, config.model, "change")
        obj = get_object_or_404(config.model, pk=pk)
        form_class = _build_form_class(config)
        form = form_class(instance=obj)
        checkbox_fields = _apply_bootstrap_form_widgets(form)
        # Hide role assignment input from non-superuser staff members
        if config.key == 'users' and request.user.is_staff and not request.user.is_superuser:
            if 'role' in form.fields:
                form.fields.pop('role', None)
        return render(
            request,
            self.template_name,
            {
                "menu": get_model_configs(),
                "current_key": config.key,
                "config": config,
                "form": form,
                "mode": "edit",
                "obj": obj,
                "checkbox_fields": checkbox_fields,
            },
        )

    def post(self, request: HttpRequest, model_key: str, pk: int) -> HttpResponse:
        config = get_model_config(model_key)
        self.require_perm(request, config.model, "change")
        obj = get_object_or_404(config.model, pk=pk)
        original_role = getattr(obj, 'role', None)
        # Special-case: reply action for contact messages (send email without validating model form)
        if config.key == "contacts" and "reply" in request.POST:
            reply_text = request.POST.get("reply_message", "").strip()
            if not reply_text:
                messages.error(request, "Vui lòng nhập nội dung phản hồi.")
                return redirect(reverse("admin_panel:model_edit", kwargs={"model_key": config.key, "pk": obj.id}))

            recipient = getattr(obj, "email", None)
            if not recipient:
                messages.error(request, "Không tìm thấy email người nhận.")
                return redirect(reverse("admin_panel:model_edit", kwargs={"model_key": config.key, "pk": obj.id}))

            subject = f"Phản hồi: {getattr(obj, 'subject', '') or ''}"
            from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(settings, "SERVER_EMAIL", "no-reply@localhost")
            try:
                send_mail(subject, reply_text, from_email, [recipient], fail_silently=False)
                # mark as read if model supports a status flag
                try:
                    obj.status = getattr(obj, 'STATUS_READ', 'READ')
                    obj.save(update_fields=['status'])
                except Exception:
                    pass
                messages.success(request, "Đã gửi phản hồi tới người dùng.")
            except Exception as e:
                messages.error(request, f"Lỗi khi gửi email: {e}")
            return redirect(reverse("admin_panel:model_edit", kwargs={"model_key": config.key, "pk": obj.id}))

        # Special-case: verify payment for bookings (quick action triggered by button)
        if config.key == 'bookings' and 'verify_payment' in request.POST:
            # permission already enforced above
            try:
                val = request.POST.get('verify_payment')
                # treat any truthy value as verify
                if val and val != '0' and val.lower() != 'false':
                    obj.payment_verified = True
                    obj.paid_at = timezone.now()
                    # if booking still pending, mark confirmed
                    if getattr(obj, 'status', None) == 'PENDING':
                        obj.status = 'CONFIRMED'
                    obj.save(update_fields=['payment_verified', 'paid_at', 'status'])
                    messages.success(request, 'Đã duyệt thanh toán thành công.')
                    # Create or update a Payment record so it appears in payments admin
                    try:
                        payment = Payment.objects.filter(booking=obj).first()
                        # map booking.payment_method to payment method choices
                        pm = (getattr(obj, 'payment_method', None) or '').lower() if getattr(obj, 'payment_method', None) else ''
                        if 'cash' in pm or pm == 'cod':
                            mapped_method = PaymentMethods.COD
                        else:
                            # treat transfer/bank/credit/vnpay as VNPay for admin purposes
                            mapped_method = PaymentMethods.VNPay

                        if payment:
                            payment.payment_method = mapped_method
                            payment.amount = obj.total_price
                            payment.status = PaymentStatus.PAID
                            if not payment.transaction_id:
                                payment.transaction_id = uuid.uuid4().hex
                            payment.save()
                        else:
                            Payment.objects.create(
                                booking=obj,
                                payment_method=mapped_method,
                                amount=obj.total_price,
                                status=PaymentStatus.PAID,
                                transaction_id=uuid.uuid4().hex,
                            )
                    except Exception:
                        # Do not block approval if payment record creation fails
                        pass
                else:
                    obj.payment_verified = False
                    obj.paid_at = None
                    obj.save(update_fields=['payment_verified', 'paid_at'])
                    messages.success(request, 'Đã hủy duyệt thanh toán.')
                    # mark related Payment as unpaid if exists
                    try:
                        payment = Payment.objects.filter(booking=obj).first()
                        if payment:
                            payment.status = PaymentStatus.UNPAID
                            payment.save()
                    except Exception:
                        pass
            except Exception as e:
                messages.error(request, f'Lỗi khi duyệt thanh toán: {e}')
            return redirect(reverse("admin_panel:model_edit", kwargs={"model_key": config.key, "pk": obj.id}))

        # Default: validate and save the model form
        form_class = _build_form_class(config)
        form = form_class(request.POST, request.FILES, instance=obj)
        checkbox_fields = _apply_bootstrap_form_widgets(form)
        if form.is_valid():
            # If editing a User and current admin is not a superuser,
            # prevent changing the role value.
            if config.key == 'users' and not request.user.is_superuser:
                new_role = form.cleaned_data.get('role') if 'role' in form.cleaned_data else None
                if new_role is not None and new_role != original_role:
                    form.add_error('role', 'Bạn không có quyền thay đổi phân quyền người dùng.')
                    return render(
                        request,
                        self.template_name,
                        {
                            "menu": get_model_configs(),
                            "current_key": config.key,
                            "config": config,
                            "form": form,
                            "mode": "edit",
                            "obj": obj,
                            "checkbox_fields": checkbox_fields,
                        },
                    )

            obj_saved = form.save()
            # If this is a Tour, save any newly uploaded extra images
            if config.key == 'tours':
                files = request.FILES.getlist('extra_images')
                for f in files:
                    try:
                        TourImage.objects.create(tour=obj_saved, image=f)
                    except Exception:
                        pass

            messages.success(request, f"Đã cập nhật {config.label} thành công.")
            return redirect(reverse("admin_panel:model_list", kwargs={"model_key": config.key}))
        return render(
            request,
            self.template_name,
            {
                "menu": get_model_configs(),
                "current_key": config.key,
                "config": config,
                "form": form,
                "mode": "edit",
                "obj": obj,
                "checkbox_fields": checkbox_fields,
            },
        )


class AdminModelDeleteView(StaffRequiredMixin, View):
    template_name = "admin_panel/model_confirm_delete.html"

    def get(self, request: HttpRequest, model_key: str, pk: int) -> HttpResponse:
        config = get_model_config(model_key)
        self.require_perm(request, config.model, "delete")
        obj = get_object_or_404(config.model, pk=pk)
        return render(
            request,
            self.template_name,
            {
                "menu": get_model_configs(),
                "current_key": config.key,
                "config": config,
                "obj": obj,
            },
        )

    def post(self, request: HttpRequest, model_key: str, pk: int) -> HttpResponse:
        config = get_model_config(model_key)
        self.require_perm(request, config.model, "delete")
        obj = get_object_or_404(config.model, pk=pk)
        obj.delete()
        messages.success(request, f"Đã xóa {config.label} thành công.")
        return redirect(reverse("admin_panel:model_list", kwargs={"model_key": config.key}))


@require_POST
@login_required
def ckeditor_upload(request):
    """Handle image upload from CKEditor5 SimpleUploadAdapter.

    Expects file field named 'upload'. Returns JSON: { 'url': '<file-url>' }.
    """
    # Only staff may upload via admin panel
    if not request.user.is_staff:
        return HttpResponseForbidden("Không có quyền tải ảnh.")

    upload = request.FILES.get("upload")
    if not upload:
        return HttpResponseBadRequest("No file uploaded")

    # Build safe filename
    name, ext = os.path.splitext(upload.name)
    filename = f"uploads/ckeditor/{uuid.uuid4().hex}{ext}"

    saved_path = default_storage.save(filename, upload)
    url = default_storage.url(saved_path)

    # Return URL that CKEditor can insert
    return JsonResponse({"url": url})

