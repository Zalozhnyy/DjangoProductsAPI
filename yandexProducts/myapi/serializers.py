from rest_framework import serializers
from rest_framework_recursive.fields import RecursiveField

from .models import *


class CategorySerializer(serializers.Serializer):
    id = serializers.UUIDField(required=True, allow_null=False)
    name = serializers.CharField(max_length=255, required=True, allow_null=False)
    price = serializers.IntegerField(allow_null=True, required=False)
    parentId = serializers.UUIDField(required=True, allow_null=True)
    date = serializers.DateTimeField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'parentId', "date"]

    def create(self, validated_data):
        if validated_data['parentId']:
            validated_data['parentId'] = Category.objects.get(pk=validated_data['parentId'])
        return Category.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.date = validated_data.get('date', instance.date)

        parentId = validated_data.get('parentId', instance.parentId)
        if parentId is not None:
            instance.parentId = Category.objects.get(pk=parentId)
        else:
            instance.parentId = parentId

        instance.save()
        return instance


class ProductSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=True, allow_null=False)
    name = serializers.CharField(max_length=255, required=True, allow_null=False)
    price = serializers.IntegerField(allow_null=False, required=True)
    parentId = serializers.UUIDField(required=True, allow_null=False)
    date = serializers.DateTimeField()

    class Meta:
        model = ProductItem
        fields = ['id', 'name', 'parentId', "date", "price"]

    def validate_parentId(self, value):
        category_instance = Category.objects.filter(pk=value)

        if not category_instance:
            raise serializers.ValidationError("Parent do not exist")

        return value

    def create(self, validated_data):
        validated_data["parentId"] = Category.objects.get(pk=validated_data['parentId'])
        return ProductItem.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.date = validated_data.get('date', instance.date)
        instance.price = validated_data.get('price', instance.price)

        parentId = validated_data.get('parentId', instance.parentId)
        if parentId is not None:
            instance.parentId = Category.objects.get(pk=parentId)
        else:
            instance.parentId = parentId

        instance.save()
        return instance


class NodesSerializer(serializers.Serializer):
    children = serializers.ListField(child=RecursiveField())

    id = serializers.UUIDField(required=True, allow_null=False)
    name = serializers.CharField(max_length=255, required=True, allow_null=False)
    price = serializers.IntegerField(allow_null=True, required=True)
    parentId = serializers.UUIDField(required=True, allow_null=True)
    date = serializers.DateTimeField()


class RecursiveModelSerializer(serializers.ModelSerializer):
    parent = RecursiveField(allow_null=True)

    class Meta:
        model = RecursiveModel
        fields = ('name', 'parent')
