from django.urls import path
from .views import gis_map, stops_geojson

urlpatterns = [
    path('show_map/', gis_map, name='show_map'),
    path('stops_geojson/', stops_geojson, name='stops_geojson'),
]