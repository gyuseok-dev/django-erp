from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from guardian.admin import GuardedModelAdmin
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (
    ChoicesCheckboxFilter,
    RangeDateFilter,
    RelatedDropdownFilter,
)
from unfold.contrib.import_export.forms import ExportForm, ImportForm
from unfold.decorators import action, display

from .models import (
    AllowanceType,
    DeductionType,
    Payslip,
    PayslipAllowance,
    PayslipDeduction,
    PayrollAdjustment,
    PayrollPeriod,
    PayrollPeriodStatus,
    PayslipStatus,
    SalaryContract,
)


@admin.register(AllowanceType)
class AllowanceTypeAdmin(ModelAdmin):
    """Allowance type admin."""

    list_display = [
        "display_header",
        "code",
        "calculation_type",
        "display_amount",
        "display_taxable",
        "is_active",
    ]
    list_filter = [
        ("calculation_type", ChoicesCheckboxFilter),
        "is_taxable",
        "is_active",
    ]
    search_fields = ["name", "code", "description"]
    ordering = ["display_order", "name"]

    fieldsets = [
        (
            _("Basic Information"),
            {
                "fields": [
                    ("name", "code"),
                    "calculation_type",
                    ("default_amount", "default_percentage"),
                    ("is_taxable", "is_active"),
                    "display_order",
                ]
            },
        ),
        (
            _("Description"),
            {
                "classes": ["tab"],
                "fields": ["description"],
            },
        ),
    ]

    @display(description=_("Name"), header=True)
    def display_header(self, instance):
        return instance.name

    @display(description=_("Amount"))
    def display_amount(self, instance):
        if instance.calculation_type == "FIXED":
            return f"₩{instance.default_amount:,}"
        elif instance.calculation_type == "PERCENTAGE":
            return f"{instance.default_percentage}%"
        return "-"

    @display(
        description=_("Taxable"),
        label={
            True: "success",
            False: "info",
        },
    )
    def display_taxable(self, instance):
        return _("Yes") if instance.is_taxable else _("No")


@admin.register(DeductionType)
class DeductionTypeAdmin(ModelAdmin):
    """Deduction type admin."""

    list_display = [
        "display_header",
        "code",
        "calculation_type",
        "display_rate",
        "display_statutory",
        "is_active",
    ]
    list_filter = [
        ("calculation_type", ChoicesCheckboxFilter),
        "is_statutory",
        "is_active",
    ]
    search_fields = ["name", "code", "description"]
    ordering = ["name"]

    fieldsets = [
        (
            _("Basic Information"),
            {
                "fields": [
                    ("name", "code"),
                    "calculation_type",
                    ("default_rate", "employer_rate"),
                    ("min_amount", "max_amount"),
                    ("is_statutory", "is_active"),
                ]
            },
        ),
        (
            _("Description"),
            {
                "classes": ["tab"],
                "fields": ["description"],
            },
        ),
    ]

    @display(description=_("Name"), header=True)
    def display_header(self, instance):
        return instance.name

    @display(description=_("Rate"))
    def display_rate(self, instance):
        if instance.calculation_type == "PERCENTAGE":
            return f"{float(instance.default_rate) * 100:.2f}%"
        return "-"

    @display(
        description=_("Statutory"),
        label={
            True: "danger",
            False: "info",
        },
    )
    def display_statutory(self, instance):
        return _("Yes") if instance.is_statutory else _("No")


class PayslipInline(TabularInline):
    """Payslip inline for PayrollPeriod."""

    model = Payslip
    extra = 0
    fields = [
        "employee",
        "base_salary",
        "gross_salary",
        "total_deductions",
        "net_salary",
        "status",
    ]
    readonly_fields = [
        "base_salary",
        "gross_salary",
        "total_deductions",
        "net_salary",
        "status",
    ]
    ordering = ["employee__employee_number"]
    max_num = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(ModelAdmin):
    """Payroll period admin."""

    list_display = [
        "display_header",
        "display_period",
        "payment_date",
        "employee_count",
        "display_amounts",
        "display_status",
    ]
    list_filter = [
        "year",
        "month",
        ("status", ChoicesCheckboxFilter),
        ("payment_date", RangeDateFilter),
    ]
    search_fields = ["name"]
    readonly_fields = [
        "total_gross",
        "total_deductions",
        "total_net",
        "employee_count",
        "approved_by",
        "approved_at",
        "created_at",
        "modified_at",
    ]
    autocomplete_fields = ["approved_by"]
    ordering = ["-year", "-month"]

    fieldsets = [
        (
            _("Period Information"),
            {
                "fields": [
                    "name",
                    ("year", "month"),
                    ("start_date", "end_date"),
                    "payment_date",
                    "status",
                ]
            },
        ),
        (
            _("Statistics"),
            {
                "classes": ["tab"],
                "fields": [
                    "employee_count",
                    "total_gross",
                    "total_deductions",
                    "total_net",
                ],
            },
        ),
        (
            _("Approval"),
            {
                "classes": ["tab"],
                "fields": [
                    "approved_by",
                    "approved_at",
                ],
            },
        ),
        (
            _("Notes"),
            {
                "classes": ["tab"],
                "fields": ["notes"],
            },
        ),
        (
            _("Timestamps"),
            {
                "classes": ["tab"],
                "fields": [
                    "created_at",
                    "modified_at",
                ],
            },
        ),
    ]

    inlines = [PayslipInline]

    @display(description=_("Period"), header=True)
    def display_header(self, instance):
        return f"{instance.year}년 {instance.month}월"

    @display(description=_("Period"))
    def display_period(self, instance):
        return f"{instance.start_date} ~ {instance.end_date}"

    @display(description=_("Total Amount"))
    def display_amounts(self, instance):
        return f"₩{instance.total_net:,}"

    @display(
        description=_("Status"),
        label={
            PayrollPeriodStatus.DRAFT: "info",
            PayrollPeriodStatus.CALCULATING: "warning",
            PayrollPeriodStatus.PENDING_APPROVAL: "warning",
            PayrollPeriodStatus.APPROVED: "success",
            PayrollPeriodStatus.PAID: "success",
            PayrollPeriodStatus.CLOSED: "danger",
        },
    )
    def display_status(self, instance):
        return instance.get_status_display()

    @action(description=_("Calculate Payroll"))
    def calculate_payroll_action(self, request, object_id):
        """Calculate payroll for this period."""
        from payroll.services.payroll_calculator import PayrollCalculator

        period = self.get_object(request, object_id)

        # Check if already calculating or beyond
        if period.status != PayrollPeriodStatus.DRAFT:
            messages.warning(
                request,
                _("Payroll period must be in DRAFT status to calculate."),
            )
            return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

        try:
            # Start calculation
            period.start_calculation()
            period.save()

            # Calculate payroll
            calculator = PayrollCalculator(period)
            payslips = calculator.calculate_all_employees()

            # Submit for approval
            period.submit_for_approval()
            period.save()

            messages.success(
                request,
                _(f"Successfully calculated payroll for {len(payslips)} employees."),
            )
        except Exception as e:
            messages.error(request, _(f"Error calculating payroll: {e}"))

        return HttpResponseRedirect(
            reverse(
                "admin:payroll_payrollperiod_change",
                args=[object_id],
            )
        )

    @action(description=_("Approve Payroll"))
    def approve_action(self, request, object_id):
        """Approve payroll period."""
        period = self.get_object(request, object_id)

        if period.status != PayrollPeriodStatus.PENDING_APPROVAL:
            messages.warning(
                request,
                _("Payroll period must be in PENDING_APPROVAL status to approve."),
            )
            return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

        try:
            period.approve()
            # Set approver to current user's employee
            if hasattr(request.user, "employee"):
                period.approved_by = request.user.employee
            period.save()

            messages.success(request, _("Payroll period approved successfully."))
        except Exception as e:
            messages.error(request, _(f"Error approving payroll: {e}"))

        return HttpResponseRedirect(
            reverse(
                "admin:payroll_payrollperiod_change",
                args=[object_id],
            )
        )

    @action(description=_("Mark as Paid"))
    def mark_as_paid_action(self, request, object_id):
        """Mark payroll period as paid."""
        period = self.get_object(request, object_id)

        if period.status != PayrollPeriodStatus.APPROVED:
            messages.warning(
                request,
                _("Payroll period must be in APPROVED status to mark as paid."),
            )
            return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

        try:
            period.mark_as_paid()
            period.save()

            # Update all payslips to PAID status
            period.payslips.update(status=PayslipStatus.PAID)

            messages.success(request, _("Payroll period marked as paid."))
        except Exception as e:
            messages.error(request, _(f"Error marking as paid: {e}"))

        return HttpResponseRedirect(
            reverse(
                "admin:payroll_payrollperiod_change",
                args=[object_id],
            )
        )

    actions_row = [
        "calculate_payroll_action",
        "approve_action",
        "mark_as_paid_action",
    ]


@admin.register(SalaryContract)
class SalaryContractAdmin(SimpleHistoryAdmin, ModelAdmin):
    """Salary contract admin."""

    list_display = [
        "display_header",
        "display_employee",
        "effective_date",
        "annual_salary",
        "monthly_base_salary",
        "contract_type",
        "is_active",
    ]
    list_filter = [
        ("employee__department", RelatedDropdownFilter),
        ("contract_type", ChoicesCheckboxFilter),
        ("effective_date", RangeDateFilter),
        "is_active",
    ]
    search_fields = [
        "employee__employee_number",
        "employee__first_name",
        "employee__last_name",
    ]
    autocomplete_fields = ["employee", "previous_contract", "approved_by"]
    readonly_fields = ["created_at", "modified_at", "approved_at"]
    ordering = ["-effective_date"]

    fieldsets = [
        (
            _("Contract Information"),
            {
                "fields": [
                    "employee",
                    "contract_type",
                    ("effective_date", "end_date"),
                    "is_active",
                ]
            },
        ),
        (
            _("Salary"),
            {
                "classes": ["tab"],
                "fields": [
                    "annual_salary",
                    "monthly_base_salary",
                ],
            },
        ),
        (
            _("Reference"),
            {
                "classes": ["tab"],
                "fields": [
                    "previous_contract",
                    "document",
                ],
            },
        ),
        (
            _("Approval"),
            {
                "classes": ["tab"],
                "fields": [
                    "approved_by",
                    "approved_at",
                ],
            },
        ),
        (
            _("Notes"),
            {
                "classes": ["tab"],
                "fields": ["notes"],
            },
        ),
        (
            _("Timestamps"),
            {
                "classes": ["tab"],
                "fields": [
                    "created_at",
                    "modified_at",
                ],
            },
        ),
    ]

    @display(description=_("Contract"), header=True)
    def display_header(self, instance):
        return f"{instance.employee.full_name} - {instance.effective_date}"

    @display(description=_("Employee"))
    def display_employee(self, instance):
        return instance.employee.full_name


class PayslipAllowanceInline(TabularInline):
    """Payslip allowance inline."""

    model = PayslipAllowance
    extra = 0
    fields = ["allowance_type", "quantity", "rate", "amount", "calculation_note"]
    autocomplete_fields = ["allowance_type"]


class PayslipDeductionInline(TabularInline):
    """Payslip deduction inline."""

    model = PayslipDeduction
    extra = 0
    fields = ["deduction_type", "base_amount", "rate", "amount", "calculation_note"]
    autocomplete_fields = ["deduction_type"]


class PayrollAdjustmentInline(TabularInline):
    """Payroll adjustment inline."""

    model = PayrollAdjustment
    extra = 0
    fields = ["adjustment_type", "amount", "reason", "approved_by", "approved_at"]
    autocomplete_fields = ["approved_by"]
    readonly_fields = ["approved_at"]


@admin.register(Payslip)
class PayslipAdmin(GuardedModelAdmin, SimpleHistoryAdmin, ModelAdmin):
    """Payslip admin."""

    list_display = [
        "display_header",
        "display_employee",
        "display_period",
        "display_gross",
        "display_deductions",
        "display_net",
        "display_status",
    ]
    list_filter = [
        ("payroll_period", RelatedDropdownFilter),
        ("employee__department", RelatedDropdownFilter),
        ("status", ChoicesCheckboxFilter),
    ]
    search_fields = [
        "employee__employee_number",
        "employee__first_name",
        "employee__last_name",
    ]
    autocomplete_fields = ["payroll_period", "employee"]
    readonly_fields = [
        "gross_salary",
        "total_allowances",
        "overtime_pay",
        "total_deductions",
        "net_salary",
        "created_at",
        "modified_at",
    ]
    ordering = [
        "-payroll_period__year",
        "-payroll_period__month",
        "employee__employee_number",
    ]

    fieldsets = [
        (
            _("Basic Information"),
            {
                "fields": [
                    "payroll_period",
                    "employee",
                    "status",
                ]
            },
        ),
        (
            _("Work Information"),
            {
                "classes": ["tab"],
                "fields": [
                    ("work_days", "paid_leave_days", "unpaid_leave_days"),
                    ("overtime_hours", "night_hours", "holiday_hours"),
                ],
            },
        ),
        (
            _("Salary"),
            {
                "classes": ["tab"],
                "fields": [
                    "base_salary",
                    "total_allowances",
                    "overtime_pay",
                    "gross_salary",
                ],
            },
        ),
        (
            _("Deductions"),
            {
                "classes": ["tab"],
                "fields": [
                    "income_tax",
                    "resident_tax",
                    "national_pension",
                    "health_insurance",
                    "long_term_care",
                    "employment_insurance",
                    "other_deductions",
                    "total_deductions",
                ],
            },
        ),
        (
            _("Net Salary"),
            {
                "classes": ["tab"],
                "fields": [
                    "net_salary",
                ],
            },
        ),
        (
            _("Payment"),
            {
                "classes": ["tab"],
                "fields": [
                    ("payment_date", "payment_method"),
                    "pdf_file",
                ],
            },
        ),
        (
            _("Notes"),
            {
                "classes": ["tab"],
                "fields": ["notes"],
            },
        ),
        (
            _("Timestamps"),
            {
                "classes": ["tab"],
                "fields": [
                    "created_at",
                    "modified_at",
                ],
            },
        ),
    ]

    inlines = [
        PayslipAllowanceInline,
        PayslipDeductionInline,
        PayrollAdjustmentInline,
    ]

    @display(description=_("Payslip"), header=True)
    def display_header(self, instance):
        return f"{instance.employee.full_name} - {instance.payroll_period}"

    @display(description=_("Employee"))
    def display_employee(self, instance):
        return instance.employee.full_name

    @display(description=_("Period"))
    def display_period(self, instance):
        return f"{instance.payroll_period.year}년 {instance.payroll_period.month}월"

    @display(description=_("Gross"))
    def display_gross(self, instance):
        return f"₩{instance.gross_salary:,}"

    @display(description=_("Deductions"))
    def display_deductions(self, instance):
        return f"₩{instance.total_deductions:,}"

    @display(description=_("Net"))
    def display_net(self, instance):
        return f"₩{instance.net_salary:,}"

    @display(
        description=_("Status"),
        label={
            PayslipStatus.DRAFT: "info",
            PayslipStatus.CALCULATED: "warning",
            PayslipStatus.APPROVED: "success",
            PayslipStatus.PAID: "success",
        },
    )
    def display_status(self, instance):
        return instance.get_status_display()


@admin.register(PayslipAllowance)
class PayslipAllowanceAdmin(ModelAdmin):
    """Payslip allowance admin."""

    list_display = [
        "display_header",
        "allowance_type",
        "quantity",
        "rate",
        "amount",
    ]
    list_filter = [
        ("payslip__payroll_period", RelatedDropdownFilter),
        ("allowance_type", RelatedDropdownFilter),
    ]
    search_fields = [
        "payslip__employee__first_name",
        "payslip__employee__last_name",
        "allowance_type__name",
    ]
    autocomplete_fields = ["payslip", "allowance_type"]
    ordering = [
        "-payslip__payroll_period__year",
        "-payslip__payroll_period__month",
        "payslip__employee__employee_number",
        "allowance_type__display_order",
    ]

    @display(description=_("Payslip"), header=True)
    def display_header(self, instance):
        return f"{instance.payslip.employee.full_name} - {instance.allowance_type.name}"


@admin.register(PayslipDeduction)
class PayslipDeductionAdmin(ModelAdmin):
    """Payslip deduction admin."""

    list_display = [
        "display_header",
        "deduction_type",
        "base_amount",
        "rate",
        "amount",
    ]
    list_filter = [
        ("payslip__payroll_period", RelatedDropdownFilter),
        ("deduction_type", RelatedDropdownFilter),
    ]
    search_fields = [
        "payslip__employee__first_name",
        "payslip__employee__last_name",
        "deduction_type__name",
    ]
    autocomplete_fields = ["payslip", "deduction_type"]
    ordering = [
        "-payslip__payroll_period__year",
        "-payslip__payroll_period__month",
        "payslip__employee__employee_number",
        "deduction_type__name",
    ]

    @display(description=_("Payslip"), header=True)
    def display_header(self, instance):
        return f"{instance.payslip.employee.full_name} - {instance.deduction_type.name}"


@admin.register(PayrollAdjustment)
class PayrollAdjustmentAdmin(ModelAdmin):
    """Payroll adjustment admin."""

    list_display = [
        "display_header",
        "adjustment_type",
        "amount",
        "approved_by",
        "approved_at",
    ]
    list_filter = [
        ("payslip__payroll_period", RelatedDropdownFilter),
        ("adjustment_type", ChoicesCheckboxFilter),
    ]
    search_fields = [
        "payslip__employee__first_name",
        "payslip__employee__last_name",
        "reason",
    ]
    autocomplete_fields = ["payslip", "approved_by"]
    readonly_fields = ["approved_at", "created_at", "modified_at"]
    ordering = ["-created_at"]

    fieldsets = [
        (
            _("Adjustment Information"),
            {
                "fields": [
                    "payslip",
                    "adjustment_type",
                    "amount",
                    "reason",
                ]
            },
        ),
        (
            _("Approval"),
            {
                "classes": ["tab"],
                "fields": [
                    "approved_by",
                    "approved_at",
                ],
            },
        ),
        (
            _("Timestamps"),
            {
                "classes": ["tab"],
                "fields": [
                    "created_at",
                    "modified_at",
                ],
            },
        ),
    ]

    @display(description=_("Adjustment"), header=True)
    def display_header(self, instance):
        return f"{instance.payslip.employee.full_name} - {instance.get_adjustment_type_display()}"
