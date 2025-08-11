from django.core import mail
from django.test import TransactionTestCase
from django.utils import timezone

from capps.users.models import User
from nina.models import Project, ProjectMembership


class ProjectEmailTestCase(TransactionTestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpass123",  # noqa: S106  # pragma: allowlist secret
        )

    def test_email_sent_on_project_creation(self) -> None:
        """Test that email is sent to admin when a new project is created."""
        # Clear any existing emails
        mail.outbox = []

        # Create a new project
        Project.objects.create(number="TEST001", name="Test Project")

        # Check that one email was sent
        self.assertEqual(len(mail.outbox), 1)

        # Check email details
        email = mail.outbox[0]
        self.assertEqual(
            email.subject, "TEST001 Test Project - New project was registered"
        )
        self.assertEqual(email.body, "A new project was registered, please verify it")
        self.assertEqual(email.from_email, "noreply@genlab.com")
        self.assertEqual(email.to, ["admin@genlab.com", "staff@genlab.com"])

    def test_email_sent_on_project_verification(self) -> None:
        """Test that email is sent to project members when project is verified."""
        # Clear any existing emails
        mail.outbox = []

        # Create a project (this will send the first email)
        project = Project.objects.create(number="TEST002", name="Test Project 2")

        # Add a member to the project
        ProjectMembership.objects.create(
            project=project, user=self.user, role=ProjectMembership.Role.MEMBER
        )

        # Clear the creation email
        mail.outbox = []

        # Verify the project (this should trigger the verification email)
        project.verified_at = timezone.now()
        project.save()

        # Check that one email was sent
        self.assertEqual(len(mail.outbox), 1)

        # Check email details
        email = mail.outbox[0]
        self.assertEqual(
            email.subject, "TEST002 Test Project 2 - New project was registered"
        )
        self.assertEqual(email.body, "A new project was registered, please verify it")
        self.assertEqual(email.from_email, "noreply@genlab.com")
        self.assertEqual(email.to, ["testuser@example.com"])

    def test_no_email_sent_on_project_update_without_verification(self) -> None:
        """Test that no email is sent when project is updated but not verified."""
        # Create a project
        project = Project.objects.create(number="TEST003", name="Test Project 3")

        # Clear the creation email
        mail.outbox = []

        # Update project name (should not trigger verification email)
        project.name = "Updated Test Project 3"
        project.save()

        # Check that no additional email was sent
        self.assertEqual(len(mail.outbox), 0)

    def test_no_duplicate_email_on_multiple_verification_updates(self) -> None:
        """Test that no duplicate email is sent when verified project is updated."""
        # Create and verify a project
        project = Project.objects.create(number="TEST004", name="Test Project 4")

        # Add a member
        ProjectMembership.objects.create(
            project=project, user=self.user, role=ProjectMembership.Role.OWNER
        )

        # Clear the creation email
        mail.outbox = []

        # Verify the project
        project.verified_at = timezone.now()
        project.save()

        # Check that verification email was sent
        self.assertEqual(len(mail.outbox), 1)

        # Clear emails again
        mail.outbox = []

        # Update the project again (should not trigger another verification email)
        project.name = "Updated Test Project 4"
        project.save()

        # Check that no additional email was sent
        self.assertEqual(len(mail.outbox), 0)

    def test_verification_email_sent_to_multiple_members(self) -> None:
        """Test that verification email is sent to all project members."""
        # Create additional users
        user2 = User.objects.create_user(
            email="testuser2@example.com",
            password="testpass123",  # noqa: S106  # pragma: allowlist secret
        )
        user3 = User.objects.create_user(
            email="testuser3@example.com",
            password="testpass123",  # noqa: S106  # pragma: allowlist secret
        )

        # Create a project
        project = Project.objects.create(number="TEST005", name="Test Project 5")

        # Add multiple members
        ProjectMembership.objects.create(
            project=project, user=self.user, role=ProjectMembership.Role.OWNER
        )
        ProjectMembership.objects.create(
            project=project, user=user2, role=ProjectMembership.Role.MANAGER
        )
        ProjectMembership.objects.create(
            project=project, user=user3, role=ProjectMembership.Role.MEMBER
        )

        # Clear the creation email
        mail.outbox = []

        # Verify the project
        project.verified_at = timezone.now()
        project.save()

        # Check that verification email was sent
        self.assertEqual(len(mail.outbox), 1)

        # Check that all members received the email
        email = mail.outbox[0]
        expected_recipients = [
            "testuser@example.com",
            "testuser2@example.com",
            "testuser3@example.com",
        ]
        self.assertEqual(sorted(email.to), sorted(expected_recipients))
