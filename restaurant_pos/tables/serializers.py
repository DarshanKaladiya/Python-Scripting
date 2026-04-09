from rest_framework import serializers
from .models import Table, FloorSection

class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ['id', 'section', 'name', 'capacity', 'status', 'x_pos', 'y_pos', 'width', 'height', 'shape']

class FloorSectionSerializer(serializers.ModelSerializer):
    tables = TableSerializer(many=True, read_only=True)
    
    class Meta:
        model = FloorSection
        fields = ['id', 'name', 'tables']
