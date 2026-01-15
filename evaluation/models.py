from decimal import Decimal

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition
from simple_history.models import HistoricalRecords

from core.models import AuditedModel


class EvaluationTemplate(AuditedModel):
    """Evaluation template model."""

    name = models.CharField(_("Template name"), max_length=200)
    description = models.TextField(_("Description"), blank=True)

    # Applicable targets
    applicable_grades = models.ManyToManyField(
        "organization.JobGrade",
        related_name="evaluation_templates",
        verbose_name=_("Applicable grades"),
        blank=True,
    )
    applicable_departments = models.ManyToManyField(
        "organization.Department",
        related_name="evaluation_templates",
        verbose_name=_("Applicable departments"),
        blank=True,
    )

    # Weights
    self_weight = models.DecimalField(
        _("Self-evaluation weight"),
        max_digits=5,
        decimal_places=2,
        default=Decimal("20.00"),
        help_text=_("Percentage weight (e.g., 20.00 for 20%)"),
    )
    peer_weight = models.DecimalField(
        _("Peer evaluation weight"),
        max_digits=5,
        decimal_places=2,
        default=Decimal("30.00"),
        help_text=_("Percentage weight (e.g., 30.00 for 30%)"),
    )
    manager_weight = models.DecimalField(
        _("Manager evaluation weight"),
        max_digits=5,
        decimal_places=2,
        default=Decimal("50.00"),
        help_text=_("Percentage weight (e.g., 50.00 for 50%)"),
    )

    is_active = models.BooleanField(_("Active"), default=True)
    version = models.CharField(_("Version"), max_length=20, default="v1.0")

    class Meta:
        verbose_name = _("Evaluation Template")
        verbose_name_plural = _("Evaluation Templates")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.version})"

    def clean(self):
        """Validate that weights sum to 100%."""
        total_weight = self.self_weight + self.peer_weight + self.manager_weight
        if total_weight != Decimal("100.00"):
            from django.core.exceptions import ValidationError

            raise ValidationError(
                _("Weights must sum to 100% (current: {}%)").format(total_weight)
            )


class EvaluationCategory(AuditedModel):
    """Evaluation category model (e.g., Competency, Performance, Attitude)."""

    template = models.ForeignKey(
        EvaluationTemplate,
        on_delete=models.CASCADE,
        related_name="categories",
        verbose_name=_("Template"),
    )
    name = models.CharField(_("Category name"), max_length=200)
    weight = models.DecimalField(
        _("Weight"),
        max_digits=5,
        decimal_places=2,
        help_text=_("Percentage weight within template"),
    )
    display_order = models.PositiveIntegerField(_("Display order"), default=0)
    description = models.TextField(_("Description"), blank=True)

    class Meta:
        verbose_name = _("Evaluation Category")
        verbose_name_plural = _("Evaluation Categories")
        ordering = ["template", "display_order"]

    def __str__(self):
        return f"{self.template.name} - {self.name}"


class ScaleType(models.TextChoices):
    """Evaluation scale type choices."""

    FIVE_POINT = "FIVE_POINT", _("5-Point Scale (1-5)")
    TEN_POINT = "TEN_POINT", _("10-Point Scale (1-10)")
    HUNDRED_POINT = "HUNDRED_POINT", _("100-Point Scale (0-100)")
    DESCRIPTIVE = "DESCRIPTIVE", _("Descriptive")


class EvaluationCriteria(AuditedModel):
    """Evaluation criteria model (detailed evaluation items)."""

    category = models.ForeignKey(
        EvaluationCategory,
        on_delete=models.CASCADE,
        related_name="criteria",
        verbose_name=_("Category"),
    )
    name = models.CharField(_("Criteria name"), max_length=200)
    description = models.TextField(_("Description"))
    weight = models.DecimalField(
        _("Weight"),
        max_digits=5,
        decimal_places=2,
        help_text=_("Percentage weight within category"),
    )
    display_order = models.PositiveIntegerField(_("Display order"), default=0)

    # Evaluation scale
    scale_type = models.CharField(
        _("Scale type"),
        max_length=20,
        choices=ScaleType.choices,
        default=ScaleType.FIVE_POINT,
    )

    # Examples
    excellent_example = models.TextField(_("Excellent example"), blank=True)
    poor_example = models.TextField(_("Poor example"), blank=True)

    class Meta:
        verbose_name = _("Evaluation Criteria")
        verbose_name_plural = _("Evaluation Criteria")
        ordering = ["category", "display_order"]

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class EvaluationPeriodStatus(models.TextChoices):
    """Evaluation period status choices."""

    DRAFT = "DRAFT", _("Draft")
    OPEN = "OPEN", _("Open")
    UNDER_REVIEW = "UNDER_REVIEW", _("Under Review")
    COMPLETED = "COMPLETED", _("Completed")
    CLOSED = "CLOSED", _("Closed")


class PeriodType(models.TextChoices):
    """Evaluation period type choices."""

    ANNUAL = "ANNUAL", _("Annual")
    SEMI_ANNUAL = "SEMI_ANNUAL", _("Semi-annual")
    QUARTERLY = "QUARTERLY", _("Quarterly")


class EvaluationPeriod(AuditedModel):
    """Evaluation period model with FSM workflow."""

    name = models.CharField(_("Period name"), max_length=200)
    year = models.PositiveIntegerField(_("Year"))
    period_type = models.CharField(
        _("Period type"),
        max_length=20,
        choices=PeriodType.choices,
        default=PeriodType.ANNUAL,
    )

    # Period dates
    start_date = models.DateField(_("Evaluation target start date"))
    end_date = models.DateField(_("Evaluation target end date"))
    evaluation_start = models.DateField(_("Evaluation input start date"))
    evaluation_end = models.DateField(_("Evaluation input end date"))

    # FSM State
    status = FSMField(
        _("Status"),
        default=EvaluationPeriodStatus.DRAFT,
        choices=EvaluationPeriodStatus.choices,
    )

    # Statistics
    total_evaluations = models.PositiveIntegerField(
        _("Total evaluations"), default=0
    )
    completed_evaluations = models.PositiveIntegerField(
        _("Completed evaluations"), default=0
    )

    description = models.TextField(_("Description"), blank=True)

    class Meta:
        verbose_name = _("Evaluation Period")
        verbose_name_plural = _("Evaluation Periods")
        ordering = ["-year", "-created_at"]

    def __str__(self):
        return f"{self.year}년 {self.get_period_type_display()} - {self.name}"

    @property
    def completion_rate(self):
        """Calculate completion rate."""
        if self.total_evaluations == 0:
            return Decimal("0")
        return (
            Decimal(str(self.completed_evaluations))
            / Decimal(str(self.total_evaluations))
            * 100
        )

    # FSM Transitions
    @transition(
        field=status,
        source=EvaluationPeriodStatus.DRAFT,
        target=EvaluationPeriodStatus.OPEN,
    )
    def open_evaluation(self):
        """Open evaluation period."""
        pass

    @transition(
        field=status,
        source=EvaluationPeriodStatus.OPEN,
        target=EvaluationPeriodStatus.UNDER_REVIEW,
    )
    def close_submission(self):
        """Close submission and start review."""
        pass

    @transition(
        field=status,
        source=EvaluationPeriodStatus.UNDER_REVIEW,
        target=EvaluationPeriodStatus.COMPLETED,
    )
    def complete(self):
        """Complete evaluation period."""
        pass

    @transition(
        field=status,
        source=EvaluationPeriodStatus.COMPLETED,
        target=EvaluationPeriodStatus.CLOSED,
    )
    def close_period(self):
        """Close evaluation period."""
        pass


class EvaluationType(models.TextChoices):
    """Evaluation type choices."""

    SELF = "SELF", _("Self-evaluation")
    PEER = "PEER", _("Peer evaluation")
    MANAGER = "MANAGER", _("Manager evaluation")
    HR = "HR", _("HR evaluation")


class EvaluationStatus(models.TextChoices):
    """Employee evaluation status choices."""

    PENDING = "PENDING", _("Pending")
    IN_PROGRESS = "IN_PROGRESS", _("In Progress")
    SUBMITTED = "SUBMITTED", _("Submitted")
    REVIEWED = "REVIEWED", _("Reviewed")


class EmployeeEvaluation(AuditedModel):
    """Employee evaluation instance model."""

    evaluation_period = models.ForeignKey(
        EvaluationPeriod,
        on_delete=models.CASCADE,
        related_name="evaluations",
        verbose_name=_("Evaluation period"),
    )
    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="evaluations",
        verbose_name=_("Employee"),
    )
    template = models.ForeignKey(
        EvaluationTemplate,
        on_delete=models.PROTECT,
        related_name="evaluations",
        verbose_name=_("Template"),
    )

    # Evaluator
    evaluator = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="conducted_evaluations",
        verbose_name=_("Evaluator"),
    )

    # Evaluation type
    evaluation_type = models.CharField(
        _("Evaluation type"),
        max_length=20,
        choices=EvaluationType.choices,
    )

    # Scores
    total_score = models.DecimalField(
        _("Total score"), max_digits=5, decimal_places=2, default=0
    )
    weighted_score = models.DecimalField(
        _("Weighted score"), max_digits=5, decimal_places=2, default=0
    )

    # Comprehensive feedback
    strengths = models.TextField(_("Strengths"), blank=True)
    weaknesses = models.TextField(_("Areas for improvement"), blank=True)
    goals = models.TextField(_("Future goals"), blank=True)
    comments = models.TextField(_("Overall comments"), blank=True)

    # Status
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=EvaluationStatus.choices,
        default=EvaluationStatus.PENDING,
    )

    submitted_at = models.DateTimeField(_("Submitted at"), null=True, blank=True)

    # History tracking
    history = HistoricalRecords()

    class Meta:
        verbose_name = _("Employee Evaluation")
        verbose_name_plural = _("Employee Evaluations")
        unique_together = ["evaluation_period", "employee", "evaluator", "evaluation_type"]
        ordering = ["-evaluation_period", "employee"]

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_evaluation_type_display()} by {self.evaluator.full_name}"

    def submit(self):
        """Submit evaluation."""
        self.status = EvaluationStatus.SUBMITTED
        self.submitted_at = timezone.now()
        self.save()


class EvaluationScore(AuditedModel):
    """Evaluation score for each criteria."""

    employee_evaluation = models.ForeignKey(
        EmployeeEvaluation,
        on_delete=models.CASCADE,
        related_name="scores",
        verbose_name=_("Employee evaluation"),
    )
    criteria = models.ForeignKey(
        EvaluationCriteria,
        on_delete=models.PROTECT,
        related_name="scores",
        verbose_name=_("Criteria"),
    )

    score = models.DecimalField(
        _("Score"), max_digits=5, decimal_places=2, default=0
    )
    comment = models.TextField(_("Comment"), blank=True)

    class Meta:
        verbose_name = _("Evaluation Score")
        verbose_name_plural = _("Evaluation Scores")
        unique_together = ["employee_evaluation", "criteria"]
        ordering = ["criteria__display_order"]

    def __str__(self):
        return f"{self.employee_evaluation.employee.full_name} - {self.criteria.name}: {self.score}"


class Grade(models.TextChoices):
    """Evaluation grade choices."""

    S = "S", _("Outstanding (95-100)")
    A = "A", _("Excellent (85-94)")
    B = "B", _("Good (70-84)")
    C = "C", _("Fair (60-69)")
    D = "D", _("Poor (<60)")


class EvaluationSummary(AuditedModel):
    """Evaluation summary model (aggregated results)."""

    evaluation_period = models.ForeignKey(
        EvaluationPeriod,
        on_delete=models.CASCADE,
        related_name="summaries",
        verbose_name=_("Evaluation period"),
    )
    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="evaluation_summaries",
        verbose_name=_("Employee"),
    )

    # Score breakdown
    self_evaluation_score = models.DecimalField(
        _("Self-evaluation score"),
        max_digits=5,
        decimal_places=2,
        default=0,
    )
    peer_evaluation_score = models.DecimalField(
        _("Peer evaluation score (average)"),
        max_digits=5,
        decimal_places=2,
        default=0,
    )
    manager_evaluation_score = models.DecimalField(
        _("Manager evaluation score"),
        max_digits=5,
        decimal_places=2,
        default=0,
    )
    final_score = models.DecimalField(
        _("Final score (weighted average)"),
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    # Grade
    grade = models.CharField(
        _("Grade"),
        max_length=1,
        choices=Grade.choices,
    )

    # Ranking
    department_rank = models.PositiveIntegerField(
        _("Department rank"), null=True, blank=True
    )
    company_rank = models.PositiveIntegerField(
        _("Company rank"), null=True, blank=True
    )

    # Comprehensive feedback
    final_feedback = models.TextField(_("Final feedback"), blank=True)
    development_plan = models.TextField(_("Development plan"), blank=True)

    # Result linkage
    salary_increase_rate = models.DecimalField(
        _("Salary increase rate"),
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text=_("Percentage (e.g., 5.00 for 5%)"),
    )
    promotion_recommended = models.BooleanField(
        _("Promotion recommended"), default=False
    )

    # Approval
    approved_by = models.ForeignKey(
        "employees.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_evaluation_summaries",
        verbose_name=_("Approved by"),
    )
    approved_at = models.DateTimeField(_("Approved at"), null=True, blank=True)

    # Employee acknowledgment
    acknowledged_by_employee = models.BooleanField(
        _("Acknowledged by employee"), default=False
    )
    acknowledged_at = models.DateTimeField(
        _("Acknowledged at"), null=True, blank=True
    )

    class Meta:
        verbose_name = _("Evaluation Summary")
        verbose_name_plural = _("Evaluation Summaries")
        unique_together = ["evaluation_period", "employee"]
        ordering = ["-evaluation_period", "-final_score"]

    def __str__(self):
        return f"{self.employee.full_name} - {self.evaluation_period.name}: {self.grade} ({self.final_score})"
