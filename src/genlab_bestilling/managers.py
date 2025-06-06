from django.db import models
from polymorphic.managers import PolymorphicManager, PolymorphicQuerySet


class GenrequestQuerySet(models.QuerySet):
    def filter_allowed(self, user):
        """
        Get only requests of projects that the user is part of
        """
        return self.filter(project__memberships=user)


class OrderQuerySet(PolymorphicQuerySet):
    def filter_allowed(self, user):
        """
        Get only orders of projects that the user is part of
        """
        return self.filter(genrequest__project__memberships=user)

    def filter_in_draft(self):
        """
        Get only orders in draft
        """
        return self.filter(status=self.model.OrderStatus.DRAFT)


OrderManager = PolymorphicManager.from_queryset(OrderQuerySet)


class EquipmentOrderQuantityQuerySet(models.QuerySet):
    def filter_allowed(self, user):
        """
        Get only orders of projects that the user is part of
        """
        return self.filter(order__genrequest__project__memberships=user)

    def filter_in_draft(self):
        """
        Get only orders in draft
        """
        return self.select_related("order").filter(
            order__status=self.model.OrderStatus.DRAFT
        )


class SampleQuerySet(models.QuerySet):
    def filter_allowed(self, user):
        """
        Get only samples of projects that the user is part of
        """
        return self.filter(order__genrequest__project__memberships=user)

    def filter_in_draft(self):
        """
        Get only samples of orders in draft
        """
        return self.select_related("order").filter(
            order__status=self.model.OrderStatus.DRAFT
        )


class SampleAnalysisMarkerQuerySet(models.QuerySet):
    def filter_allowed(self, user):
        """
        Get only samples of projects that the user is part of
        """
        return self.filter(order__genrequest__project__memberships=user)

    def filter_in_draft(self):
        """
        Get only samples of orders in draft
        """
        return self.select_related("order").filter(
            order__status=self.model.OrderStatus.DRAFT
        )
