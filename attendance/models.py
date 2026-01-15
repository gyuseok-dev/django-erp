from datetime import datetime, time, timedelta

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import AuditedModel


class WorkSchedule(AuditedModel):
    """Work schedule template model."""

    name = models.CharField(_("Schedule name"), max_length=100)
    start_time = models.TimeField(_("Start time"), default=time(9, 0))
    end_time = models.TimeField(_("End time"), default=time(18, 0))
    break_start = models.TimeField(_("Break start"), default=time(12, 0))
    break_end = models.TimeField(_("Break end"), default=time(13, 0))
    is_default = models.BooleanField(_("Default schedule"), default=False)
    description = models.TextField(_("Description"), blank=True)

    class Meta:
        verbose_name = _("Work Schedule")
        verbose_name_plural = _("Work Schedules")
        ordering = ["-is_default", "name"]

    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"

    @property
    def work_hours(self):
        """Calculate total work hours excluding break."""
        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)
        break_start = datetime.combine(datetime.today(), self.break_start)
        break_end = datetime.combine(datetime.today(), self.break_end)

        total = (end - start).seconds / 3600
        break_time = (break_end - break_start).seconds / 3600

        return total - break_time

    def save(self, *args, **kwargs):
        if self.is_default:
            WorkSchedule.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class AttendanceStatus(models.TextChoices):
    """Attendance status choices."""

    PRESENT = "PRESENT", _("Present")
    LATE = "LATE", _("Late")
    EARLY_LEAVE = "EARLY_LEAVE", _("Early Leave")
    ABSENT = "ABSENT", _("Absent")
    LEAVE = "LEAVE", _("On Leave")
    HOLIDAY = "HOLIDAY", _("Holiday")
    BUSINESS_TRIP = "BUSINESS_TRIP", _("Business Trip")


class AttendanceRecord(AuditedModel):
    """Daily attendance record model."""

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="attendance_records",
        verbose_name=_("Employee"),
    )
    date = models.DateField(_("Date"))
    schedule = models.ForeignKey(
        WorkSchedule,
        on_delete=models.PROTECT,
        related_name="attendance_records",
        verbose_name=_("Schedule"),
    )

    # Actual work time
    check_in = models.DateTimeField(_("Check in"), null=True, blank=True)
    check_out = models.DateTimeField(_("Check out"), null=True, blank=True)

    # Status
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PRESENT,
    )

    # Calculated values
    work_hours = models.DecimalField(
        _("Work hours"), max_digits=5, decimal_places=2, default=0
    )
    overtime_hours = models.DecimalField(
        _("Overtime hours"), max_digits=5, decimal_places=2, default=0
    )
    late_minutes = models.PositiveIntegerField(_("Late minutes"), default=0)
    early_leave_minutes = models.PositiveIntegerField(
        _("Early leave minutes"), default=0
    )

    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Attendance Record")
        verbose_name_plural = _("Attendance Records")
        unique_together = ["employee", "date"]
        ordering = ["-date", "employee"]

    def __str__(self):
        return f"{self.employee.full_name} - {self.date}"

    def calculate_attendance(self):
        """Calculate work hours and status based on check-in/out times."""
        if not self.check_in or not self.check_out:
            return

        # Calculate work hours
        work_duration = self.check_out - self.check_in
        self.work_hours = work_duration.seconds / 3600

        # Check for late arrival
        scheduled_start = datetime.combine(self.date, self.schedule.start_time)
        if self.check_in > scheduled_start:
            late_delta = self.check_in - scheduled_start
            self.late_minutes = late_delta.seconds // 60
            self.status = AttendanceStatus.LATE

        # Check for early leave
        scheduled_end = datetime.combine(self.date, self.schedule.end_time)
        if self.check_out < scheduled_end:
            early_delta = scheduled_end - self.check_out
            self.early_leave_minutes = early_delta.seconds // 60
            if self.status != AttendanceStatus.LATE:
                self.status = AttendanceStatus.EARLY_LEAVE

        # Calculate overtime (work after scheduled end time)
        if self.check_out > scheduled_end:
            overtime_delta = self.check_out - scheduled_end
            self.overtime_hours = overtime_delta.seconds / 3600

        # Set present if no issues
        if self.late_minutes == 0 and self.early_leave_minutes == 0:
            self.status = AttendanceStatus.PRESENT


class OvertimeRequestStatus(models.TextChoices):
    """Overtime request status choices."""

    PENDING = "PENDING", _("Pending")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    COMPLETED = "COMPLETED", _("Completed")
    CANCELLED = "CANCELLED", _("Cancelled")


class OvertimeRequest(AuditedModel):
    """Overtime work request model."""

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="overtime_requests",
        verbose_name=_("Employee"),
    )
    date = models.DateField(_("Date"))
    planned_start = models.TimeField(_("Planned start time"))
    planned_end = models.TimeField(_("Planned end time"))
    planned_hours = models.DecimalField(
        _("Planned hours"), max_digits=4, decimal_places=2
    )
    actual_hours = models.DecimalField(
        _("Actual hours"), max_digits=4, decimal_places=2, null=True, blank=True
    )
    reason = models.TextField(_("Reason"))

    # Approval workflow
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=OvertimeRequestStatus.choices,
        default=OvertimeRequestStatus.PENDING,
    )
    approved_by = models.ForeignKey(
        "employees.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_overtimes",
        verbose_name=_("Approved by"),
    )
    approved_at = models.DateTimeField(_("Approved at"), null=True, blank=True)
    rejection_reason = models.TextField(_("Rejection reason"), blank=True)

    class Meta:
        verbose_name = _("Overtime Request")
        verbose_name_plural = _("Overtime Requests")
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.employee.full_name} - {self.date} ({self.planned_hours}h)"

    def save(self, *args, **kwargs):
        # Calculate planned hours
        if self.planned_start and self.planned_end:
            start = datetime.combine(datetime.today(), self.planned_start)
            end = datetime.combine(datetime.today(), self.planned_end)
            if end < start:  # Overnight
                end += timedelta(days=1)
            self.planned_hours = (end - start).seconds / 3600
        super().save(*args, **kwargs)


class Holiday(AuditedModel):
    """Holiday/Off day model."""

    name = models.CharField(_("Holiday name"), max_length=100)
    date = models.DateField(_("Date"), unique=True)
    is_paid = models.BooleanField(_("Paid holiday"), default=True)
    is_national = models.BooleanField(_("National holiday"), default=True)
    is_substitute = models.BooleanField(_("Substitute holiday"), default=False)
    description = models.TextField(_("Description"), blank=True)

    class Meta:
        verbose_name = _("Holiday")
        verbose_name_plural = _("Holidays")
        ordering = ["date"]

    def __str__(self):
        return f"{self.name} ({self.date})"
