import datetime
import json
import uuid

from django.test import TestCase
from ..models import ItemModel, PriceCalculation, PriceHistory
from ..serializers import ItemSerializer, PriceHistorySerializer

date_1 = (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat() + "Z"
date_2 = (datetime.datetime.now() - datetime.timedelta(days=2)).isoformat() + "Z"
date_3 = (datetime.datetime.now() - datetime.timedelta(days=3)).isoformat() + "Z"
date_few_hours_ago = (datetime.datetime.now() - datetime.timedelta(hours=5)).isoformat() + "Z"
date_now = datetime.datetime.now().isoformat() + "Z"

root_id = uuid.uuid4()
child_category_id = uuid.uuid4()
child_id = uuid.uuid4()
subcat_child1 = uuid.uuid4()
subcat_child2 = uuid.uuid4()
subcat_child3 = uuid.uuid4()

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
                'id': child_category_id,
                'name': 'root_child_category',
                'parentId': root_id,
                'type': "CATEGORY",
            },
            {
                'id': child_id,
                'name': 'root_child',
                'parentId': root_id,
                'type': "OFFER",
                'price': 100
            },
            {
                'id': subcat_child1,
                'name': 'subcat_child1',
                'parentId': child_category_id,
                'type': "OFFER",
                'price': 200
            },
            {
                'id': subcat_child2,
                'name': 'subcat_child2',
                'parentId': child_category_id,
                'type': "OFFER",
                'price': 1000
            },
        ],
        "updateDate": date_3
    }
]


class StatisticViewTests(TestCase):
    def setUp(self):
        for b in batch:
            response = self.client.post("http://localhost/imports", data=b, content_type="application/json")
            assert response.status_code == 200

    def test_items_recently_updated(self):
        update_batch = [
            BATCH_CHILD_TEMPLATE(subcat_child1, child_category_id, date_few_hours_ago, 500),
            BATCH_CHILD_TEMPLATE(child_id, root_id, date_few_hours_ago, 500),
            BATCH_CHILD_TEMPLATE(subcat_child2, child_category_id, date_2, 500)
        ]

        for b in update_batch:
            response = self.client.post("http://localhost/imports", data=b, content_type="application/json")
            assert response.status_code == 200

        sales_response = self.client.get("http://localhost/sales", {"date": date_now})
        assert sales_response.status_code == 200
        response_data = json.loads(sales_response.content)

        response_ids = [item['id'] for item in response_data['items']]

        # asserts
        for id in response_ids:
            self.assertIn(uuid.UUID(id), {subcat_child1, child_id})

    def test_get_node_offer_history_from_to_date(self):

        update_batch = [
            BATCH_CHILD_TEMPLATE(child_id, root_id, date_1, 200),
            BATCH_CHILD_TEMPLATE(child_id, root_id, date_few_hours_ago, 300),
            BATCH_CHILD_TEMPLATE(child_id, root_id, date_now, 1000)
        ]

        for b in update_batch:
            response = self.client.post("http://localhost/imports", data=b, content_type="application/json")
            assert response.status_code == 200

        sales_response = self.client.get(f"http://localhost/node/{child_id}/statistic",
                                         {"dateStart": date_1, "dateEnd": date_now})
        assert sales_response.status_code == 200
        response_data = json.loads(sales_response.content)

        self.assertEqual(len(response_data['items']), 2)

        for item in response_data['items']:
            self.assertIn(item['price'], [200, 300])
            self.assertIn(item['date'].replace(".000Z", 'Z'), [date_1, date_few_hours_ago])

    def test_get_node_category_history_from_to_date(self):

        update_batch = [
            BATCH_CHILD_TEMPLATE(child_id, root_id, date_1, 200),
            BATCH_CHILD_TEMPLATE(child_id, root_id, date_few_hours_ago, 300),
            BATCH_CHILD_TEMPLATE(child_id, root_id, date_now, 1000)
        ]

        for b in update_batch:
            response = self.client.post("http://localhost/imports", data=b, content_type="application/json")
            assert response.status_code == 200

        sales_response = self.client.get(f"http://localhost/node/{root_id}/statistic",
                                         {"dateStart": date_1, "dateEnd": date_now})
        assert sales_response.status_code == 200
        response_data = json.loads(sales_response.content)

        self.assertEqual(len(response_data['items']), 2)

        for item in response_data['items']:
            self.assertIn(item['date'].replace(".000Z", 'Z'), [date_1, date_few_hours_ago])

    def test_get_node_offer_history_all_time(self):

        update_batch = [
            BATCH_CHILD_TEMPLATE(child_id, root_id, date_1, 200),
            BATCH_CHILD_TEMPLATE(child_id, root_id, date_few_hours_ago, 300),
            BATCH_CHILD_TEMPLATE(child_id, root_id, date_now, 1000)
        ]

        for b in update_batch:
            response = self.client.post("http://localhost/imports", data=b, content_type="application/json")
            assert response.status_code == 200

        sales_response = self.client.get(f"http://localhost/node/{child_id}/statistic")
        assert sales_response.status_code == 200
        response_data = json.loads(sales_response.content)

        self.assertEqual(len(response_data['items']), 4)

        for item in response_data['items']:
            self.assertIn(item['date'].replace(".000Z", 'Z'), [date_3, date_1, date_few_hours_ago, date_now])

    def test_get_node_node_history_all_time(self):

        update_batch = [
            BATCH_CHILD_TEMPLATE(child_id, root_id, date_1, 200),
            BATCH_CHILD_TEMPLATE(child_id, root_id, date_few_hours_ago, 300),
            BATCH_CHILD_TEMPLATE(child_id, root_id, date_now, 1000)
        ]

        for b in update_batch:
            response = self.client.post("http://localhost/imports", data=b, content_type="application/json")
            assert response.status_code == 200

        sales_response = self.client.get(f"http://localhost/node/{root_id}/statistic")
        assert sales_response.status_code == 200
        response_data = json.loads(sales_response.content)

        self.assertEqual(len(response_data['items']), 4)

        for item in response_data['items']:
            self.assertIn(item['date'].replace(".000Z", 'Z'), [date_3, date_1, date_few_hours_ago, date_now])
