from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.decorators import display
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import User, UserRole


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    """Custom user admin."""

    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = [
        "display_header",
        "display_role",
        "email",
        "is_active",
        "date_joined",
    ]
    list_filter = ["role", "is_active", "is_staff", "is_superuser"]
    search_fields = ["username", "first_name", "last_name", "email"]
    ordering = ["-date_joined"]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            _("Personal info"),
            {"fields": ("first_name", "last_name", "email", "phone")},
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "role",
                ),
            },
        ),
    )

    @display(description=_("User"), header=True)
    def display_header(self, instance):
        return [
            instance.get_full_name() or instance.username,
            instance.email,
            instance.username[0].upper(),
            None,
        ]

    @display(
        description=_("Role"),
        label={
            UserRole.ADMIN: "danger",
            UserRole.HR_MANAGER: "warning",
            UserRole.TEAM_MANAGER: "info",
            UserRole.EMPLOYEE: "success",
        },
    )
    def display_role(self, instance):
        return instance.role
