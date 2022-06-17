import uuid
import datetime
import random
import string

import enum
from typing import List

RANDOM_NAME = lambda: ''.join(random.choice(string.ascii_lowercase) for i in range(10))
RANDOM_TYPE = lambda: ItemTypes(1 if random.randint(1, 10) > 2 else 2)
RANDOM_PRICE = lambda: random.randint(1, 100000)


class ItemTypes(enum.Enum):
    OFFER = 1
    CATEGORY = 2


class Generator:
    def __init__(self):
        self._items_count = random.randint(1, 1)

        self._category_ids = []

        self._batch = []

    def _get_random_category_id(self):
        return self._category_ids[random.randint(0, len(self._category_ids) - 1)]

    def _get_offer(self, parent_id):
        assert parent_id is not None
        d = {
            "type": "OFFER",
            "name": RANDOM_NAME(),
            "id": str(uuid.uuid4()),
            "parentId": parent_id,
            "price": RANDOM_PRICE()
        }
        return d

    def _get_category(self, parent_id):
        id = uuid.uuid4()
        d = {
            "type": "CATEGORY",
            "name": RANDOM_NAME(),
            "id": str(id),
            "parentId": parent_id
        }
        self._category_ids.append(d['id'])
        return d

    def generate(self):
        for i in range(self._items_count):
            d = {
                'items': [],
                'updateDate': datetime.datetime.now(tz=datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
            }

            if len(self._category_ids) == 0:
                d['items'].append(self._get_category(None))

            self._generate_items(d['items'], random.randint(1, 5))
            self._batch.append(d)

        return self._batch

    def _generate_items(self, storage: List, count: int):

        for i in range(count):
            type = RANDOM_TYPE()
            if type == ItemTypes.OFFER:
                storage.append(self._get_offer(self._get_random_category_id()))
            elif type == ItemTypes.CATEGORY:
                storage.append(self._get_category(self._get_random_category_id()))


if __name__ == '__main__':
    a = Generator().generate()
    print(a)