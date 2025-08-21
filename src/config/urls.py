from typing import Any

from django.conf import settings
from django.conf.urls import handler403, handler404, handler500
from django.contrib import admin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import include, path, reverse_lazy
from django.views import defaults as default_views
from django.views import generic
from django.views.i18n import JavaScriptCatalog


class HomeView(LoginRequiredMixin, generic.RedirectView):
    def get_redirect_url(self, *args: Any, **kwargs: Any) -> str | None:
        return reverse_lazy("genrequest-list")


urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path(settings.ADMIN_URL, admin.site.urls),
    path("ht/", include("health_check.urls")),
    path("api/", include("config.routers")),
    path("autocomplete/", include("config.autocomplete", namespace="autocomplete")),
    path("accounts/", include("allauth.urls")),
    path("", include("genlab_bestilling.urls")),
    path("", include("nina.urls", namespace="nina")),
    path("staff/", include("staff.urls", namespace="staff")),
    path(
        "jsi18n/",
        (JavaScriptCatalog.as_view(packages=["formset"])),
        name="javascript-catalog",
    ),
]


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
else:
    # use custom error handlers in production to populate the context
    urlpatterns += [
        handler404("capps.core.views.handler404"),
        handler403("capps.core.views.handler403"),
        handler500("capps.core.views.handler500"),
    ]
