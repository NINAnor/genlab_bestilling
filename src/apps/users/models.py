from typing import Self

from django.contrib.auth.models import AbstractUser
from django.db.models import CharField, EmailField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.users.managers import UserManager


class User(AbstractUser):
    """Default custom user model."""

    email = EmailField(_("email address"), unique=True)
    username = None  # type: ignore
    first_name = CharField(max_length=200)
    last_name = CharField(max_length=200)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

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
