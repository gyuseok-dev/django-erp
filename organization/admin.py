from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportModelAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import RangeDateFilter
from unfold.contrib.import_export.forms import ExportForm, ImportForm
from unfold.decorators import display

from .models import Company, Department, JobGrade, JobPosition


@admin.register(Company)
class CompanyAdmin(ModelAdmin, ImportExportModelAdmin):
    """Company admin."""

    import_form_class = ImportForm
    export_form_class = ExportForm

    list_display = [
        "display_header",
        "registration_number",
        "ceo_name",
        "phone",
        "created_at",
    ]
    list_filter = [("created_at", RangeDateFilter)]
    search_fields = ["name", "registration_number", "ceo_name"]
    readonly_fields = ["created_at", "modified_at"]

    fieldsets = [
        (
            _("Basic Information"),
            {
                "fields": [
                    "name",
                    "registration_number",
                    "ceo_name",
                    "logo",
                ]
            },
        ),
        (
            _("Contact Information"),
            {
                "fields": [
                    ("phone", "email"),
                    "website",
                    "address",
                ]
            },
        ),
        (
            _("Additional Information"),
            {
                "fields": [
                    "established_date",
                    ("created_at", "modified_at"),
                ]
            },
        ),
    ]

    @display(description=_("Company"), header=True)
    def display_header(self, instance):
        return [
            instance.name,
            instance.address[:50] if instance.address else "",
            instance.name[0],
            {"path": instance.logo.url if instance.logo else None},
        ]


@admin.register(Department)
class DepartmentAdmin(ModelAdmin, ImportExportModelAdmin):
    """Department admin."""

    import_form_class = ImportForm
    export_form_class = ExportForm

    list_display = [
        "display_header",
        "code",
        "display_parent",
        "display_manager",
        "display_employee_count",
        "is_active",
    ]
    list_filter = ["company", "is_active", "parent"]
    search_fields = ["name", "code"]
    autocomplete_fields = ["company", "parent", "manager"]
    readonly_fields = ["created_at", "modified_at"]

    fieldsets = [
        (
            _("Basic Information"),
            {
                "fields": [
                    "company",
                    ("name", "code"),
                    "parent",
                    "manager",
                ]
            },
        ),
        (
            _("Details"),
            {
                "fields": [
                    "budget",
                    "description",
                    ("weight", "is_active"),
                ]
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": [
                    ("created_at", "modified_at"),
                ],
                "classes": ["collapse"],
            },
        ),
    ]

    @display(description=_("Department"), header=True)
    def display_header(self, instance):
        return [
            instance.name,
            instance.code,
            instance.name[0],
            None,
        ]

    @display(description=_("Parent"))
    def display_parent(self, instance):
        return instance.parent.name if instance.parent else "-"

    @display(description=_("Manager"))
    def display_manager(self, instance):
        return instance.manager.full_name if instance.manager else "-"

    @display(description=_("Employees"))
    def display_employee_count(self, instance):
        return instance.employee_count


@admin.register(JobGrade)
class JobGradeAdmin(ModelAdmin, ImportExportModelAdmin):
    """Job grade admin."""

    import_form_class = ImportForm
    export_form_class = ExportForm

    list_display = [
        "display_header",
        "level",
        "display_salary_range",
        "annual_leave_days",
    ]
    list_filter = ["level"]
    search_fields = ["name"]
    ordering = ["level"]

    fieldsets = [
        (
            _("Basic Information"),
            {
                "fields": [
                    ("name", "level"),
                    "description",
                ]
            },
        ),
        (
            _("Salary Range"),
            {
                "fields": [
                    ("base_salary_min", "base_salary_max"),
                ]
            },
        ),
        (
            _("Benefits"),
            {
                "fields": [
                    "annual_leave_days",
                ]
            },
        ),
    ]

    @display(description=_("Job Grade"), header=True)
    def display_header(self, instance):
        return [
            instance.name,
            f"Level {instance.level}",
            str(instance.level),
            None,
        ]

    @display(description=_("Salary Range"))
    def display_salary_range(self, instance):
        return f"{instance.base_salary_min} ~ {instance.base_salary_max}"


@admin.register(JobPosition)
class JobPositionAdmin(ModelAdmin, ImportExportModelAdmin):
    """Job position admin."""

    import_form_class = ImportForm
    export_form_class = ExportForm

    list_display = [
        "display_header",
        "allowance",
        "display_is_manager",
    ]
    list_filter = ["is_manager"]
    search_fields = ["name"]

    fieldsets = [
        (
            _("Basic Information"),
            {
                "fields": [
                    "name",
                    "description",
                ]
            },
        ),
        (
            _("Benefits & Permissions"),
            {
                "fields": [
                    "allowance",
                    "is_manager",
                ]
            },
        ),
    ]

    @display(description=_("Position"), header=True)
    def display_header(self, instance):
        return [
            instance.name,
            instance.description[:30] if instance.description else "",
            instance.name[0],
            None,
        ]

    @display(
        description=_("Manager"),
        label={
            True: "success",
            False: "default",
        },
    )
    def display_is_manager(self, instance):
        return instance.is_manager
