from decimal import Decimal

from django.db.models import Count, Q, Sum

from attendance.models import AttendanceRecord, AttendanceStatus
from employees.models import Employee, EmployeeStatus
from leave.models import LeaveRequest, LeaveRequestState
from payroll.models import (
    AllowanceType,
    DeductionType,
    Payslip,
    PayslipAllowance,
    PayslipDeduction,
    PayrollPeriod,
    PayslipStatus,
    SalaryContract,
)


class PayrollCalculator:
    """Payroll calculation engine."""

    def __init__(self, payroll_period: PayrollPeriod):
        self.period = payroll_period

    def calculate_for_employee(self, employee: Employee) -> Payslip:
        """Calculate payroll for a single employee."""

        # 1. Gather work data
        work_data = self._gather_work_data(employee)

        # 2. Calculate base salary
        base_salary = self._calculate_base_salary(employee, work_data)

        # 3. Calculate allowances
        allowances = self._calculate_allowances(employee, work_data)
        total_allowances = sum(a["amount"] for a in allowances.values())

        # 4. Calculate overtime pay
        overtime_pay = self._calculate_overtime_pay(employee, work_data)

        # 5. Calculate gross salary
        gross_salary = base_salary + total_allowances + overtime_pay

        # 6. Calculate deductions
        deductions = self._calculate_deductions(employee, gross_salary)
        total_deductions = sum(d["amount"] for d in deductions.values())

        # 7. Calculate net salary
        net_salary = gross_salary - total_deductions

        # 8. Create or update Payslip
        payslip, created = Payslip.objects.update_or_create(
            payroll_period=self.period,
            employee=employee,
            defaults={
                # Work information
                "work_days": work_data["work_days"],
                "paid_leave_days": work_data["paid_leave_days"],
                "unpaid_leave_days": work_data["unpaid_leave_days"],
                "overtime_hours": work_data["overtime_hours"],
                "night_hours": work_data["night_hours"],
                "holiday_hours": work_data["holiday_hours"],
                # Salary components
                "base_salary": base_salary,
                "total_allowances": total_allowances,
                "overtime_pay": overtime_pay,
                "gross_salary": gross_salary,
                # Deductions
                "income_tax": deductions["INCOME_TAX"]["amount"],
                "resident_tax": deductions["RESIDENT_TAX"]["amount"],
                "national_pension": deductions["PENSION"]["amount"],
                "health_insurance": deductions["HEALTH"]["amount"],
                "long_term_care": deductions["LONG_TERM_CARE"]["amount"],
                "employment_insurance": deductions["EMPLOYMENT"]["amount"],
                "total_deductions": total_deductions,
                # Net salary
                "net_salary": net_salary,
                "status": PayslipStatus.CALCULATED,
            },
        )

        # 9. Save allowance details
        self._save_allowance_details(payslip, allowances)

        # 10. Save deduction details
        self._save_deduction_details(payslip, deductions)

        return payslip

    def _gather_work_data(self, employee):
        """Gather work data from Attendance and Leave apps."""
        # Get attendance records for the period
        attendance_records = AttendanceRecord.objects.filter(
            employee=employee,
            date__range=[self.period.start_date, self.period.end_date],
        )

        # Calculate work days (present + late + early leave)
        work_days = attendance_records.filter(
            status__in=[
                AttendanceStatus.PRESENT,
                AttendanceStatus.LATE,
                AttendanceStatus.EARLY_LEAVE,
            ]
        ).count()

        # Calculate paid leave days
        paid_leave_days = attendance_records.filter(
            status=AttendanceStatus.LEAVE
        ).count()

        # Calculate unpaid leave days
        unpaid_leave_requests = LeaveRequest.objects.filter(
            employee=employee,
            state=LeaveRequestState.APPROVED,
            leave_type__is_paid=False,
            start_date__lte=self.period.end_date,
            end_date__gte=self.period.start_date,
        )
        unpaid_leave_days = sum(
            float(lr.total_days) for lr in unpaid_leave_requests
        )

        # Calculate overtime, night, and holiday hours
        overtime_hours = (
            attendance_records.aggregate(total=Sum("overtime_hours"))["total"] or 0
        )
        night_hours = 0  # Would be calculated from night shift records
        holiday_hours = 0  # Would be calculated from holiday work records

        return {
            "work_days": Decimal(str(work_days)),
            "paid_leave_days": Decimal(str(paid_leave_days)),
            "unpaid_leave_days": Decimal(str(unpaid_leave_days)),
            "overtime_hours": Decimal(str(overtime_hours)),
            "night_hours": Decimal(str(night_hours)),
            "holiday_hours": Decimal(str(holiday_hours)),
        }

    def _calculate_base_salary(self, employee, work_data):
        """Calculate base salary (with deduction for unpaid leave)."""
        # Get active salary contract
        contract = (
            SalaryContract.objects.filter(
                employee=employee,
                is_active=True,
                effective_date__lte=self.period.end_date,
            )
            .order_by("-effective_date")
            .first()
        )

        if not contract:
            return Decimal("0")

        monthly_base = contract.monthly_base_salary

        # Deduct for unpaid leave days
        if work_data["unpaid_leave_days"] > 0:
            # Assume 30 days per month
            daily_rate = monthly_base / 30
            deduction = daily_rate * work_data["unpaid_leave_days"]
            return monthly_base - deduction

        return monthly_base

    def _calculate_allowances(self, employee, work_data):
        """Calculate allowances."""
        allowances = {}

        # Get active allowance types
        allowance_types = AllowanceType.objects.filter(is_active=True)

        for allowance_type in allowance_types:
            if allowance_type.code == "POSITION":
                # Position allowance from JobPosition
                if employee.job_position and employee.job_position.allowance:
                    allowances[allowance_type.code] = {
                        "type": allowance_type,
                        "amount": employee.job_position.allowance,
                        "quantity": Decimal("1"),
                        "rate": Decimal("0"),
                    }
            elif allowance_type.code in ["OVERTIME", "NIGHT", "HOLIDAY"]:
                # Skip overtime-related allowances here (handled separately)
                continue
            elif allowance_type.calculation_type == "FIXED":
                # Fixed allowances (meal, transport, etc.)
                allowances[allowance_type.code] = {
                    "type": allowance_type,
                    "amount": allowance_type.default_amount,
                    "quantity": Decimal("1"),
                    "rate": Decimal("0"),
                }

        return allowances

    def _calculate_overtime_pay(self, employee, work_data):
        """Calculate overtime pay."""
        if work_data["overtime_hours"] <= 0:
            return Decimal("0")

        # Get base monthly salary
        contract = (
            SalaryContract.objects.filter(
                employee=employee,
                is_active=True,
                effective_date__lte=self.period.end_date,
            )
            .order_by("-effective_date")
            .first()
        )

        if not contract:
            return Decimal("0")

        # Calculate hourly rate (209 hours = monthly standard work hours in Korea)
        hourly_rate = contract.monthly_base_salary / 209

        # Overtime rate: 1.5x for weekday overtime
        overtime_rate = Decimal("1.5")
        overtime_pay = hourly_rate * overtime_rate * work_data["overtime_hours"]

        return overtime_pay

    def _calculate_deductions(self, employee, gross_salary):
        """Calculate deductions (4대보험 and taxes)."""
        deductions = {}

        # Get active deduction types
        deduction_types = DeductionType.objects.filter(is_active=True, is_statutory=True)

        for deduction_type in deduction_types:
            if deduction_type.code == "PENSION":
                # National Pension (4.5%)
                amount = gross_salary * Decimal(str(deduction_type.default_rate))
                # Apply max limit
                if deduction_type.max_amount and amount > deduction_type.max_amount:
                    amount = deduction_type.max_amount
                deductions["PENSION"] = {
                    "type": deduction_type,
                    "amount": amount,
                    "base_amount": gross_salary,
                    "rate": deduction_type.default_rate,
                }

            elif deduction_type.code == "HEALTH":
                # Health Insurance (3.545%)
                amount = gross_salary * Decimal(str(deduction_type.default_rate))
                deductions["HEALTH"] = {
                    "type": deduction_type,
                    "amount": amount,
                    "base_amount": gross_salary,
                    "rate": deduction_type.default_rate,
                }

            elif deduction_type.code == "LONG_TERM_CARE":
                # Long-term Care Insurance (12.95% of health insurance)
                if "HEALTH" in deductions:
                    health_amount = deductions["HEALTH"]["amount"]
                    amount = health_amount * Decimal(str(deduction_type.default_rate))
                    deductions["LONG_TERM_CARE"] = {
                        "type": deduction_type,
                        "amount": amount,
                        "base_amount": health_amount,
                        "rate": deduction_type.default_rate,
                    }

            elif deduction_type.code == "EMPLOYMENT":
                # Employment Insurance (0.9%)
                amount = gross_salary * Decimal(str(deduction_type.default_rate))
                deductions["EMPLOYMENT"] = {
                    "type": deduction_type,
                    "amount": amount,
                    "base_amount": gross_salary,
                    "rate": deduction_type.default_rate,
                }

            elif deduction_type.code == "INCOME_TAX":
                # Income Tax (simplified calculation)
                amount = self._calculate_income_tax(gross_salary)
                deductions["INCOME_TAX"] = {
                    "type": deduction_type,
                    "amount": amount,
                    "base_amount": gross_salary,
                    "rate": Decimal("0"),
                }

            elif deduction_type.code == "RESIDENT_TAX":
                # Resident Tax (10% of income tax)
                if "INCOME_TAX" in deductions:
                    income_tax = deductions["INCOME_TAX"]["amount"]
                    amount = income_tax * Decimal(str(deduction_type.default_rate))
                    deductions["RESIDENT_TAX"] = {
                        "type": deduction_type,
                        "amount": amount,
                        "base_amount": income_tax,
                        "rate": deduction_type.default_rate,
                    }

        return deductions

    def _calculate_income_tax(self, gross_salary):
        """
        Calculate income tax using simplified brackets.
        This is a simplified version - in production, use official tax tables.
        """
        # Simplified progressive tax rates (2024)
        if gross_salary <= 1_500_000:
            return gross_salary * Decimal("0.06")
        elif gross_salary <= 4_500_000:
            return Decimal("90000") + (gross_salary - 1_500_000) * Decimal("0.15")
        elif gross_salary <= 8_800_000:
            return Decimal("540000") + (gross_salary - 4_500_000) * Decimal("0.24")
        else:
            return Decimal("1572000") + (gross_salary - 8_800_000) * Decimal("0.35")

    def _save_allowance_details(self, payslip, allowances):
        """Save allowance details to PayslipAllowance."""
        # Delete existing allowances
        PayslipAllowance.objects.filter(payslip=payslip).delete()

        # Create new allowances
        for code, data in allowances.items():
            PayslipAllowance.objects.create(
                payslip=payslip,
                allowance_type=data["type"],
                amount=data["amount"],
                quantity=data["quantity"],
                rate=data["rate"],
                calculation_note=f"{data['type'].name} calculation",
            )

    def _save_deduction_details(self, payslip, deductions):
        """Save deduction details to PayslipDeduction."""
        # Delete existing deductions
        PayslipDeduction.objects.filter(payslip=payslip).delete()

        # Create new deductions
        for code, data in deductions.items():
            PayslipDeduction.objects.create(
                payslip=payslip,
                deduction_type=data["type"],
                amount=data["amount"],
                base_amount=data["base_amount"],
                rate=data["rate"],
                calculation_note=f"{data['type'].name} calculation",
            )

    def calculate_all_employees(self):
        """Calculate payroll for all active employees."""
        employees = Employee.objects.filter(status=EmployeeStatus.ACTIVE)

        payslips = []
        for employee in employees:
            try:
                payslip = self.calculate_for_employee(employee)
                payslips.append(payslip)
            except Exception as e:
                # Log error but continue with other employees
                print(f"Error calculating payroll for {employee}: {e}")
                continue

        # Update period statistics
        self._update_period_statistics()

        return payslips

    def _update_period_statistics(self):
        """Update payroll period statistics."""
        aggregates = Payslip.objects.filter(payroll_period=self.period).aggregate(
            total_gross=Sum("gross_salary"),
            total_deductions=Sum("total_deductions"),
            total_net=Sum("net_salary"),
            count=Count("id"),
        )

        self.period.total_gross = aggregates["total_gross"] or 0
        self.period.total_deductions = aggregates["total_deductions"] or 0
        self.period.total_net = aggregates["total_net"] or 0
        self.period.employee_count = aggregates["count"] or 0
        self.period.save()
