from django import template
from django.db.models import fields as djfields
from taggit.managers import TaggableManager

register = template.Library()


@register.filter
def verbose_name(instance):
    return instance._meta.verbose_name


def render(field, instance):
    v = getattr(instance, field.name)

    if isinstance(field, djfields.related.ManyToManyField):
        return field.verbose_name or field.name, ",".join([str(e) for e in v.all()])

    if isinstance(field, djfields.related.ManyToOneRel):
        return None, None

    return field.verbose_name or field.name, str(v)


IGNORED_FIELDS = ["tagged_items"]


@register.filter
def get_fields(instance, fields=None):
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
