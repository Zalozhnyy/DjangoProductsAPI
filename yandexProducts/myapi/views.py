import uuid

from django.views.decorators.http import require_http_methods

from django.shortcuts import render
from rest_framework.response import Response
from django.http import JsonResponse, HttpResponse
from rest_framework.parsers import JSONParser
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status

from .serializers import CategorySerializer, ProductSerializer, NodesSerializer, RecursiveModelSerializer
from .models import ItemTypes, Category, ProductItem, RecursiveModel
from .utility import query_debugger


def import_handler(_model, serializer):
    if serializer.is_valid():
        instance = _model.objects.filter(pk=serializer.validated_data['id'])

        if instance:  # object exist in database
            serializer.update(instance[0], serializer.validated_data)
        else:
            serializer.save()
    else:
        return JsonResponse(
            {
                "code": status.HTTP_400_BAD_REQUEST,
                "message": "Validation Failed"
            },
            status=status.HTTP_400_BAD_REQUEST
        )


@csrf_exempt
@require_http_methods(["POST"])
def import_view(request):
    input_data = JSONParser().parse(request)

    items = input_data['items']
    categories, products = [], []

    for item in items:
        item['date'] = input_data['updateDate']

        if ItemTypes.from_str(item['type']) == ItemTypes.CATEGORY:
            categories.append((Category, CategorySerializer(data=item)))

        elif ItemTypes.from_str(item['type']) == ItemTypes.OFFER:
            products.append((ProductItem, ProductSerializer(data=item)))

        else:
            raise NotImplementedError("unknnow item type")

    for _model, serializer in categories:
        import_handler(_model, serializer)

    for _model, serializer in products:
        import_handler(_model, serializer)

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

    instance = Category.objects.filter(id=id)
    if instance:
        instance[0].delete()
        return HttpResponse(status=200)

    instance = ProductItem.objects.filter(id=id)
    if instance:
        instance[0].delete()
        return HttpResponse(status=200)

    return JsonResponse(
        {
            "code": status.HTTP_404_NOT_FOUND,
            "message": "Item not found"
        },
        status=status.HTTP_404_NOT_FOUND
    )


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
        head = Category.objects.all().get(pk=id)
        serializer = CategorySerializer(head)
        output['type'] = "CATEGORY"
        output['children'] = []

    except Category.DoesNotExist:
        try:
            head = ProductItem.objects.all().get(pk=id)
            serializer = ProductSerializer(head)
            output['type'] = "OFFER"

        except ProductItem.DoesNotExist:
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


    return JsonResponse(output, status=200)


def recurse(output):
    id = output['id']
    item_count = 0
    price_count = 0

    for item in ProductItem.objects.all().filter(parentId=id):
        tmp = {
            "type": "OFFER",
            "children": None
        }

        serializer = ProductSerializer(item)
        tmp.update(serializer.data)
        output['children'].append(tmp)

        price_count += serializer.data['price']
        item_count += 1

    for item in Category.objects.all().filter(parentId=id):
        tmp = {
            "type": "CATEGORY",
            "children": []
        }
        serializer = CategorySerializer(item)
        tmp.update(serializer.data)
        output['children'].append(tmp)
        tmp_price, tmp_count = recurse(tmp)

        price = tmp_price // tmp_count if item_count != 0 else None
        item.price = price
        tmp['price'] = price

        item.save()

        price_count += tmp_price
        item_count += tmp_count

    return price_count, item_count

