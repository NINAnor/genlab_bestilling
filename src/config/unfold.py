from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

AREA_LINK = {
    "title": _("Areas"),
    "icon": "label",
    "link": reverse_lazy("admin:genlab_bestilling_area_changelist"),
}
LOCATION_LINK = {
    "title": _("Locations"),
    "icon": "map",
    "link": reverse_lazy("admin:genlab_bestilling_location_changelist"),
}
LOCATIONTYPE_LINK = {
    "title": _("Location Types"),
    "icon": "map",
    "link": reverse_lazy("admin:genlab_bestilling_locationtype_changelist"),
}
ANALYSISTYPE_LINK = {
    "title": _("Analysis Types"),
    "icon": "biotech",
    "link": reverse_lazy("admin:genlab_bestilling_analysistype_changelist"),
}
SAMPLETYPE_LINK = {
    "title": _("Sample Types"),
    "icon": "science",
    "link": reverse_lazy("admin:genlab_bestilling_sampletype_changelist"),
}
SPECIES_LINK = {
    "title": _("Species"),
    "icon": "nature",
    "link": reverse_lazy("admin:genlab_bestilling_species_changelist"),
}
EQUIPMENTTYPE_LINK = {
    "title": _("Equipment Types"),
    "icon": "hardware",
    "link": reverse_lazy("admin:genlab_bestilling_equipmenttype_changelist"),
}
MARKERS_LINK = {
    "title": _("Markers"),
    "icon": "genetics",
    "link": reverse_lazy("admin:genlab_bestilling_marker_changelist"),
}
ORGS_LINK = {
    "title": _("Organizations"),
    "icon": "groups",
    "link": reverse_lazy("admin:genlab_bestilling_organization_changelist"),
}
# ANALYSIS_ORDER_LINK = {
#     "title": _("Analysis Orders"),
#     "icon": "lab_research",
#     "link": reverse_lazy("admin:genlab_bestilling_analysisorder_changelist"),
# }
# EQUIPMENT_ORDER_LINK = {
#     "title": _("Equipment Orders"),
#     "icon": "orders",
#     "link": reverse_lazy("admin:genlab_bestilling_equipmentorder_changelist"),
# }
GENREQUEST_LINK = {
    "title": _("Requests"),
    "icon": "inbox",
    "link": reverse_lazy("admin:genlab_bestilling_genrequest_changelist"),
}
# SAMPLES_LINK = {
#     "title": _("Samples"),
#     "icon": "labs",
#     "link": reverse_lazy("admin:genlab_bestilling_sample_changelist"),
# }
PROJECTS_LINK = {
    "title": _("Projects"),
    "icon": "folder_shared",
    "link": reverse_lazy("admin:nina_project_changelist"),
    "permission": lambda request: request.user.has_perm("nina.view_project"),
}
PROJECT_MEMBERSHIP_LINK = {
    "title": _("Members"),
    "link": reverse_lazy("admin:nina_projectmembership_changelist"),
    "permission": lambda request: request.user.has_perm("nina.view_projectmembership"),
}
USERS_LINK = {
    "title": _("Users"),
    "icon": "person",
    "link": reverse_lazy("admin:users_user_changelist"),
    "permission": lambda request: request.user.has_perm("users.view_user"),
}

UNFOLD = {
    "SITE_TITLE": "GenLab",
    "SITE_HEADER": "GenLab",
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/svg+xml",
            "href": lambda request: static("images/favicons/favicon.ico"),
        },
    ],
    "SITE_LOGO": lambda request: static("images/logo.png"),
    "THEME": "light",
    "COLORS": {
        "primary": {
            "50": "#004C6C",
            "100": "#004C6C",
            "200": "#004C6C",
            "300": "#004C6C",
            "400": "#004C6C",
            "500": "#004C6C",
            "600": "#004C6C",
            "700": "#004C6C",
            "800": "#004C6C",
            "900": "#004C6C",
            "950": "#004C6C",
        },
    },
    "SIDEBAR": {
        "show_search": True,  # Search in applications and models names
        "show_all_applications": False,
        "navigation": [
            {
                "title": _("Navigation"),
                "items": [
                    {
                        "title": _("Dashboard"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                    GENREQUEST_LINK,
                    # EQUIPMENT_ORDER_LINK,
                    # ANALYSIS_ORDER_LINK,
                    PROJECTS_LINK,
                    USERS_LINK,
                ],
            },
            {
                "title": "Enumerables",
                "collapsible": True,
                "items": [
                    AREA_LINK,
                    LOCATION_LINK,
                    LOCATIONTYPE_LINK,
                    ANALYSISTYPE_LINK,
                    SAMPLETYPE_LINK,
                    SPECIES_LINK,
                    EQUIPMENTTYPE_LINK,
                    MARKERS_LINK,
                    ORGS_LINK,
                ],
            },
        ],
    },
    "TABS": [
        {
            "models": ["genlab_bestilling.analysisorder", "genlab_bestilling.sample"],
            "items": [
                # SAMPLES_LINK,
                # ANALYSIS_ORDER_LINK,
            ],
        },
        {
            "models": ["nina.project", "nina.projectmembership"],
            "items": [PROJECT_MEMBERSHIP_LINK, PROJECTS_LINK],
        },
    ],
}
