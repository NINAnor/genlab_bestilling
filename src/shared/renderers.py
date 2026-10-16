from typing import Self

from rest_framework.renderers import BrowsableAPIRenderer


class BrowsableAPIRendererWithoutForms(BrowsableAPIRenderer):
    """
    Renders the Browsable API but completely removes the
    HTML input forms at the bottom.
    """

    def get_rendered_html_form(self: Self, *args, **kwargs) -> str:
        return ""
