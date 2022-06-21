import datetime
from typing import List, Set, Union

from django.db import connection, reset_queries
import time
import functools

from django.db.models import QuerySet, Sum, Max

from .models import ItemModel
from .serializers import PriceHistorySerializer, ItemSerializer, save_history


def query_debugger(func):
    @functools.wraps(func)
    def inner_func(*args, **kwargs):
        reset_queries()

        start_queries = len(connection.queries)

        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()

        end_queries = len(connection.queries)

        print(f"Function : {func.__name__} queries: {end_queries - start_queries}  {int((end - start) * 1e3):d} ms")
        return result

    return inner_func


def import_handler(item: dict):
    try:
        instance = ItemModel.objects.get(pk=item['id'])
        serializer = ItemSerializer(data=item, instance=instance)
    except ItemModel.DoesNotExist:
        serializer = ItemSerializer(data=item)

    if serializer.is_valid(raise_exception=True):
        serializer.save()


def calculate_category_prices(children: Union[QuerySet, List[ItemModel]]):
    calculated = set()
    for child in children:
        if not child.parentId or child.parentId in calculated:
            continue

        parent = child.parentId

        all_children = ItemModel.objects.filter(parentId=child.parentId).aggregate(
            price=Sum("price_info__items_price_count"),
            count=Sum("price_info__category_items_count"),
            date=Max("date")
        )
        parent.price_info.items_price_count = all_children['price']
        parent.price_info.category_items_count = all_children['count']
        parent.price = parent.price_info.items_price_count // parent.price_info.category_items_count
        parent.price_info.save()

        parent.date = all_children['date']
        parent.save()

        save_history(parent.id, parent.price, parent.date)

        calculated.add(parent)

    if calculated:
        calculate_category_prices(list(calculated))


def decrement_deleted_item(instance: ItemModel):
    count = instance.price_info.category_items_count
    price = instance.price_info.items_price_count
    date = datetime.datetime.now()

    while instance.parentId:
        instance = instance.parentId

        instance.price_info.category_items_count -= count
        instance.price_info.items_price_count -= price
        instance.price_info.save()

        if instance.price_info.category_items_count > 0:
            new_price = instance.price_info.items_price_count // instance.price_info.category_items_count
        else:
            new_price = None
        instance.price = new_price

        instance.date = date
        instance.save()
        save_history(instance.id, instance.price, instance.date)
