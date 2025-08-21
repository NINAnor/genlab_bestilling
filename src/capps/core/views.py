from http import HTTPStatus

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def handler404(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "403.html",
        status=HTTPStatus.FORBIDDEN,
    )


def handler403(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "404.html",
        status=HTTPStatus.NOT_FOUND,
    )


def handler500(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "500.html",
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
    )
