from django.conf import settings
from django.core.mail import send_mail
from django.db import models
from django.db.models import QuerySet
from django.urls import reverse
from django_lifecycle import (
    AFTER_CREATE,
    AFTER_UPDATE,
    LifecycleModel,
    hook,
)
from django_lifecycle.conditions import (
    WhenFieldHasChanged,
    WhenFieldValueWas,
)

from shared.mixins import AdminUrlsMixin


class ProjectMembership(AdminUrlsMixin, models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        MANAGER = "manager", "Manager"
        MEMBER = "member", "Member"

    project = models.ForeignKey(
        "Project", on_delete=models.CASCADE, related_name="members"
    )
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(
        choices=Role,
        default=Role.MEMBER,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "user"], name="unique_user_per_project"
            )
        ]

    def __str__(self) -> str:
        return f"{self.project_id} {self.user} - {self.get_role_display()}"


class ProjectManager(models.Manager):
    def filter_selectable(self) -> QuerySet:
        """
        Obtain only active and verified projects
        """
        return self.filter(active=True).exclude(verified_at=None)


class Project(AdminUrlsMixin, LifecycleModel):
    number = models.CharField(primary_key=True)
    name = models.CharField(null=True, blank=True)
    memberships = models.ManyToManyField(
        "users.User", through=ProjectMembership, blank=True
    )
    active = models.BooleanField(default=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    objects = ProjectManager()

    def __str__(self) -> str:
        if self.name:
            return f"{self.number} {self.name}"

        return self.number

    def get_absolute_url(self) -> str:
        return reverse("nina:project-detail", kwargs={"pk": self.pk})

    @hook(AFTER_CREATE, on_commit=True)
    def notify_require_verification(self) -> None:
        send_mail(
            f"{self.number} {self.name} - New project was registered",
            "A new project was registered, please verify it",
            settings.NOTIFICATIONS["SENDER"],
            settings.NOTIFICATIONS["NEW_PROJECT"],
            fail_silently=settings.EMAIL_FAIL_SILENTLY,
        )

    @hook(
        AFTER_UPDATE,
        condition=(
            WhenFieldHasChanged("verified_at", has_changed=True)
            & WhenFieldValueWas("verified_at", value=None)
        ),
    )
    def notify_verified(self) -> None:
        send_mail(
            f"{self.number} {self.name} - New project was registered",
            "A new project was registered, please verify it",
            settings.NOTIFICATIONS["SENDER"],
            self.memberships.values_list("email", flat=True),
            fail_silently=settings.EMAIL_FAIL_SILENTLY,
        )
