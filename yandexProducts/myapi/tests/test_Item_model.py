from django.test import TestCase
from ..models import ItemModel, PriceCalculation, PriceHistory
from ..serializers import ItemSerializer

import uuid
import datetime

date = datetime.datetime.now().isoformat() + "Z"

data = {
    "root": {
        'id': "3eabb388-b675-48f6-ad06-9e5d11a9044e",
        'name': 'root',
        'date': date,
        'parentId': None,
        'type': "CATEGORY",
        'price': None
    },

    'root_child': {
        'id': "345fdc5f-efe5-4c66-8083-7943de05a3d9",
        'name': 'root_child',
        'date': date,
        'parentId': "3eabb388-b675-48f6-ad06-9e5d11a9044e",
        'type': "OFFER",
        'price': 100
    },

    'root_child_update': {
        'id': "345fdc5f-efe5-4c66-8083-7943de05a3d9",
        'name': 'root_child',
        'date': date,
        'parentId': "3eabb388-b675-48f6-ad06-9e5d11a9044e",
        'type': "OFFER",
        'price': 200
    },

}


class ItemModelCreateUpdateTests(TestCase):
    def setUp(self):
        root = ItemModel.objects.create(**data['root'])
        data['root_child']['parentId'] = root
        data['root_child_update']['parentId'] = root
        child = ItemModel.objects.create(**data['root_child'])

    def test_create(self):
        obj = ItemModel.objects.get(pk='3eabb388-b675-48f6-ad06-9e5d11a9044e')
        price = PriceCalculation.objects.get(id=obj.price_info.id)

        serializer = ItemSerializer(obj)

        self.assertEqual(data['root'], serializer.data)


    def test_update(self):
        child = ItemModel.objects.get(pk="345fdc5f-efe5-4c66-8083-7943de05a3d9")
        child.price = data['root_child_update']['price']
        child.save()

        test = ItemModel.objects.get(pk="345fdc5f-efe5-4c66-8083-7943de05a3d9")

        self.assertEqual(test.price, data['root_child_update']['price'])
