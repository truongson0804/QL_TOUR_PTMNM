from rest_framework import serializers
from .models.tours import Tour

class TourSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tour
        fields = ('id', 'title', 'thumbnail')