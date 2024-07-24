from typing import Any

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import include, path, reverse_lazy
from django.views import defaults as default_views
from django.views import generic


class HomeView(LoginRequiredMixin, generic.RedirectView):
    def get_redirect_url(self, *args: Any, **kwargs: Any) -> str | None:
        return reverse_lazy("genrequest-list")


urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path(settings.ADMIN_URL, admin.site.urls),
    path("ht/", include("health_check.urls")),
    path("api/", include("config.routers")),
    path("accounts/", include("allauth.urls")),
    path("", include("genlab_bestilling.urls")),
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
