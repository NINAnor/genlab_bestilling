from django.contrib import messages
from django.db.models.query import QuerySet
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from capps.users.models import User
from genlab_bestilling.models import Order


class OrderAPIView(APIView):
    class RequestJson:
        user_ids = "user_ids"

    def get_object(self) -> Order:
        return Order.objects.get(pk=self.kwargs["pk"])

    def get_genlab_staff(self) -> QuerySet[User]:
        return User.objects.filter(groups__name="genlab")

    def post(self, request: Request, *args, **kwargs) -> Response:
        order = self.get_object()

        if not order.is_seen:
            msg = "Order must be seen before assigning staff."

            messages.error(request, msg)
            return Response(
                status=400,
                data={"detail": msg},
            )

        try:
            users = self.get_genlab_staff().filter(
                id__in=request.data.get(self.RequestJson.user_ids, [])
            )
            order.responsible_staff.clear()
            order.responsible_staff.set(users)
            order.save()

            return Response(
                status=200,
            )
        except Exception:
            # TODO Report to Sentry
            return Response(
                status=500,
            )
