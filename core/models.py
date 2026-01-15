from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class AuditedModel(models.Model):
    """Abstract base model with audit fields."""

    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    modified_at = models.DateTimeField(_("Modified at"), auto_now=True)

    class Meta:
        abstract = True


class UserRole(models.TextChoices):
    """User role choices."""

    ADMIN = "ADMIN", _("Administrator")
    HR_MANAGER = "HR_MANAGER", _("HR Manager")
    TEAM_MANAGER = "TEAM_MANAGER", _("Team Manager")
    EMPLOYEE = "EMPLOYEE", _("Employee")


class User(AbstractUser, AuditedModel):
    """Custom user model."""

    role = models.CharField(
        _("Role"),
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.EMPLOYEE,
    )
    phone = models.CharField(_("Phone"), max_length=20, blank=True)
    department = models.CharField(_("Department"), max_length=100, blank=True)

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ["-date_joined"]

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_hr_manager(self):
        return self.role in [UserRole.ADMIN, UserRole.HR_MANAGER]

    @property
    def is_team_manager(self):
        return self.role in [UserRole.ADMIN, UserRole.HR_MANAGER, UserRole.TEAM_MANAGER]
