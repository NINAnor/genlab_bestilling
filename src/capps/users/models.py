from typing import Self

from django.contrib.auth.models import AbstractUser
from django.db.models import EmailField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from capps.users.managers import UserManager
from shared.mixins import CleanSaveMixin


class User(CleanSaveMixin, AbstractUser):
    """Default custom user model."""

    email = EmailField(_("email address"), unique=True)
    username = None  # type: ignore

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()  # type: ignore[assignment,misc] # Override the default manager.

    def __str__(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email

    def get_absolute_url(self: Self) -> str:
        """Get URL for user's detail view.

        Returns
        -------
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"pk": self.id})

    def is_genlab_staff(self) -> bool:
        return self.groups.filter(name="genlab").exists()
