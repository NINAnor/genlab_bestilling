from django.conf import settings
from django.db import models
from django.db.models import QuerySet
from django.urls import reverse
from django.utils.timezone import now
from django_lifecycle import (
    AFTER_CREATE,
    LifecycleModel,
    hook,
)

from shared.mixins import AdminUrlsMixin


class ValidProject(AdminUrlsMixin, models.Model):
    """A list of valid/known project numbers that can be auto-verified."""

    number = models.CharField(primary_key=True)
    name = models.CharField(null=True, blank=True)

    class Meta:
        verbose_name = "Valid Project"
        verbose_name_plural = "Valid Projects"

    def __str__(self) -> str:
        if self.name:
            return f"{self.number} {self.name}"
        return self.number


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
    def notify_project_created(self) -> None:
        from nina.tasks import send_email_async  # noqa: PLC0415

        # Project was validated against ValidProject in form, auto-verify it
        self.verified_at = now()
        self.save(update_fields=["verified_at"])

        # Send email to admins
        admin_message = (
            f"A new project {self.number} {self.name} was registered and verified.\n\n"
            f"View project: {settings.NOTIFICATIONS['BASE_URL']}"
            + reverse("staff:projects-detail", kwargs={"pk": self.pk})
        )
        send_email_async.enqueue(
            subject=f"{self.number} {self.name} - Project registered and verified",
            message=admin_message,
            from_email=None,
            recipient_list=settings.NOTIFICATIONS["NEW_PROJECT"],
        )

        # Send confirmation to project members
        user_message = (
            f"Your project {self.number} {self.name} has been registered and "
            f"verified. You can now start using it to place orders."
        )
        send_email_async.enqueue(
            subject=f"{self.number} {self.name} - Project registered and verified",
            message=user_message,
            from_email=None,
            recipient_list=list(self.memberships.values_list("email", flat=True)),
        )
