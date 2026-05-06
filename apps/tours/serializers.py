from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models.tours import Tour
import json

class TourSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Tour
        geo_field = 'location'
        fields = ('id', 'title', 'thumbnail')