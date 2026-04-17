from rest_framework import serializers
from .models import Table, FloorSection, FloorDecor

class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = '__all__'

class FloorDecorSerializer(serializers.ModelSerializer):
    class Meta:
        model = FloorDecor
        fields = '__all__'

class FloorSectionSerializer(serializers.ModelSerializer):
    tables = TableSerializer(many=True, read_only=True)
    decor_items = FloorDecorSerializer(many=True, read_only=True)
    
    class Meta:
        model = FloorSection
        fields = ['id', 'name', 'tables', 'decor_items']
