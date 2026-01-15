from decimal import Decimal

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition
from djmoney.models.fields import MoneyField
from simple_history.models import HistoricalRecords

from core.models import AuditedModel


class CalculationType(models.TextChoices):
    """Calculation type choices for allowances and deductions."""

    FIXED = "FIXED", _("Fixed Amount")
    PERCENTAGE = "PERCENTAGE", _("Percentage of Base Salary")
    HOURLY = "HOURLY", _("Hourly Rate")
    FORMULA = "FORMULA", _("Custom Formula")


class AllowanceType(AuditedModel):
    """Allowance type master data."""

    name = models.CharField(_("Allowance name"), max_length=100)
    code = models.CharField(_("Code"), max_length=20, unique=True)
    calculation_type = models.CharField(
        _("Calculation type"),
        max_length=20,
        choices=CalculationType.choices,
        default=CalculationType.FIXED,
    )
    default_amount = MoneyField(
        _("Default amount"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
        default=0,
    )
    default_percentage = models.DecimalField(
        _("Default percentage"),
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text=_("Percentage of base salary (e.g., 10.00 for 10%)"),
    )
    is_taxable = models.BooleanField(
        _("Taxable"), default=True, help_text=_("Subject to income tax")
    )
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True)
    display_order = models.PositiveIntegerField(_("Display order"), default=0)

    class Meta:
        verbose_name = _("Allowance Type")
        verbose_name_plural = _("Allowance Types")
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class DeductionType(AuditedModel):
    """Deduction type master data."""

    name = models.CharField(_("Deduction name"), max_length=100)
    code = models.CharField(_("Code"), max_length=20, unique=True)
    calculation_type = models.CharField(
        _("Calculation type"),
        max_length=20,
        choices=CalculationType.choices,
        default=CalculationType.PERCENTAGE,
    )
    default_rate = models.DecimalField(
        _("Default rate"),
        max_digits=5,
        decimal_places=4,
        default=0,
        help_text=_("Deduction rate (e.g., 0.0450 for 4.5%)"),
    )
    employer_rate = models.DecimalField(
        _("Employer rate"),
        max_digits=5,
        decimal_places=4,
        default=0,
        help_text=_("Employer contribution rate (for insurance)"),
    )
    min_amount = MoneyField(
        _("Minimum amount"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
        null=True,
        blank=True,
    )
    max_amount = MoneyField(
        _("Maximum amount"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
        null=True,
        blank=True,
    )
    is_statutory = models.BooleanField(
        _("Statutory deduction"),
        default=False,
        help_text=_("Legal mandatory deduction (4대보험, 세금)"),
    )
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        verbose_name = _("Deduction Type")
        verbose_name_plural = _("Deduction Types")
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class PayrollPeriodStatus(models.TextChoices):
    """Payroll period status choices."""

    DRAFT = "DRAFT", _("Draft")
    CALCULATING = "CALCULATING", _("Calculating")
    PENDING_APPROVAL = "PENDING_APPROVAL", _("Pending Approval")
    APPROVED = "APPROVED", _("Approved")
    PAID = "PAID", _("Paid")
    CLOSED = "CLOSED", _("Closed")


class PayrollPeriod(AuditedModel):
    """Payroll period model with FSM workflow."""

    year = models.PositiveIntegerField(_("Year"))
    month = models.PositiveIntegerField(_("Month"))
    name = models.CharField(_("Period name"), max_length=100)

    # Period dates
    start_date = models.DateField(_("Start date"))
    end_date = models.DateField(_("End date"))
    payment_date = models.DateField(_("Payment date"))

    # FSM State
    status = FSMField(
        _("Status"),
        default=PayrollPeriodStatus.DRAFT,
        choices=PayrollPeriodStatus.choices,
    )

    # Statistics
    total_gross = MoneyField(
        _("Total gross salary"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
        default=0,
    )
    total_deductions = MoneyField(
        _("Total deductions"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
        default=0,
    )
    total_net = MoneyField(
        _("Total net salary"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
        default=0,
    )
    employee_count = models.PositiveIntegerField(_("Employee count"), default=0)

    # Approval
    approved_by = models.ForeignKey(
        "employees.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_payroll_periods",
        verbose_name=_("Approved by"),
    )
    approved_at = models.DateTimeField(_("Approved at"), null=True, blank=True)

    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Payroll Period")
        verbose_name_plural = _("Payroll Periods")
        unique_together = ["year", "month"]
        ordering = ["-year", "-month"]

    def __str__(self):
        return f"{self.year}년 {self.month}월 급여"

    # FSM Transitions
    @transition(
        field=status, source=PayrollPeriodStatus.DRAFT, target=PayrollPeriodStatus.CALCULATING
    )
    def start_calculation(self):
        """Start payroll calculation."""
        pass

    @transition(
        field=status,
        source=PayrollPeriodStatus.CALCULATING,
        target=PayrollPeriodStatus.PENDING_APPROVAL,
    )
    def submit_for_approval(self):
        """Submit for approval after calculation."""
        pass

    @transition(
        field=status,
        source=PayrollPeriodStatus.PENDING_APPROVAL,
        target=PayrollPeriodStatus.APPROVED,
    )
    def approve(self):
        """Approve payroll period."""
        self.approved_at = timezone.now()

    @transition(
        field=status, source=PayrollPeriodStatus.APPROVED, target=PayrollPeriodStatus.PAID
    )
    def mark_as_paid(self):
        """Mark as paid."""
        pass

    @transition(
        field=status, source=PayrollPeriodStatus.PAID, target=PayrollPeriodStatus.CLOSED
    )
    def close_period(self):
        """Close payroll period."""
        pass


class ContractType(models.TextChoices):
    """Salary contract type choices."""

    INITIAL = "INITIAL", _("Initial Contract")
    RENEWAL = "RENEWAL", _("Renewal")
    RAISE = "RAISE", _("Salary Raise")
    PROMOTION = "PROMOTION", _("Promotion")


class SalaryContract(AuditedModel):
    """Salary contract model."""

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="salary_contracts",
        verbose_name=_("Employee"),
    )

    # Contract period
    effective_date = models.DateField(_("Effective date"))
    end_date = models.DateField(_("End date"), null=True, blank=True)

    # Salary information
    annual_salary = MoneyField(
        _("Annual salary"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
    )
    monthly_base_salary = MoneyField(
        _("Monthly base salary"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
    )

    # Contract type
    contract_type = models.CharField(
        _("Contract type"),
        max_length=20,
        choices=ContractType.choices,
        default=ContractType.INITIAL,
    )

    # Metadata
    is_active = models.BooleanField(_("Active"), default=True)
    previous_contract = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="next_contracts",
        verbose_name=_("Previous contract"),
    )
    approved_by = models.ForeignKey(
        "employees.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_salary_contracts",
        verbose_name=_("Approved by"),
    )
    approved_at = models.DateTimeField(_("Approved at"), null=True, blank=True)

    notes = models.TextField(_("Notes"), blank=True)
    document = models.FileField(
        _("Contract document"),
        upload_to="payroll/contracts/",
        blank=True,
    )

    # History tracking
    history = HistoricalRecords()

    class Meta:
        verbose_name = _("Salary Contract")
        verbose_name_plural = _("Salary Contracts")
        ordering = ["-effective_date"]

    def __str__(self):
        return f"{self.employee.full_name} - {self.effective_date} ({self.get_contract_type_display()})"

    def save(self, *args, **kwargs):
        # Calculate monthly base salary from annual salary
        if self.annual_salary and not self.monthly_base_salary:
            self.monthly_base_salary = self.annual_salary / 12
        super().save(*args, **kwargs)


class PayslipStatus(models.TextChoices):
    """Payslip status choices."""

    DRAFT = "DRAFT", _("Draft")
    CALCULATED = "CALCULATED", _("Calculated")
    APPROVED = "APPROVED", _("Approved")
    PAID = "PAID", _("Paid")


class PaymentMethod(models.TextChoices):
    """Payment method choices."""

    BANK_TRANSFER = "BANK_TRANSFER", _("Bank Transfer")
    CASH = "CASH", _("Cash")
    CHECK = "CHECK", _("Check")


class Payslip(AuditedModel):
    """Individual payslip model."""

    payroll_period = models.ForeignKey(
        PayrollPeriod,
        on_delete=models.CASCADE,
        related_name="payslips",
        verbose_name=_("Payroll period"),
    )
    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="payslips",
        verbose_name=_("Employee"),
    )

    # Work information
    work_days = models.DecimalField(
        _("Work days"), max_digits=5, decimal_places=2, default=0
    )
    paid_leave_days = models.DecimalField(
        _("Paid leave days"), max_digits=5, decimal_places=2, default=0
    )
    unpaid_leave_days = models.DecimalField(
        _("Unpaid leave days"), max_digits=5, decimal_places=2, default=0
    )
    overtime_hours = models.DecimalField(
        _("Overtime hours"), max_digits=6, decimal_places=2, default=0
    )
    night_hours = models.DecimalField(
        _("Night hours"), max_digits=6, decimal_places=2, default=0
    )
    holiday_hours = models.DecimalField(
        _("Holiday hours"), max_digits=6, decimal_places=2, default=0
    )

    # Salary components
    base_salary = MoneyField(
        _("Base salary"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
        default=0,
    )
    total_allowances = MoneyField(
        _("Total allowances"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
        default=0,
    )
    overtime_pay = MoneyField(
        _("Overtime pay"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
        default=0,
    )
    gross_salary = MoneyField(
        _("Gross salary"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
        default=0,
    )

    # Deductions
    total_deductions = MoneyField(
        _("Total deductions"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
        default=0,
    )
    income_tax = MoneyField(
        _("Income tax"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
        default=0,
    )
    resident_tax = MoneyField(
        _("Resident tax"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
        default=0,
    )
    national_pension = MoneyField(
        _("National pension"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
        default=0,
    )
    health_insurance = MoneyField(
        _("Health insurance"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
        default=0,
    )
    long_term_care = MoneyField(
        _("Long-term care insurance"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
        default=0,
    )
    employment_insurance = MoneyField(
        _("Employment insurance"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
        default=0,
    )
    other_deductions = MoneyField(
        _("Other deductions"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
        default=0,
    )

    # Net salary
    net_salary = MoneyField(
        _("Net salary"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
        default=0,
    )

    # Status
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=PayslipStatus.choices,
        default=PayslipStatus.DRAFT,
    )

    # Payment information
    payment_date = models.DateField(_("Payment date"), null=True, blank=True)
    payment_method = models.CharField(
        _("Payment method"),
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.BANK_TRANSFER,
    )

    # Attachments
    notes = models.TextField(_("Notes"), blank=True)
    pdf_file = models.FileField(
        _("PDF file"),
        upload_to="payroll/payslips/",
        blank=True,
    )

    # History tracking
    history = HistoricalRecords()

    class Meta:
        verbose_name = _("Payslip")
        verbose_name_plural = _("Payslips")
        unique_together = ["payroll_period", "employee"]
        ordering = ["-payroll_period__year", "-payroll_period__month", "employee"]

    def __str__(self):
        return f"{self.employee.full_name} - {self.payroll_period}"

    def calculate_gross(self):
        """Calculate gross salary."""
        self.gross_salary = self.base_salary + self.total_allowances + self.overtime_pay
        return self.gross_salary

    def calculate_net(self):
        """Calculate net salary."""
        self.net_salary = self.gross_salary - self.total_deductions
        return self.net_salary


class PayslipAllowance(AuditedModel):
    """Payslip allowance detail."""

    payslip = models.ForeignKey(
        Payslip,
        on_delete=models.CASCADE,
        related_name="allowances",
        verbose_name=_("Payslip"),
    )
    allowance_type = models.ForeignKey(
        AllowanceType,
        on_delete=models.PROTECT,
        related_name="payslip_allowances",
        verbose_name=_("Allowance type"),
    )

    amount = MoneyField(
        _("Amount"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
    )
    quantity = models.DecimalField(
        _("Quantity"), max_digits=10, decimal_places=2, default=1, help_text=_("Hours or units")
    )
    rate = models.DecimalField(
        _("Rate"), max_digits=10, decimal_places=2, default=0, help_text=_("Rate per unit")
    )

    calculation_note = models.TextField(_("Calculation note"), blank=True)

    class Meta:
        verbose_name = _("Payslip Allowance")
        verbose_name_plural = _("Payslip Allowances")
        ordering = ["allowance_type__display_order"]

    def __str__(self):
        return f"{self.payslip} - {self.allowance_type.name}"


class PayslipDeduction(AuditedModel):
    """Payslip deduction detail."""

    payslip = models.ForeignKey(
        Payslip,
        on_delete=models.CASCADE,
        related_name="deductions",
        verbose_name=_("Payslip"),
    )
    deduction_type = models.ForeignKey(
        DeductionType,
        on_delete=models.PROTECT,
        related_name="payslip_deductions",
        verbose_name=_("Deduction type"),
    )

    amount = MoneyField(
        _("Amount"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
    )
    base_amount = MoneyField(
        _("Base amount"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
        help_text=_("Amount used for calculation"),
    )
    rate = models.DecimalField(
        _("Rate"), max_digits=5, decimal_places=4, default=0, help_text=_("Deduction rate")
    )

    calculation_note = models.TextField(_("Calculation note"), blank=True)

    class Meta:
        verbose_name = _("Payslip Deduction")
        verbose_name_plural = _("Payslip Deductions")
        ordering = ["deduction_type__name"]

    def __str__(self):
        return f"{self.payslip} - {self.deduction_type.name}"


class AdjustmentType(models.TextChoices):
    """Adjustment type choices."""

    BONUS = "BONUS", _("Bonus")
    INCENTIVE = "INCENTIVE", _("Incentive")
    RETROACTIVE = "RETROACTIVE", _("Retroactive Payment")
    DEDUCTION = "DEDUCTION", _("Deduction")
    CORRECTION = "CORRECTION", _("Correction")


class PayrollAdjustment(AuditedModel):
    """Payroll adjustment model (bonus, deduction, etc.)."""

    payslip = models.ForeignKey(
        Payslip,
        on_delete=models.CASCADE,
        related_name="adjustments",
        verbose_name=_("Payslip"),
    )

    adjustment_type = models.CharField(
        _("Adjustment type"),
        max_length=20,
        choices=AdjustmentType.choices,
    )

    amount = MoneyField(
        _("Amount"),
        max_digits=14,
        decimal_places=2,
        default_currency="KRW",
        help_text=_("Positive for addition, negative for deduction"),
    )
    reason = models.TextField(_("Reason"))

    approved_by = models.ForeignKey(
        "employees.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_adjustments",
        verbose_name=_("Approved by"),
    )
    approved_at = models.DateTimeField(_("Approved at"), null=True, blank=True)

    class Meta:
        verbose_name = _("Payroll Adjustment")
        verbose_name_plural = _("Payroll Adjustments")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.payslip} - {self.get_adjustment_type_display()} ({self.amount})"
