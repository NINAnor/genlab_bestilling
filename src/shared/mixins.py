class CleanSaveMixin:
    """
    Mixin to ensure that the save method is called with object validation.
    https://docs.djangoproject.com/en/5.2/ref/models/instances/#validating-objects

    To validate instances, implement the `clean` method.
    It's a hook designed to be overridden by subclasses to perform custom
    validation logic across multiple fields.

    Example:
    ```
    from django.core.exceptions import ValidationError

    def clean(self) -> None:
        if self.is_candy and 'candy' not in self.name:
            raise ValidationError("Name must contain 'candy' if object is marked as candy.")
        pass
    ```
    """  # noqa: E501

    def save(self, *args, **kwargs) -> None:
        self.full_clean()  # type: ignore[attr-defined]
        return super().save(*args, **kwargs)  # type: ignore[misc]
