from datetime import date

from django.db import models
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from simple_history.models import HistoricalRecords

from core.models import AuditedModel, User


class EmployeeStatus(models.TextChoices):
    """Employee status choices."""

    ACTIVE = "ACTIVE", _("Active")
    ON_LEAVE = "ON_LEAVE", _("On Leave")
    RESIGNED = "RESIGNED", _("Resigned")


class ContractType(models.TextChoices):
    """Contract type choices."""

    PERMANENT = "PERMANENT", _("Permanent")
    CONTRACT = "CONTRACT", _("Contract")
    INTERN = "INTERN", _("Intern")
    PART_TIME = "PART_TIME", _("Part-time")


class Gender(models.TextChoices):
    """Gender choices."""

    MALE = "MALE", _("Male")
    FEMALE = "FEMALE", _("Female")


class Employee(AuditedModel):
    """Employee model."""

    # Basic Information
    employee_number = models.CharField(
        _("Employee number"), max_length=20, unique=True
    )
    first_name = models.CharField(_("First name"), max_length=100)
    last_name = models.CharField(_("Last name"), max_length=100)
    email = models.EmailField(_("Email"), unique=True)
    phone = models.CharField(_("Phone"), max_length=20)
    birth_date = models.DateField(_("Birth date"))
    gender = models.CharField(_("Gender"), max_length=10, choices=Gender.choices)
    profile_image = models.ImageField(
        _("Profile image"), upload_to="employees/photos/", blank=True
    )

    # HR Information
    department = models.ForeignKey(
        "organization.Department",
        on_delete=models.PROTECT,
        related_name="employees",
        verbose_name=_("Department"),
    )
    job_grade = models.ForeignKey(
        "organization.JobGrade",
        on_delete=models.PROTECT,
        related_name="employees",
        verbose_name=_("Job grade"),
    )
    job_position = models.ForeignKey(
        "organization.JobPosition",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
        verbose_name=_("Job position"),
    )
    manager = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subordinates",
        verbose_name=_("Manager"),
    )

    # Contract Information
    hire_date = models.DateField(_("Hire date"))
    contract_type = models.CharField(
        _("Contract type"),
        max_length=20,
        choices=ContractType.choices,
        default=ContractType.PERMANENT,
    )
    contract_end_date = models.DateField(
        _("Contract end date"), null=True, blank=True
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=EmployeeStatus.choices,
        default=EmployeeStatus.ACTIVE,
    )
    resignation_date = models.DateField(_("Resignation date"), null=True, blank=True)
    resignation_reason = models.TextField(_("Resignation reason"), blank=True)

    # Salary Information
    base_salary = MoneyField(
        _("Base salary"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
    )
    bank_name = models.CharField(_("Bank name"), max_length=50)
    bank_account = models.CharField(_("Bank account"), max_length=50)

    # Additional Information
    address = models.TextField(_("Address"), blank=True)
    emergency_contact_name = models.CharField(
        _("Emergency contact name"), max_length=100, blank=True
    )
    emergency_contact_phone = models.CharField(
        _("Emergency contact phone"), max_length=20, blank=True
    )
    notes = models.TextField(_("Notes"), blank=True)

    # User account link
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employee",
        verbose_name=_("User account"),
    )

    # History tracking
    history = HistoricalRecords()

    class Meta:
        verbose_name = _("Employee")
        verbose_name_plural = _("Employees")
        ordering = ["employee_number"]

    def __str__(self):
        return f"{self.employee_number} - {self.full_name}"

    @property
    def full_name(self):
        """Return full name (Korean style: last + first)."""
        return f"{self.last_name}{self.first_name}"

    @property
    def years_of_service(self):
        """Calculate years of service."""
        end_date = self.resignation_date or date.today()
        delta = end_date - self.hire_date
        return delta.days // 365

    @property
    def months_of_service(self):
        """Calculate months of service."""
        end_date = self.resignation_date or date.today()
        delta = end_date - self.hire_date
        return delta.days // 30

    @property
    def age(self):
        """Calculate age."""
        today = date.today()
        return (
            today.year
            - self.birth_date.year
            - (
                (today.month, today.day)
                < (self.birth_date.month, self.birth_date.day)
            )
        )

    @property
    def is_manager(self):
        """Check if employee has manager position."""
        return self.job_position and self.job_position.is_manager


class DocumentType(models.TextChoices):
    """Document type choices."""

    CONTRACT = "CONTRACT", _("Employment Contract")
    RESUME = "RESUME", _("Resume")
    CERTIFICATE = "CERTIFICATE", _("Certificate")
    ID_COPY = "ID_COPY", _("ID Copy")
    DIPLOMA = "DIPLOMA", _("Diploma")
    OTHER = "OTHER", _("Other")


class EmployeeDocument(AuditedModel):
    """Employee document model."""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name=_("Employee"),
    )
    document_type = models.CharField(
        _("Document type"),
        max_length=20,
        choices=DocumentType.choices,
    )
    title = models.CharField(_("Title"), max_length=255)
    file = models.FileField(_("File"), upload_to="employees/documents/")
    expiry_date = models.DateField(_("Expiry date"), null=True, blank=True)
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Employee Document")
        verbose_name_plural = _("Employee Documents")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee.full_name} - {self.title}"

    @property
    def is_expired(self):
        """Check if document is expired."""
        if self.expiry_date:
            return self.expiry_date < date.today()
        return False


class HistoryType(models.TextChoices):
    """Employee history type choices."""

    HIRE = "HIRE", _("Hire")
    PROMOTION = "PROMOTION", _("Promotion")
    TRANSFER = "TRANSFER", _("Transfer")
    SALARY_CHANGE = "SALARY_CHANGE", _("Salary Change")
    POSITION_CHANGE = "POSITION_CHANGE", _("Position Change")
    LEAVE_START = "LEAVE_START", _("Leave Start")
    LEAVE_END = "LEAVE_END", _("Leave End")
    RESIGNATION = "RESIGNATION", _("Resignation")


class EmployeeHistory(AuditedModel):
    """Employee history record model."""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="employment_history",
        verbose_name=_("Employee"),
    )
    history_type = models.CharField(
        _("History type"),
        max_length=20,
        choices=HistoryType.choices,
    )
    effective_date = models.DateField(_("Effective date"))

    # Department change
    previous_department = models.ForeignKey(
        "organization.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("Previous department"),
    )
    new_department = models.ForeignKey(
        "organization.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("New department"),
    )

    # Grade change
    previous_grade = models.ForeignKey(
        "organization.JobGrade",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("Previous grade"),
    )
    new_grade = models.ForeignKey(
        "organization.JobGrade",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("New grade"),
    )

    # Position change
    previous_position = models.ForeignKey(
        "organization.JobPosition",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("Previous position"),
    )
    new_position = models.ForeignKey(
        "organization.JobPosition",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("New position"),
    )

    # Salary change
    previous_salary = MoneyField(
        _("Previous salary"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
        null=True,
        blank=True,
    )
    new_salary = MoneyField(
        _("New salary"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
        null=True,
        blank=True,
    )

    reason = models.TextField(_("Reason"), blank=True)

    class Meta:
        verbose_name = _("Employee History")
        verbose_name_plural = _("Employee Histories")
        ordering = ["-effective_date", "-created_at"]

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_history_type_display()} ({self.effective_date})"
