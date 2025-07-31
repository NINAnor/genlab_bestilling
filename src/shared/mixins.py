from django.urls import reverse


class AdminUrlsMixin:
    """
    Mixin to provide admin URLs for models.
    """

    class AdminUrlSuffix:
        ADD = "add"
        CHANGE = "change"
        CHANGELIST = "changelist"
        HISTORY = "history"
        DELETE = "delete"

    @classmethod
    def _get_admin_url_base(cls) -> str:
        return f"admin:{cls._meta.app_label}_{cls._meta.model_name}"  # type: ignore[attr-defined]

    @classmethod
    def get_admin_add_url(cls) -> str:
        return reverse(f"{cls._get_admin_url_base()}_{cls.AdminUrlSuffix.ADD}")

    def get_admin_change_url(self) -> str:
        return reverse(
            f"{self._get_admin_url_base()}_{self.AdminUrlSuffix.CHANGE}",
            kwargs={"object_id": self.pk},  # type: ignore[attr-defined]
        )

    @classmethod
    def get_admin_changelist_url(cls) -> str:
        return reverse(f"{cls._get_admin_url_base()}_{cls.AdminUrlSuffix.CHANGELIST}")

    def get_admin_history_url(self) -> str:
        return reverse(
            f"{self._get_admin_url_base()}_{self.AdminUrlSuffix.HISTORY}",
            kwargs={"object_id": self.pk},  # type: ignore[attr-defined]
        )

    def get_admin_delete_url(self) -> str:
        return reverse(
            f"{self._get_admin_url_base()}_{self.AdminUrlSuffix.DELETE}",
            kwargs={"object_id": self.pk},  # type: ignore[attr-defined]
        )
