from django.db import models
from polymorphic.managers import PolymorphicManager, PolymorphicQuerySet


class GenrequestQuerySet(models.QuerySet):
    def filter_allowed(self, user):
        return self.filter(project__memberships=user)


class OrderQuerySet(PolymorphicQuerySet):
    def filter_allowed(self, user):
        return self.filter(genrequest__project__memberships=user)

    def filter_in_draft(self):
        return self.filter(status=self.model.OrderStatus.DRAFT)


OrderManager = PolymorphicManager.from_queryset(OrderQuerySet)


class EquipmentOrderQuantityQuerySet(models.QuerySet):
    def filter_allowed(self, user):
        return self.filter(order__genrequest__project__memberships=user)

    def filter_in_draft(self):
        return self.select_related("order").filter(
            order__status=self.model.OrderStatus.DRAFT
        )


class SampleQuerySet(models.QuerySet):
    def filter_allowed(self, user):
        return self.filter(order__genrequest__project__memberships=user)

    def filter_in_draft(self):
        return self.select_related("order").filter(
            order__status=self.model.OrderStatus.DRAFT
        )
