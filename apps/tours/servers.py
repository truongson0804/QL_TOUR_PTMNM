# api.py
from rest_framework.views import APIView
from rest_framework.response import Response


class TourMapAPI(APIView):
    def get(self, request, id):
        # RouteStop model removed; return empty FeatureCollection
        return Response({"type": "FeatureCollection", "features": []})


class ToursOverviewAPI(APIView):
    """Return a simple list of tours with metadata. No lat/lng (RouteStop removed)."""
    def get(self, request):
        from .models.tours import Tour

        out = []
        tours = Tour.objects.filter(status='ACTIVE').order_by('-create_at')
        for tour in tours:
            img_url = None
            # fallback to tour thumbnail
            if getattr(tour, 'thumbnail', None) and getattr(tour.thumbnail, 'url', None):
                try:
                    img_url = request.build_absolute_uri(tour.thumbnail.url)
                except Exception:
                    img_url = None

            # price label short format
            price_label = ''
            try:
                p = float(tour.price)
                if p >= 1000000:
                    price_label = f"{p/1000000:.1f}M ₫"
                else:
                    price_label = f"{int(p):,} ₫".replace(',', '.')
            except Exception:
                price_label = ''

            out.append({
                'id': tour.id,
                'title': tour.title,
                'lat': None,
                'lng': None,
                'img': img_url or request.build_absolute_uri('/static/images/placeholder-tour.svg'),
                'priceLabel': price_label,
                'location': str(tour.country) if getattr(tour, 'country', None) else '',
            })

        return Response(out)
