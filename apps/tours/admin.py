from django.contrib import admin
from django.contrib.gis.geos import Point

from .forms import TourStopAdminForm

from .models.categories import Category
from .models.continent import Continent
from .models.country import Country
from .models.route_stop import RouteStop
from .models.tour_schedules import TourSchedule
from .models.tour_stop import TourStop
from .models.tours import Tour


@admin.register(Category)
class CategoriesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Tour)
class ToursAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'category',
        'country',
        'price',
        'duration_days',
        'max_people',
        'status',
        'create_at',
    )
    search_fields = ('title', 'description', 'category__name', 'country__name')
    list_filter = ('status', 'category', 'country')
    ordering = ('-create_at',)


@admin.register(TourSchedule)
class TourSchedulesAdmin(admin.ModelAdmin):
    list_display = ('id', 'tour', 'start_day', 'end_day', 'total_slots')
    search_fields = ('tour__title',)
    list_filter = ('tour__category', 'start_day', 'end_day')
    ordering = ('-start_day',)


@admin.register(Country)
class CountriesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'continent')
    search_fields = ('name', 'code')
    list_filter = ('continent',)
    ordering = ('name',)


@admin.register(Continent)
class ContinentsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code')
    search_fields = ('name', 'code')
    ordering = ('name',)
@admin.register(RouteStop)
class RoutesStopAdmin(admin.ModelAdmin):
    list_display = ('id', 'tour', 'stop', 'order', 'stay_minutes')
    search_fields = ('tour__title', 'stop__name')
    ordering = ('tour', 'order')