from typing import List, Set

from django.db import connection, reset_queries
import time
import functools

from .models import ItemModel
from .serializers import PriceHistorySerializer, ItemSerializer


def query_debugger(func):
    @functools.wraps(func)
    def inner_func(*args, **kwargs):
        reset_queries()

        start_queries = len(connection.queries)

        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()

        end_queries = len(connection.queries)

        print(f"Function : {func.__name__}")
        print(f"Number of Queries : {end_queries - start_queries}")
        print(f"Finished in : {int((end - start) * 1e3):d} ms")
        return result

    return inner_func


# def calc_category_price(head: ItemModel, updated_items: Set) -> (int, int):
#     item_count = 0
#     price_count = 0
#
#     if head is None:
#         return
#
#     for q in ItemModel.objects.filter(parentId=head.id):
#
#         if q.type == "CATEGORY":
#             tmp_price, tmp_count = calc_category_price(q, updated_items)
#
#             price_count += tmp_price
#             item_count += tmp_count
#
#         elif q.type == "OFFER":
#             price_count += q.price
#             item_count += 1
#
#     head.price = price_count // item_count if item_count != 0 else None
#     head.save()
#     updated_items.add(head.id)
#
#     return price_count, item_count
#

def import_handler(item: dict):
    try:
        instance = ItemModel.objects.get(pk=item['id'])
        serializer = ItemSerializer(data=item, instance=instance)
    except ItemModel.DoesNotExist:
        serializer = ItemSerializer(data=item)

    if serializer.is_valid(raise_exception=True):
        serializer.save()
