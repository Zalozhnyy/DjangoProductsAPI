from rest_framework import serializers
import datetime

from .models import ItemModel


class ItemSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=True, allow_null=False)
    parentId = serializers.UUIDField(required=True, allow_null=True)

    name = serializers.CharField(max_length=255, required=True, allow_null=False)
    type = serializers.CharField(max_length=20, required=True, allow_null=False)
    price = serializers.IntegerField(allow_null=True)
    date = serializers.DateTimeField()

    class Meta:
        model = ItemModel
        fields = ['id', 'name', 'parentId', "date", "price", 'type']

    def validate_parentId(self, value):
        if value is None:
            return value

        category_instance = ItemModel.objects.get(pk=value)
        return category_instance

    def create(self, validated_data):
        # if validated_data['parentId'] is not None:
        #     validated_data["parentId"] = ItemModel.objects.get(pk=validated_data['parentId'])

        return ItemModel.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.date = validated_data.get('date', instance.date)
        instance.price = validated_data.get('price', instance.price)
        instance.type = validated_data.get('type', instance.type)
        instance.parentId = validated_data.get('parentId', instance.parentId)

        instance.save()
        return instance
