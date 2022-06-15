from rest_framework import serializers

from .models import ItemModel, PriceHistory


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

        try:
            category_instance = ItemModel.objects.get(pk=value)
        except ItemModel.DoesNotExist:
            category_instance = None

        return category_instance

    def create(self, validated_data):

        instance = ItemModel.objects.create(**validated_data)
        if instance.type == 'OFFER':
            self._save_history(instance.id, instance.price, instance.date)
        return instance

    def update(self, instance, validated_data):

        if validated_data['date'] < instance.date:
            print("Update date lower that object date")
            # raise Exception("Update date lower that object date")
        if validated_data['type'] != instance.type:
            print("Can't change item type")
            return

        instance.name = validated_data.get('name', instance.name)
        instance.type = validated_data.get('type', instance.type)
        instance.parentId = validated_data.get('parentId', instance.parentId)
        instance.price = validated_data.get('price', instance.price)
        instance.date = validated_data.get('date', instance.date)

        instance.save()

        if instance.type == 'OFFER':
            self._save_history(instance.id, instance.price, instance.date)

        return instance

    def _save_history(self, id, price, date):
        s = PriceHistorySerializer(
            data={"itemId": id, "price": price, "price_date_stamp": date})
        if s.is_valid():
            s.save()


class PriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceHistory
        fields = ['itemId', 'price', 'price_date_stamp']

        serializers.UniqueTogetherValidator(
            queryset=model.objects.all(),
            fields=('itemId', 'price', 'price_date_stamp'),
        )
