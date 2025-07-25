from typing import Any

from django import template
from django.db.models import Model
from django.db.models import fields as djfields
from taggit.managers import TaggableManager

register = template.Library()


@register.filter
def verbose_name(instance: Model) -> str:
    return str(instance._meta.verbose_name)


def render(field: Any, instance: Model) -> tuple:
    try:
        v = getattr(instance, field.name)

        if isinstance(field, djfields.related.ManyToManyField):
            return field.verbose_name or field.name, ", ".join(
                [str(e) for e in v.all()]
            )

        if isinstance(field, djfields.related.ManyToOneRel):
            return None, None

        return field.verbose_name or field.name, str(v)
    except AttributeError:
        return None, None


IGNORED_FIELDS = [
    "tagged_items",
    "is_seen",
    "is_prioritized",
    "responsible_staff",
]
IGNORED_FIELDS_STAFF = ["tagged_items"]


@register.filter
def get_fields(instance: Model, fields: str | None = None) -> Any:
    return filter(
        lambda x: x[0],
        (
            render(field, instance)
            for field in instance._meta.get_fields()
            if (not fields or field.name in fields.split(" "))
            and not isinstance(field, TaggableManager)
            and field.name not in IGNORED_FIELDS
        ),
    )


@register.filter
def get_fields_staff(instance: Model, fields: str | None = None) -> Any:
    return filter(
        lambda x: x[0],
        (
            render(field, instance)
            for field in instance._meta.get_fields()
            if (not fields or field.name in fields.split(" "))
            and not isinstance(field, TaggableManager)
            and field.name not in IGNORED_FIELDS_STAFF
        ),
    )
