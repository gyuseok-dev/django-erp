from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from guardian.admin import GuardedModelAdmin
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin, StackedInline, TabularInline
from unfold.contrib.filters.admin import (
    ChoicesCheckboxFilter,
    RangeDateFilter,
    RelatedCheckboxFilter,
    RelatedDropdownFilter,
)
from unfold.contrib.import_export.forms import ExportForm, ImportForm
from unfold.decorators import display

from .models import (
    ContractType,
    Employee,
    EmployeeDocument,
    EmployeeHistory,
    EmployeeStatus,
)


class EmployeeDocumentInline(TabularInline):
    """Employee document inline."""

    model = EmployeeDocument
    extra = 0
    fields = ["document_type", "title", "file", "expiry_date"]


class EmployeeHistoryInline(TabularInline):
    """Employee history inline."""

    model = EmployeeHistory
    extra = 0
    readonly_fields = ["history_type", "effective_date", "reason", "created_at"]
    fields = ["history_type", "effective_date", "reason", "created_at"]
    ordering = ["-effective_date"]
    max_num = 0
    can_delete = False


@admin.register(Employee)
class EmployeeAdmin(
    GuardedModelAdmin, SimpleHistoryAdmin, ModelAdmin, ImportExportModelAdmin
):
    """Employee admin."""

    import_form_class = ImportForm
    export_form_class = ExportForm

    list_display = [
        "display_header",
        "display_department",
        "display_grade",
        "display_position",
        "display_status",
        "display_hire_date",
    ]
    list_filter = [
        ("department", RelatedDropdownFilter),
        ("job_grade", RelatedCheckboxFilter),
        ("status", ChoicesCheckboxFilter),
        ("contract_type", ChoicesCheckboxFilter),
        ("hire_date", RangeDateFilter),
    ]
    search_fields = [
        "employee_number",
        "first_name",
        "last_name",
        "email",
        "phone",
    ]
    autocomplete_fields = ["department", "job_grade", "job_position", "manager", "user"]
    readonly_fields = ["created_at", "modified_at", "years_of_service"]
    ordering = ["employee_number"]

    fieldsets = [
        (
            _("Basic Information"),
            {
                "fields": [
                    ("employee_number", "status"),
                    ("first_name", "last_name"),
                    ("email", "phone"),
                    ("birth_date", "gender"),
                    "profile_image",
                ]
            },
        ),
        (
            _("Organization"),
            {
                "classes": ["tab"],
                "fields": [
                    "department",
                    ("job_grade", "job_position"),
                    "manager",
                ],
            },
        ),
        (
            _("Contract"),
            {
                "classes": ["tab"],
                "fields": [
                    ("hire_date", "contract_type"),
                    "contract_end_date",
                    ("resignation_date", "resignation_reason"),
                    "years_of_service",
                ],
            },
        ),
        (
            _("Salary & Bank"),
            {
                "classes": ["tab"],
                "fields": [
                    "base_salary",
                    ("bank_name", "bank_account"),
                ],
            },
        ),
        (
            _("Additional Information"),
            {
                "classes": ["tab"],
                "fields": [
                    "address",
                    ("emergency_contact_name", "emergency_contact_phone"),
                    "notes",
                    "user",
                ],
            },
        ),
        (
            _("Timestamps"),
            {
                "classes": ["collapse"],
                "fields": [
                    ("created_at", "modified_at"),
                ],
            },
        ),
    ]

    inlines = [EmployeeDocumentInline, EmployeeHistoryInline]

    @display(description=_("Employee"), header=True)
    def display_header(self, instance):
        return [
            instance.full_name,
            instance.employee_number,
            instance.last_name[0] if instance.last_name else "?",
            {"path": instance.profile_image.url if instance.profile_image else None},
        ]

    @display(description=_("Department"))
    def display_department(self, instance):
        return instance.department.name

    @display(description=_("Grade"))
    def display_grade(self, instance):
        return instance.job_grade.name

    @display(description=_("Position"))
    def display_position(self, instance):
        return instance.job_position.name if instance.job_position else "-"

    @display(
        description=_("Status"),
        label={
            EmployeeStatus.ACTIVE: "success",
            EmployeeStatus.ON_LEAVE: "warning",
            EmployeeStatus.RESIGNED: "danger",
        },
    )
    def display_status(self, instance):
        return instance.status

    @display(description=_("Hire Date"))
    def display_hire_date(self, instance):
        return instance.hire_date


@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(ModelAdmin, ImportExportModelAdmin):
    """Employee document admin."""

    import_form_class = ImportForm
    export_form_class = ExportForm

    list_display = [
        "display_header",
        "document_type",
        "display_employee",
        "display_expiry",
        "created_at",
    ]
    list_filter = ["document_type", ("expiry_date", RangeDateFilter)]
    search_fields = ["title", "employee__first_name", "employee__last_name"]
    autocomplete_fields = ["employee"]

    @display(description=_("Document"), header=True)
    def display_header(self, instance):
        return [
            instance.title,
            instance.get_document_type_display(),
            instance.title[0],
            None,
        ]

    @display(description=_("Employee"))
    def display_employee(self, instance):
        return instance.employee.full_name

    @display(
        description=_("Expiry"),
        label=lambda instance: "danger" if instance.is_expired else "success",
    )
    def display_expiry(self, instance):
        if instance.expiry_date:
            return instance.expiry_date
        return _("No expiry")


@admin.register(EmployeeHistory)
class EmployeeHistoryAdmin(ModelAdmin):
    """Employee history admin."""

    list_display = [
        "display_header",
        "history_type",
        "effective_date",
        "display_employee",
    ]
    list_filter = ["history_type", ("effective_date", RangeDateFilter)]
    search_fields = ["employee__first_name", "employee__last_name"]
    autocomplete_fields = [
        "employee",
        "previous_department",
        "new_department",
        "previous_grade",
        "new_grade",
    ]
    readonly_fields = ["created_at"]

    @display(description=_("History"), header=True)
    def display_header(self, instance):
        return [
            instance.get_history_type_display(),
            str(instance.effective_date),
            instance.history_type[0],
            None,
        ]

    @display(description=_("Employee"))
    def display_employee(self, instance):
        return instance.employee.full_name
