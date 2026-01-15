from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportModelAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import (
    ChoicesCheckboxFilter,
    RangeDateFilter,
    RelatedDropdownFilter,
)
from unfold.contrib.import_export.forms import ExportForm, ImportForm
from unfold.decorators import action, display

from .models import (
    AttendanceRecord,
    AttendanceStatus,
    Holiday,
    OvertimeRequest,
    OvertimeRequestStatus,
    WorkSchedule,
)


@admin.register(WorkSchedule)
class WorkScheduleAdmin(ModelAdmin, ImportExportModelAdmin):
    """Work schedule admin."""

    import_form_class = ImportForm
    export_form_class = ExportForm

    list_display = [
        "display_header",
        "display_time_range",
        "display_break_time",
        "display_work_hours",
        "is_default",
    ]
    list_filter = ["is_default"]
    search_fields = ["name"]

    fieldsets = [
        (
            _("Basic Information"),
            {
                "fields": [
                    "name",
                    "description",
                    "is_default",
                ]
            },
        ),
        (
            _("Work Hours"),
            {
                "fields": [
                    ("start_time", "end_time"),
                    ("break_start", "break_end"),
                ]
            },
        ),
    ]

    @display(description=_("Schedule"), header=True)
    def display_header(self, instance):
        return [
            instance.name,
            instance.description[:30] if instance.description else "",
            instance.name[0],
            None,
        ]

    @display(description=_("Work Time"))
    def display_time_range(self, instance):
        return f"{instance.start_time.strftime('%H:%M')} - {instance.end_time.strftime('%H:%M')}"

    @display(description=_("Break Time"))
    def display_break_time(self, instance):
        return f"{instance.break_start.strftime('%H:%M')} - {instance.break_end.strftime('%H:%M')}"

    @display(description=_("Hours"))
    def display_work_hours(self, instance):
        return f"{instance.work_hours:.1f}h"


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(ModelAdmin, ImportExportModelAdmin):
    """Attendance record admin."""

    import_form_class = ImportForm
    export_form_class = ExportForm

    list_display = [
        "display_header",
        "display_employee",
        "display_check_in",
        "display_check_out",
        "display_work_hours",
        "display_status",
    ]
    list_filter = [
        ("date", RangeDateFilter),
        ("status", ChoicesCheckboxFilter),
        ("employee__department", RelatedDropdownFilter),
    ]
    search_fields = [
        "employee__first_name",
        "employee__last_name",
        "employee__employee_number",
    ]
    autocomplete_fields = ["employee", "schedule"]
    date_hierarchy = "date"

    fieldsets = [
        (
            _("Basic Information"),
            {
                "fields": [
                    "employee",
                    "date",
                    "schedule",
                    "status",
                ]
            },
        ),
        (
            _("Check In/Out"),
            {
                "fields": [
                    ("check_in", "check_out"),
                ]
            },
        ),
        (
            _("Calculated Values"),
            {
                "fields": [
                    ("work_hours", "overtime_hours"),
                    ("late_minutes", "early_leave_minutes"),
                ]
            },
        ),
        (
            _("Notes"),
            {
                "fields": ["notes"],
            },
        ),
    ]

    @display(description=_("Date"), header=True)
    def display_header(self, instance):
        return [
            str(instance.date),
            instance.date.strftime("%A"),
            str(instance.date.day),
            None,
        ]

    @display(description=_("Employee"))
    def display_employee(self, instance):
        return instance.employee.full_name

    @display(description=_("Check In"))
    def display_check_in(self, instance):
        if instance.check_in:
            return instance.check_in.strftime("%H:%M")
        return "-"

    @display(description=_("Check Out"))
    def display_check_out(self, instance):
        if instance.check_out:
            return instance.check_out.strftime("%H:%M")
        return "-"

    @display(description=_("Work Hours"))
    def display_work_hours(self, instance):
        return f"{instance.work_hours:.1f}h"

    @display(
        description=_("Status"),
        label={
            AttendanceStatus.PRESENT: "success",
            AttendanceStatus.LATE: "warning",
            AttendanceStatus.EARLY_LEAVE: "warning",
            AttendanceStatus.ABSENT: "danger",
            AttendanceStatus.LEAVE: "info",
            AttendanceStatus.HOLIDAY: "default",
            AttendanceStatus.BUSINESS_TRIP: "info",
        },
    )
    def display_status(self, instance):
        return instance.status


@admin.register(OvertimeRequest)
class OvertimeRequestAdmin(ModelAdmin, ImportExportModelAdmin):
    """Overtime request admin."""

    import_form_class = ImportForm
    export_form_class = ExportForm

    list_display = [
        "display_header",
        "display_employee",
        "display_time_range",
        "display_hours",
        "display_status",
    ]
    list_filter = [
        ("date", RangeDateFilter),
        ("status", ChoicesCheckboxFilter),
        ("employee__department", RelatedDropdownFilter),
    ]
    search_fields = [
        "employee__first_name",
        "employee__last_name",
        "reason",
    ]
    autocomplete_fields = ["employee", "approved_by"]
    readonly_fields = ["approved_at"]
    date_hierarchy = "date"

    fieldsets = [
        (
            _("Request Information"),
            {
                "fields": [
                    "employee",
                    "date",
                    ("planned_start", "planned_end"),
                    "reason",
                ]
            },
        ),
        (
            _("Status"),
            {
                "fields": [
                    "status",
                    ("approved_by", "approved_at"),
                    "rejection_reason",
                ]
            },
        ),
        (
            _("Actual Hours"),
            {
                "fields": [
                    ("planned_hours", "actual_hours"),
                ]
            },
        ),
    ]

    actions_row = ["approve_request", "reject_request"]

    @display(description=_("Date"), header=True)
    def display_header(self, instance):
        return [
            str(instance.date),
            instance.get_status_display(),
            str(instance.date.day),
            None,
        ]

    @display(description=_("Employee"))
    def display_employee(self, instance):
        return instance.employee.full_name

    @display(description=_("Time"))
    def display_time_range(self, instance):
        return f"{instance.planned_start.strftime('%H:%M')} - {instance.planned_end.strftime('%H:%M')}"

    @display(description=_("Hours"))
    def display_hours(self, instance):
        return f"{instance.planned_hours:.1f}h"

    @display(
        description=_("Status"),
        label={
            OvertimeRequestStatus.PENDING: "warning",
            OvertimeRequestStatus.APPROVED: "success",
            OvertimeRequestStatus.REJECTED: "danger",
            OvertimeRequestStatus.COMPLETED: "info",
            OvertimeRequestStatus.CANCELLED: "default",
        },
    )
    def display_status(self, instance):
        return instance.status

    @action(description=_("Approve"))
    def approve_request(self, request, object_id):
        obj = OvertimeRequest.objects.get(pk=object_id)
        if obj.status == OvertimeRequestStatus.PENDING:
            obj.status = OvertimeRequestStatus.APPROVED
            if hasattr(request.user, "employee"):
                obj.approved_by = request.user.employee
            obj.approved_at = timezone.now()
            obj.save()

    @action(description=_("Reject"))
    def reject_request(self, request, object_id):
        obj = OvertimeRequest.objects.get(pk=object_id)
        if obj.status == OvertimeRequestStatus.PENDING:
            obj.status = OvertimeRequestStatus.REJECTED
            obj.save()


@admin.register(Holiday)
class HolidayAdmin(ModelAdmin, ImportExportModelAdmin):
    """Holiday admin."""

    import_form_class = ImportForm
    export_form_class = ExportForm

    list_display = [
        "display_header",
        "date",
        "display_is_paid",
        "display_is_national",
        "is_substitute",
    ]
    list_filter = ["is_paid", "is_national", "is_substitute", ("date", RangeDateFilter)]
    search_fields = ["name"]
    date_hierarchy = "date"

    fieldsets = [
        (
            _("Holiday Information"),
            {
                "fields": [
                    "name",
                    "date",
                    "description",
                ]
            },
        ),
        (
            _("Settings"),
            {
                "fields": [
                    ("is_paid", "is_national", "is_substitute"),
                ]
            },
        ),
    ]

    @display(description=_("Holiday"), header=True)
    def display_header(self, instance):
        return [
            instance.name,
            instance.date.strftime("%Y-%m-%d"),
            instance.name[0],
            None,
        ]

    @display(
        description=_("Paid"),
        label={True: "success", False: "danger"},
    )
    def display_is_paid(self, instance):
        return instance.is_paid

    @display(
        description=_("National"),
        label={True: "info", False: "default"},
    )
    def display_is_national(self, instance):
        return instance.is_national
