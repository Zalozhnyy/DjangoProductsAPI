import datetime
import uuid

from django.views.decorators.http import require_http_methods

from django.http import JsonResponse, HttpResponse
from rest_framework.parsers import JSONParser
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status, exceptions

from .serializers import ItemSerializer, PriceHistorySerializer
from .models import ItemModel, PriceHistory
from .utility import get_head_of_three, calc_category_price, save_history, query_debugger

bad_request = lambda: JsonResponse({"code": status.HTTP_400_BAD_REQUEST, "message": "Validation Failed"},
                                   status=status.HTTP_400_BAD_REQUEST)

item_not_found = lambda: JsonResponse({"code": status.HTTP_404_NOT_FOUND, "message": "Item not found"},
                                      status=status.HTTP_404_NOT_FOUND
                                      )


@csrf_exempt
@require_http_methods(["POST"])
def import_view(request):
    input_data = JSONParser().parse(request)

    items = input_data['items']
    items = sorted(items, key=lambda x: x['type'])
    changed_categories = set()

    for item in items:
        item['date'] = input_data['updateDate']

        if item['type'] == "CATEGORY":
            item['price'] = None

        try:
            instance = ItemModel.objects.get(pk=item['id'])
            serializer = ItemSerializer(data=item, instance=instance)
        except ItemModel.DoesNotExist:
            serializer = ItemSerializer(data=item)

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            head = get_head_of_three(ItemModel.objects.all().get(pk=serializer.validated_data['id']),
                                     serializer.validated_data['date'])
            calc_category_price(head, changed_categories)

        else:
            return bad_request()

    for item in ItemModel.objects.all().filter(id__in=list(changed_categories)):
        save_history(item.id, item.price, item.date)

    return HttpResponse(status=200)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_view(request, id):
    try:
        id = uuid.UUID(id)
    except Exception:
        return bad_request()

    try:
        instance = ItemModel.objects.get(pk=id)

        head = get_head_of_three(instance, date=datetime.datetime.now(tz=datetime.timezone.utc))

        instance.delete()

        changed_categories = set()
        calc_category_price(head, changed_categories)
        for item in ItemModel.objects.all().filter(id__in=list(changed_categories)):
            save_history(item.id, item.price, item.date)


    except ItemModel.DoesNotExist:
        return item_not_found()

    return HttpResponse(status=200)


@csrf_exempt
@require_http_methods(["GET"])
def nodes_view(request, id):
    try:
        id = uuid.UUID(id)
    except Exception:
        return bad_request()

    output = dict()

    try:
        head = ItemModel.objects.all().get(pk=id)
        serializer = ItemSerializer(head)
        output['children'] = []

    except ItemModel.DoesNotExist:
        return item_not_found()

    output.update(serializer.data)
    price, count = recurse(output)
    output['price'] = price // count if count != 0 else None
    output['date'] = output['date'].replace('Z', ".000Z")
    head.price = price // count if count != 0 else None

    return JsonResponse(output, status=200)


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


def recurse(output):
    id = output['id']

    item_count = 0
    price_count = 0

    for item in ItemModel.objects.all().filter(parentId=id):

        serializer = ItemSerializer(item)
        tmp = dict()
        tmp.update(serializer.data)
        tmp['date'] = tmp['date'].replace('Z', ".000Z")

        if item.type == "OFFER":
            tmp.update({"children": None})

            price_count += serializer.data['price']
            item_count += 1

        elif item.type == "CATEGORY":
            tmp.update({"children": []})
            tmp_price, tmp_count = recurse(tmp)

            price_count += tmp_price
            item_count += tmp_count

            price = tmp_price // tmp_count if item_count != 0 else None
            tmp['price'] = price

        else:
            return

        output['children'].append(tmp)

    return price_count, item_count
