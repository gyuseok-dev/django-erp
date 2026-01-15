from django.utils.translation import gettext_lazy as _


def dashboard_callback(request, context):
    """Dashboard callback for Unfold admin."""
    context.update(
        {
            "navigation": [
                {
                    "title": _("Quick Stats"),
                    "items": [
                        {
                            "title": _("Total Employees"),
                            "description": _("Active employees in the system"),
                            "value": _get_employee_count(),
                            "icon": "people",
                        },
                        {
                            "title": _("Pending Leave Requests"),
                            "description": _("Requests awaiting approval"),
                            "value": _get_pending_leave_count(),
                            "icon": "pending_actions",
                        },
                        {
                            "title": _("This Month Payroll"),
                            "description": _("Total payroll amount"),
                            "value": _get_current_payroll_total(),
                            "icon": "payments",
                        },
                    ],
                },
            ],
        }
    )
    return context


def _get_employee_count():
    """Get active employee count."""
    try:
        from employees.models import Employee

        return Employee.objects.filter(status="ACTIVE").count()
    except Exception:
        return 0


def _get_pending_leave_count():
    """Get pending leave request count."""
    try:
        from leave.models import LeaveRequest

        return LeaveRequest.objects.filter(state="PENDING").count()
    except Exception:
        return 0


def _get_current_payroll_total():
    """Get current month payroll total."""
    try:
        from datetime import date

        from payroll.models import PayrollPeriod

        today = date.today()
        period = PayrollPeriod.objects.filter(
            year=today.year, month=today.month
        ).first()
        if period:
            return f"{period.payslip_set.aggregate(total=Sum('net_salary'))['total']:,.0f}"
        return "0"
    except Exception:
        return "0"
