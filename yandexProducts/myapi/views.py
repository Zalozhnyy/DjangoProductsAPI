import datetime
import uuid
from itertools import chain
from typing import Union

from django.db.models import Sum, Avg, Count, QuerySet, Max

from django.http import JsonResponse, HttpResponse
from rest_framework.parsers import JSONParser
from rest_framework.generics import ListCreateAPIView, DestroyAPIView, ListAPIView

from rest_framework import status, exceptions

from .serializers import PriceHistorySerializer, ItemChildrenSerializer, save_history
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

        return HttpResponse(status=200)


class ItemDeleteAPIView(DestroyAPIView):

    def delete(self, request, *args, **kwargs):
        try:
            id = uuid.UUID(kwargs['id'])
        except Exception:
            return bad_request()

        try:
            instance = ItemModel.objects.get(pk=id)

            if instance.parentId:
                decrement_deleted_item(instance)

            instance.delete()

        except ItemModel.DoesNotExist:
            return item_not_found()

        return HttpResponse(status=200)


class ItemSalesView(ListAPIView):
    allowed_methods = ['GET']

    def get(self, request, *args, **kwargs):
        date = request.query_params.get('date', None)
        if not date:
            return bad_request()

        try:
            date = datetime.datetime.fromisoformat(date[:-1]).astimezone(datetime.timezone.utc)
        except Exception as e:
            return bad_request()

        day_before = date - datetime.timedelta(days=1)

        q = ItemModel.objects.all().filter(type="OFFER", date__lte=date, date__gte=day_before)

        s = ItemSerializer(instance=q, many=True)

        return JsonResponse({'items': s.data}, status=200)


class ItemStatisticView(ListAPIView):
    allowed_methods = ['GET']

    def get(self, request, *args, **kwargs):

        try:
            id = uuid.UUID(kwargs['id'])

            dateStart = request.query_params.get('dateStart', None)
            dateEnd = request.query_params.get('dateEnd', None)

        except Exception:
            return bad_request()

        if dateStart is None and dateEnd is None:
            q = PriceHistory.objects.all().filter(itemId=id)

        elif dateStart and dateEnd:
            dateStart = datetime.datetime.fromisoformat(dateStart[:-1]).astimezone(datetime.timezone.utc)
            dateEnd = datetime.datetime.fromisoformat(dateEnd[:-1]).astimezone(datetime.timezone.utc)

            if dateEnd < dateStart:
                raise Exception

            q = PriceHistory.objects.all().filter(itemId=id, price_date_stamp__lt=dateEnd, price_date_stamp__gte=dateStart)

        else:
            return bad_request()

        serializer = PriceHistorySerializer(q, many=True)

        return JsonResponse({'items': serializer.data}, status=200)
