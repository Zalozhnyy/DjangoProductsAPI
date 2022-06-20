from django.test import TestCase
from ..models import ItemModel, PriceCalculation, PriceHistory
from ..serializers import ItemSerializer, PriceHistorySerializer
from django.urls import reverse

import uuid
import datetime
import json

date_1 = (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat() + "Z"
date_2 = (datetime.datetime.now() - datetime.timedelta(days=2)).isoformat() + "Z"
date_3 = (datetime.datetime.now() - datetime.timedelta(days=3)).isoformat() + "Z"
date = datetime.datetime.now().isoformat() + "Z"

root_id = "3eabb388-b675-48f6-ad06-9e5d11a9044e"
child_id = "345fdc5f-efe5-4c66-8083-7943de05a3d9"

BATCH_CHILD_TEMPLATE = lambda _id, _parent_id, _date, _price: {
    "items": [
        {
            'id': _id,
            'name': 'child',
            'parentId': _parent_id,
            'type': "OFFER",
            'price': _price
        }
    ],
    "updateDate": _date
}

batch = [
    {
        "items": [
            {
                'id': root_id,
                'name': 'root',
                'parentId': None,
                'type': "CATEGORY",
            },
            {
                'id': child_id,
                'name': 'root_child',
                'parentId': root_id,
                'type': "OFFER",
                'price': 200
            }
        ],
        "updateDate": date_3
    }
]


class ImportViewLogicTests(TestCase):
    def setUp(self):
        for b in batch:
            response = self.client.post("http://localhost/imports", data=b, content_type="application/json")
            assert response.status_code == 200

    def test_created_root(self):
        # objects created test
        self.assertEqual(len(ItemModel.objects.all()), 2)
        self.assertEqual(len(PriceCalculation.objects.all()), 2)

        # price recalculated test
        root = ItemModel.objects.get(pk=root_id)
        self.assertEqual(root.price, 200)

        # price history table
        self.assertEqual(len(PriceHistory.objects.all()), 2)
        root = PriceHistory.objects.get(itemId=root_id, price_date_stamp=date_3)
        self.assertEqual(root.price, 200)

    def test_update_child(self):
        # setup
        data = BATCH_CHILD_TEMPLATE("345fdc5f-efe5-4c66-8083-7943de05a3d9", root_id, date_2, 250)
        response = self.client.post("http://localhost/imports",
                                    data=data,
                                    content_type="application/json")
        assert response.status_code == 200

        # asserts

        # price recalculated test
        root = ItemModel.objects.get(pk=root_id)
        self.assertEqual(root.price, 250)

        # price history table
        self.assertEqual(len(PriceHistory.objects.all()), 4)
        root = PriceHistory.objects.get(itemId=root_id, price_date_stamp=date_2)
        self.assertEqual(root.price, 250)

    def test_add_child(self):
        # setup
        data = BATCH_CHILD_TEMPLATE(str(uuid.uuid4()), root_id, date_2, 500)
        response = self.client.post("http://localhost/imports",
                                    data=data,
                                    content_type="application/json")
        assert response.status_code == 200

        # asserts
        root = ItemSerializer(ItemModel.objects.get(pk=root_id))
        self.assertEqual(root.data['price'], 350)
        self.assertEqual(root.data['date'], date_2)

        # price history table
        self.assertEqual(len(PriceHistory.objects.all()), 4)
        root_old = PriceHistory.objects.get(itemId=root_id, price_date_stamp=date_3)
        root_new = PriceHistory.objects.get(itemId=root_id, price_date_stamp=date_2)
        self.assertEqual(root_old.price, 200)
        self.assertEqual(root_new.price, 350)

    def test_delete_child(self):
        delete_child = self.client.delete(f"http://localhost/delete/{child_id}")
        assert delete_child.status_code == 200

        self.assertNotIn(child_id, [e.itemId.id for e in PriceHistory.objects.all()])

        root = ItemModel.objects.get(pk=root_id)
        self.assertIs(root.price, None)

    def test_delete_root(self):
        delete_child = self.client.delete(f"http://localhost/delete/{root_id}")
        self.assertEqual(delete_child.status_code, 200)

        get_deleted_node = self.client.get(f"http://localhost/nodes/{root_id}")
        self.assertJSONEqual(
            str(get_deleted_node.content, encoding='utf8'),
            {"code": 404, "message": "Item not found"}
        )

        self.assertEqual(len(PriceHistory.objects.all()), 0)
