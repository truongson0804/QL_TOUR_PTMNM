# api.py
from rest_framework.views import APIView
from rest_framework.response import Response
from .models.route_stop import RouteStop
import json

class TourMapAPI(APIView):
    def get(self, request, id):
        # Lấy tất cả RouteStop của tour, sắp xếp theo order
        route_stops = (
            RouteStop.objects
            .filter(tour=id)
            .select_related("stop")
            .order_by("order")
        )

        if not route_stops.exists():
            # Chưa có stops -> trả về empty feature collection
            return Response({"type": "FeatureCollection", "features": []})

        features = []

        # Thêm tất cả stops
        for rs in route_stops:
            stop = rs.stop
            if not stop or not hasattr(stop, 'location'):
                continue
                
            features.append(
                {
                    "type": "Feature",
                    "geometry": json.loads(stop.location.geojson),
                    "properties": {
                        "type": "stop",
                        "name": stop.name,
                        "order": rs.order,
                        "description": stop.description,
                        "id": stop.id,
                        "image": request.build_absolute_uri(stop.image.url) if getattr(stop, 'image', None) and getattr(stop.image, 'url', None) else None,
                    },
                }
            )

        return Response({"type": "FeatureCollection", "features": features})


class ToursOverviewAPI(APIView):
    """Return a simple list of tours with a representative lat/lng (first stop) and metadata.

    This is used by the map page to show available tours as markers and list items.
    """
    def get(self, request):
        from .models.tours import Tour

        out = []
        tours = Tour.objects.filter(status='ACTIVE').order_by('-create_at')
        for tour in tours:
            lat = None
            lng = None
            img_url = None

            # Lấy RouteStop đầu tiên của tour (được sắp xếp theo order)
            first_route_stop = (
                RouteStop.objects
                .filter(tour=tour)
                .select_related('stop')
                .order_by('order')
                .first()
            )
            
            if first_route_stop and first_route_stop.stop and hasattr(first_route_stop.stop, 'location'):
                try:
                    geom = json.loads(first_route_stop.stop.location.geojson)
                    coords = geom.get('coordinates', None)
                    if coords and len(coords) >= 2:
                        lng, lat = coords[0], coords[1]
                        if getattr(first_route_stop.stop, 'image', None) and getattr(first_route_stop.stop.image, 'url', None):
                            img_url = request.build_absolute_uri(first_route_stop.stop.image.url)
                except Exception:
                    pass

            # fallback to tour thumbnail
            if not img_url and getattr(tour, 'thumbnail', None) and getattr(tour.thumbnail, 'url', None):
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
                'lat': lat,
                'lng': lng,
                'img': img_url or request.build_absolute_uri('/static/images/placeholder-tour.svg'),
                'priceLabel': price_label,
                'location': str(tour.country) if getattr(tour, 'country', None) else '',
            })

        return Response(out)
