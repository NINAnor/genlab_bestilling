from typing import Any

from django import template
from django.db.models import Model
from django.db.models import fields as djfields
from django.forms import BoundField
from django.utils.safestring import SafeString, mark_safe
from taggit.managers import TaggableManager

register = template.Library()


@register.filter
def verbose_name(instance: Model) -> str:
    return str(instance._meta.verbose_name)


@register.filter
def dal_forward_conf(field: BoundField) -> SafeString:
    # crispy-tailwind's select rendering bypasses the widget's own `render()`,
    # which is where django-autocomplete-light injects its "forward" config
    # markup, so we have to re-add it manually.
    render_forward_conf = getattr(field.field.widget, "render_forward_conf", None)
    if not callable(render_forward_conf):
        return mark_safe("")
    return mark_safe(render_forward_conf(field.id_for_label))  # noqa: S308


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


@register.filter
def get_item(array: list[Any], index: int) -> Any:
    try:
        return array[index]
    except IndexError:
        return None
