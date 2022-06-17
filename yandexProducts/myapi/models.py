import datetime

from django.db import models

import uuid
from enum import Enum


def get_default_price_model():
    return PriceCalculation.objects.create()

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


class PriceCalculation(models.Model):
    category_items_count = models.IntegerField(default=0, null=False)
    items_price_count = models.IntegerField(default=0, null=False)


class ItemModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True, null=False)
    name = models.CharField(max_length=255, null=False)
    date = models.DateTimeField()
    price = models.IntegerField(null=True)
    type = models.CharField(null=False, max_length=20)

    parentId = models.ForeignKey('self',
                                 on_delete=models.CASCADE,
                                 null=True,
                                 related_name='children')

    price_info = models.OneToOneField(PriceCalculation,
                                      on_delete=models.CASCADE,
                                      auto_created=True,
                                      null=False,
                                      default=get_default_price_model)

    def __str__(self):
        return str(self.id)


class PriceHistory(models.Model):
    itemId = models.ForeignKey(ItemModel, on_delete=models.CASCADE, null=False, db_index=True)
    price = models.IntegerField(null=True)
    price_date_stamp = models.DateTimeField(null=False)

    class Meta:
        unique_together = [['itemId', 'price', 'price_date_stamp']]
