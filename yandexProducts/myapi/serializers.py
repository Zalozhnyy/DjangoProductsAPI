from rest_framework import serializers, relations

from .models import ItemModel, PriceHistory


def get_head(validated_data: dict, update_data: bool):
    head: ItemModel = ItemModel.objects.get(pk=validated_data['id'])

    while head.parentId is not None:
        head = head.parentId
        if update_data and head.date != validated_data['date']:
            head.date = validated_data['date']
            head.save()

    return head


def save_history(id, price, date):
    s = PriceHistorySerializer(
        data={"itemId": id, "price": price, "price_date_stamp": date})
    if s.is_valid():
        s.save()


def push_date_to_parent(instance: ItemModel):
    parent = instance.parentId
    if parent and parent.date < instance.date:
        parent.date = instance.date
        parent.save()


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemModel
        fields = ['id', 'name', 'parentId', "date", "price", 'type']

    def create(self, validated_data):

        instance = ItemModel.objects.create(**validated_data)
        if instance.type == 'OFFER':
            price = instance.price_info
            price.category_items_count = 1
            price.items_price_count = instance.price
            price.save()

            save_history(instance.id, instance.price, instance.date)

        # push_date_to_parent(instance)

        return instance

    def update(self, instance, validated_data):

        if validated_data['date'] < instance.date:
            print("Update date lower that object date")
            # raise Exception("Update date lower that object date")
        if validated_data['type'] != instance.type:
            print("Can't change item type")
            return

        if instance.type == 'OFFER':
            price = instance.price_info
            price.items_price_count += (validated_data['price'] - instance.price)
            price.save()

        instance = super().update(instance, validated_data)

        if instance.type == 'OFFER':
            save_history(instance.id, instance.price, instance.date)

        return instance


class PriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceHistory
        fields = ['itemId', 'price', 'price_date_stamp']

        serializers.UniqueTogetherValidator(
            queryset=model.objects.all(),
            fields=('itemId', 'price', 'price_date_stamp'),
        )


class ChildrenSerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        data = ItemChildrenSerializer(ItemModel.objects.get(pk=instance.id)).data
        if len(data["children"]) == 0 or data['type'] == "OFFER":
            data['children'] = None
        return data

    class Meta:
        model = ItemModel
        fields = ['id', 'name', "parentId", 'type', 'price', 'date']


class ItemChildrenSerializer(serializers.ModelSerializer):
    children = ChildrenSerializer(many=True, read_only=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['date'] = data['date'].replace('Z', '.000Z')
        return data

    class Meta:
        model = ItemModel
        fields = ['id', 'name', "parentId", 'type', 'price', 'date', "children"]
