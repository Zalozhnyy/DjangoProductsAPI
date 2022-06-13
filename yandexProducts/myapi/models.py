from django.db import models

import uuid
from enum import Enum


class ItemTypes(Enum):
    OFFER = 1
    CATEGORY = 2

    @staticmethod
    def from_str(label):
        if label in {"CATEGORY", 'category'}:
            return ItemTypes.CATEGORY
        elif label in ("OFFER", 'offer'):
            return ItemTypes.OFFER
        else:
            raise NotImplementedError


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    name = models.CharField(max_length=255, null=False)
    date = models.DateTimeField()
    price = models.IntegerField(null=True)

    parentId = models.ForeignKey('self', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return str(self.id)


class ProductItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    name = models.CharField(max_length=255, null=False)
    price = models.IntegerField(null=True)
    date = models.DateTimeField()

    parentId = models.ForeignKey(Category, on_delete=models.CASCADE, null=False)


class RecursiveModel(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', null=True, on_delete=models.CASCADE)
