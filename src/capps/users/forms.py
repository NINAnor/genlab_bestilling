from allauth.account.forms import SignupForm
from django.contrib.auth import forms as admin_forms
from django.contrib.auth import get_user_model
from django.forms import EmailField
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class UserAdminChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):  # type: ignore[name-defined]
        model = User
        field_classes = {"email": EmailField}


class UserAdminCreationForm(admin_forms.UserCreationForm):
    """Form for User Creation in the Admin Area.
    To change user signup, see UserSignupForm.
    """

    class Meta(admin_forms.UserCreationForm.Meta):  # type: ignore[name-defined]
        model = User
        fields = ["email"]
        field_classes = {"email": EmailField}
        error_messages = {
            "email": {"unique": _("This email has already been taken.")},
        }


class UserSignupForm(SignupForm):
    """Form that will be rendered on a user sign up section/screen.
    Default fields will be added automatically.
    """
