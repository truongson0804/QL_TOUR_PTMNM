from django.shortcuts import render
from django.http import JsonResponse
from ..tours.models.tour_stop import TourStop
import json


# Create your views here.
def gis_map(request):
    return render(request, 'map.html')


def stops_geojson(request):
    """Return all TourStop points as a GeoJSON FeatureCollection."""
    features = []
    for stop in TourStop.objects.all():
        if not stop.location:
            continue
        try:
            geom = json.loads(stop.location.geojson)
        except Exception:
            continue
        img_url = None
        try:
            if getattr(stop, 'image') and stop.image:
                img_url = stop.image.url
        except Exception:
            img_url = None

        features.append({
            "type": "Feature",
            "geometry": geom,
            "properties": {
                "id": stop.id,
                "name": stop.name,
                "description": stop.description or "",
                "image": img_url or "",
            },
        })
    return JsonResponse({"type": "FeatureCollection", "features": features})