import datetime
import time
import uuid
from itertools import chain
from collections import defaultdict
from typing import Union

from django.db.models import Sum, Avg, Count, QuerySet
from django.views.decorators.http import require_http_methods

from django.http import JsonResponse, HttpResponse
from rest_framework.parsers import JSONParser
from django.views.decorators.csrf import csrf_exempt
from rest_framework.generics import ListCreateAPIView

from rest_framework import status, exceptions

from .serializers import ItemSerializer, PriceHistorySerializer, ItemChildrenSerializer, get_head, save_history
from .models import ItemModel, PriceHistory
from .utility import *

bad_request = lambda: JsonResponse({"code": status.HTTP_400_BAD_REQUEST, "message": "Validation Failed"},
                                   status=status.HTTP_400_BAD_REQUEST)

item_not_found = lambda: JsonResponse({"code": status.HTTP_404_NOT_FOUND, "message": "Item not found"},
                                      status=status.HTTP_404_NOT_FOUND
                                      )


def calculate_category_prices(children: Union[QuerySet, List[ItemModel]]):

    calculated = set()
    for child in children:
        if not child.parentId or child.parentId in calculated:
            continue
        parent = child.parentId
        all_children = ItemModel.objects.filter(parentId=child.parentId).aggregate(
            price=Sum("price_info__items_price_count"),
            count=Sum("price_info__category_items_count"),
        )
        parent.price_info.items_price_count = all_children['price']
        parent.price_info.category_items_count = all_children['count']
        parent.price = parent.price_info.items_price_count // parent.price_info.category_items_count
        parent.price_info.save()
        parent.save()

        calculated.add(parent)

    if calculated:
        calculate_category_prices(list(calculated))




    # calculate_category_prices(list(calculated))

    # for parent in parents:
    #
    #     parent_price = CategoryPrice.objects.get(pk=parent)
    #     print(parent_price)
    #     child_prices = CategoryPrice.objects.filter(id_in=child_categories).aggregate(
    #         count=Sum("category_items_count"),
    #         price=Sum("items_price_count")
    #     )

        # price_table.category_items_count = child_prices['count']
        # price_table.items_price_count = child_prices['price']
        #
        # price_table.save()




class ItemAPIView(ListCreateAPIView):

    def get(self, request, *args, **kwargs):
        try:
            id = uuid.UUID(kwargs['id'])
        except Exception:
            return bad_request()

        try:
            instance = ItemModel.objects.all().get(pk=id)
            serializer = ItemChildrenSerializer(instance=instance)
        except ItemModel.DoesNotExist:
            return item_not_found()

        return JsonResponse(serializer.data, status=200)

    def post(self, request, *args, **kwargs):
        input_data = JSONParser().parse(request)
        type_map = {"CATEGORY": [], 'OFFER': []}

        for item in input_data['items']:
            item['date'] = input_data['updateDate']

            if item['type'] not in type_map.keys():
                return bad_request()

            type_map[item['type']].append(item)

        for item in chain(type_map['CATEGORY'], type_map['OFFER']):
            try:
                import_handler(item)
            except exceptions.ValidationError:
                return bad_request()

        calculate_category_prices(ItemModel.objects.filter(id__in=set([item['id'] for item in type_map['OFFER']])))

        # for item in ItemModel.objects.filter(parentId=None):
        #     item.delete()

        return HttpResponse(status=200)


# @csrf_exempt
# @require_http_methods(["DELETE"])
# def delete_view(request, id):
#     try:
#         id = uuid.UUID(id)
#     except Exception:
#         return bad_request()
#
#     try:
#         instance = ItemModel.objects.get(pk=id)
#
#         head = get_head(instance, date=datetime.datetime.now(tz=datetime.timezone.utc))
#
#         instance.delete()
#
#         changed_categories = set()
#         calc_category_price(head, changed_categories)
#         for item in ItemModel.objects.all().filter(id__in=list(changed_categories)):
#             save_history(item.id, item.price, item.date)
#
#
#     except ItemModel.DoesNotExist:
#         return item_not_found()
#
#     return HttpResponse(status=200)


def sales_view(request):
    date = request.GET.get('date', None)
    if not date:
        return bad_request()

    try:
        date = datetime.datetime.fromisoformat(date[:-1]).astimezone(datetime.timezone.utc)
    except Exception as e:
        print(e)
        return bad_request()

    day_before = date - datetime.timedelta(days=1)

    q = ItemModel.objects.all().filter(date__lt=date, date__gte=day_before)

    s = ItemSerializer(q, many=True)

    return JsonResponse({'items': s.data}, status=200)


def node_statistic_view(request, id):
    try:
        id = uuid.UUID(id)

        dateStart = request.GET.get('dateStart', None)
        dateEnd = request.GET.get('dateEnd', None)

        dateStart = datetime.datetime.fromisoformat(dateStart[:-1]).astimezone(datetime.timezone.utc)
        dateEnd = datetime.datetime.fromisoformat(dateEnd[:-1]).astimezone(datetime.timezone.utc)

        if dateEnd < dateStart:
            raise Exception

    except Exception:
        return bad_request()

    q = PriceHistory.objects.all().filter(price_date_stamp__lt=dateEnd, price_date_stamp__gte=dateStart)
    serializer = PriceHistorySerializer(q, many=True)
    print(*serializer.data, sep='\n')

    return JsonResponse({'items': serializer.data}, status=200)
