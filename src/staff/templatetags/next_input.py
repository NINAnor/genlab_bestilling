from django import template

register = template.Library()


@register.inclusion_tag("staff/components/next_url_input.html", takes_context=True)
def next_url_input(context: template.Context) -> dict:
    request = context["request"]
    return {"next_url": request.get_full_path()}
