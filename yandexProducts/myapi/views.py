import uuid

from django.views.decorators.http import require_http_methods

from rest_framework.response import Response
from django.http import JsonResponse, HttpResponse
from rest_framework.parsers import JSONParser
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status

from .serializers import ItemSerializer
from .models import ItemModel
from .utility import query_debugger


@csrf_exempt
@require_http_methods(["POST"])
def import_view(request):
    input_data = JSONParser().parse(request)

    items = input_data['items']
    items = sorted(items, key=lambda x: x['type'])

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

            if serializer.validated_data['parentId'] is not None:
                q = serializer.validated_data['parentId']

                while q is not None:
                    if q.date < serializer.validated_data['date']:
                        q.date = serializer.validated_data['date']
                        q.save()
                    else:
                        break
                    q = q.parentId

            serializer.save()



        else:
            return JsonResponse(
                {
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "Validation Failed"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    return HttpResponse(status=200)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_view(request, id):
    try:
        id = uuid.UUID(id)
    except Exception:
        return JsonResponse(
            {
                "code": status.HTTP_400_BAD_REQUEST,
                "message": "Validation Failed"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        instance = ItemModel.objects.get(pk=id)
    except ItemModel.DoesNotExist:
        return JsonResponse(
            {
                "code": status.HTTP_404_NOT_FOUND,
                "message": "Item not found"
            },
            status=status.HTTP_404_NOT_FOUND
        )

    instance.delete()
    return HttpResponse(status=200)


@query_debugger
@csrf_exempt
@require_http_methods(["GET"])
def nodes_view(request, id):
    try:
        id = uuid.UUID(id)
    except Exception:
        return JsonResponse(
            {
                "code": status.HTTP_400_BAD_REQUEST,
                "message": "Validation Failed"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    output = dict()

    try:
        head = ItemModel.objects.all().get(pk=id)
        serializer = ItemSerializer(head)
        output['children'] = []

    except ItemModel.DoesNotExist:
        return JsonResponse(
            {
                "code": status.HTTP_404_NOT_FOUND,
                "message": "Item not found"
            },
            status=status.HTTP_404_NOT_FOUND
        )

    output.update(serializer.data)
    price, count = recurse(output)
    output['price'] = price // count if count != 0 else None
    output['date'] = output['date'].replace('Z', ".000Z")
    head.price = price // count if count != 0 else None
    head.save()

    return JsonResponse(output, status=200)


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
            item.price = price
            tmp['price'] = price

            item.save()



        else:
            return

        output['children'].append(tmp)

    return price_count, item_count
