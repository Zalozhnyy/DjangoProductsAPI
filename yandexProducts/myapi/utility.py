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
