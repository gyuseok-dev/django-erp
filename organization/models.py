from django.db import models
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField

from core.models import AuditedModel


class Company(AuditedModel):
    """Company model."""

    name = models.CharField(_("Company name"), max_length=255)
    registration_number = models.CharField(
        _("Business registration number"), max_length=50, unique=True
    )
    ceo_name = models.CharField(_("CEO name"), max_length=100)
    address = models.TextField(_("Address"))
    phone = models.CharField(_("Phone"), max_length=20, blank=True)
    email = models.EmailField(_("Email"), blank=True)
    website = models.URLField(_("Website"), blank=True)
    established_date = models.DateField(_("Established date"), null=True, blank=True)
    logo = models.ImageField(_("Logo"), upload_to="company/logos/", blank=True)

    class Meta:
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Department(AuditedModel):
    """Department model with hierarchical structure."""

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="departments",
        verbose_name=_("Company"),
    )
    name = models.CharField(_("Department name"), max_length=255)
    code = models.CharField(_("Department code"), max_length=20, unique=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("Parent department"),
    )
    manager = models.ForeignKey(
        "employees.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_departments",
        verbose_name=_("Manager"),
    )
    budget = MoneyField(
        _("Budget"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
        null=True,
        blank=True,
    )
    description = models.TextField(_("Description"), blank=True)
    weight = models.PositiveIntegerField(_("Display order"), default=0)
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        verbose_name = _("Department")
        verbose_name_plural = _("Departments")
        ordering = ["weight", "name"]

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def full_path(self):
        """Return full hierarchical path."""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name

    @property
    def employee_count(self):
        """Return number of employees in this department."""
        return self.employees.filter(status="ACTIVE").count()


class JobGrade(AuditedModel):
    """Job grade/rank model (e.g., 사원, 대리, 과장, 부장)."""

    name = models.CharField(_("Grade name"), max_length=100)
    level = models.PositiveIntegerField(_("Level"), unique=True)
    base_salary_min = MoneyField(
        _("Minimum base salary"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
    )
    base_salary_max = MoneyField(
        _("Maximum base salary"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
    )
    annual_leave_days = models.PositiveIntegerField(
        _("Annual leave days"), default=15
    )
    description = models.TextField(_("Description"), blank=True)

    class Meta:
        verbose_name = _("Job Grade")
        verbose_name_plural = _("Job Grades")
        ordering = ["level"]

    def __str__(self):
        return f"Level {self.level} - {self.name}"


class JobPosition(AuditedModel):
    """Job position/title model (e.g., 팀장, 파트장)."""

    name = models.CharField(_("Position name"), max_length=100)
    allowance = MoneyField(
        _("Position allowance"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
        default=0,
    )
    is_manager = models.BooleanField(_("Has approval authority"), default=False)
    description = models.TextField(_("Description"), blank=True)

    class Meta:
        verbose_name = _("Job Position")
        verbose_name_plural = _("Job Positions")
        ordering = ["-is_manager", "name"]

    def __str__(self):
        return self.name
