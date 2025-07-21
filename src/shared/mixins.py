class CleanSaveMixin:
    """
    Mixin to ensure that the save method is called with object validation.
    Intended for classes that inherit from Django Model.
    https://docs.djangoproject.com/en/5.2/ref/models/instances/#validating-objects

    NOTE:
    To validate instances, implement the `clean` method.
    It's a hook designed to be overridden by subclasses to perform custom
    validation logic across multiple fields.

    (For historical reasons, the `clean` method is not called automatically by Django
    when saving an object. Instead, it must be called explicitly in the `save` method.)

    Example:
    ```
    from django.core.exceptions import ValidationError

    def clean(self) -> None:
        if self.is_candy and 'candy' not in self.name:
            raise ValidationError("Name must contain 'candy' if object is marked as candy.")
    ```
    """  # noqa: E501

    def save(self, *args, **kwargs) -> None:
        self.full_clean()  # type: ignore[attr-defined]
        return super().save(*args, **kwargs)  # type: ignore[misc]
