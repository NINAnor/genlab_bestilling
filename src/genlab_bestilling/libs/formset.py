import mimetypes
from pathlib import Path
from typing import Any

from django.contrib.staticfiles.storage import staticfiles_storage
from django.db.models.fields.files import FieldFile
from formset import boundfield as formset_boundfield
from formset.collection import FormCollection
from formset.upload import depict_size, file_icon_url, get_file_info, split_mime_type


class ContextFormCollection(FormCollection):
    def __init__(self, *args, context: dict[str, Any] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = context or {}

        for name, holder in self.declared_holders.items():
            self.update_holder_instances(name, holder)

    def update_holder_instances(self, name: str, holder: Any) -> None:
        pass


def _build_storage_agnostic_file_info(field_file: FieldFile) -> dict[str, Any]:
    """Build the same info dict as ``formset.upload.get_file_info``, without
    relying on filesystem-only APIs such as ``storage.path()``.

    Used as a fallback when the configured storage backend (e.g. S3) doesn't
    implement ``.path()``, which upstream django-formset's ``get_file_info``
    requires to build a preview for an already-saved file.
    """
    file_name = Path(field_file.name)
    content_type, _ = mimetypes.guess_type(file_name.name)
    mime_type, sub_type = split_mime_type(content_type)
    thumbnail_url = file_icon_url(mime_type, sub_type)

    try:
        file_exists = field_file.storage.exists(field_file.name)
    except Exception:
        file_exists = True

    if file_exists:
        download_url = field_file.url
        try:
            file_size = depict_size(field_file.size)
        except Exception:
            file_size = "-"
    else:
        download_url = "javascript:void(0);"
        thumbnail_url = staticfiles_storage.url("formset/icons/file-missing.svg")
        file_size = "-"

    name = ".".join(file_name.name.split(".")[1:])

    return {
        "content_type": content_type,
        "name": name,
        "path": field_file.name,
        "download_url": download_url,
        "thumbnail_url": thumbnail_url,
        "size": file_size,
    }


def storage_safe_get_file_info(field_file: FieldFile) -> dict[str, Any] | None:
    """Drop-in replacement for ``formset.upload.get_file_info`` that falls
    back to a storage-agnostic preview when the storage backend doesn't
    support ``.path()`` (e.g. S3Boto3Storage in production).
    """
    if not field_file:
        return None
    try:
        return get_file_info(field_file)
    except NotImplementedError:
        return _build_storage_agnostic_file_info(field_file)


# Patch the reference used by ``formset.boundfield.BoundField.value()``, which
# is what actually renders the preview for an already-saved FileField value.
# This avoids depending on an upstream django-formset fix/upgrade (as of the
# currently pinned version, this limitation is unresolved upstream).
formset_boundfield.get_file_info = storage_safe_get_file_info
