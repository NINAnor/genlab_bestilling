from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.views.generic import (
    CreateView,
    FormView,
    UpdateView,
)
from formset.views import (
    FormViewMixin,
    IncompleteSelectResponseMixin,
)

from .forms import ActionForm


class FormsetCreateView(
    IncompleteSelectResponseMixin,
    FormViewMixin,
    LoginRequiredMixin,
    CreateView,
):
    pass


class FormsetUpdateView(
    IncompleteSelectResponseMixin, FormViewMixin, LoginRequiredMixin, UpdateView
):
    pass


class ActionView(FormView):
    form_class = ActionForm

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        Action forms should be used just to modify the system
        """
        return self.http_method_not_allowed(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return self.request.path_info
