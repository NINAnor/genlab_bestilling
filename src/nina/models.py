from django.db import models
from django.urls import reverse


class ProjectMembership(models.Model):
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
    def filter_selectable(self):
        """
        Obtain only active and verified projects
        """
        return self.filter(active=True).exclude(verified_at=None)


class Project(models.Model):
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

    def get_absolute_url(self):
        return reverse("nina:project-detail", kwargs={"pk": self.pk})
