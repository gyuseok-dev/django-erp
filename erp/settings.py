from collections import OrderedDict
from os import environ, path
from pathlib import Path

import sentry_sdk
from django.core.management.utils import get_random_secret_key
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

######################################################################
# General
######################################################################
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = environ.get("SECRET_KEY", get_random_secret_key())

DEBUG = environ.get("DEBUG", "1") == "1"

ROOT_URLCONF = "erp.urls"

WSGI_APPLICATION = "erp.wsgi.application"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10_000

######################################################################
# Domains
######################################################################
ALLOWED_HOSTS = environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

CSRF_TRUSTED_ORIGINS = environ.get(
    "CSRF_TRUSTED_ORIGINS", "http://localhost:8000"
).split(",")

######################################################################
# Apps
######################################################################
INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.constance",
    "unfold.contrib.import_export",
    "unfold.contrib.guardian",
    "unfold.contrib.simple_history",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.humanize",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "debug_toolbar",
    "crispy_forms",
    "import_export",
    "guardian",
    "constance",
    "simple_history",
    "django_celery_beat",
    "djmoney",
    "django_filters",
    "django_fsm",
    # ERP Apps
    "core",
    "organization",
    "employees",
    "attendance",
    "leave",
    "payroll",
    "evaluation",
    "reports",
]

######################################################################
# Middleware
######################################################################
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]

######################################################################
# Sessions
######################################################################
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

######################################################################
# Templates
######################################################################
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            path.normpath(path.join(BASE_DIR, "erp/templates")),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

######################################################################
# Databases
######################################################################
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "database.sqlite",
    },
}

######################################################################
# Authentication
######################################################################
AUTH_USER_MODEL = "core.User"

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
)

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LOGIN_URL = "admin:login"

LOGIN_REDIRECT_URL = reverse_lazy("admin:index")

######################################################################
# Localization
######################################################################
LANGUAGE_CODE = "ko"

TIME_ZONE = "Asia/Seoul"

USE_I18N = True

USE_TZ = True

LANGUAGES = (
    ("ko", _("Korean")),
    ("en", _("English")),
)

DATE_INPUT_FORMATS = [
    "%Y-%m-%d",
    "%Y.%m.%d",
    "%d.%m.%Y",
    "%m/%d/%Y",
]

DATETIME_INPUT_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y.%m.%d %H:%M:%S",
    "%Y.%m.%d %H:%M",
]

######################################################################
# Static
######################################################################
STATIC_URL = "/static/"

STATICFILES_DIRS = [BASE_DIR / "erp" / "static"]

STATIC_ROOT = BASE_DIR / "static"

MEDIA_ROOT = BASE_DIR / "media"

MEDIA_URL = "/media/"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

######################################################################
# Unfold
######################################################################
UNFOLD = {
    "SITE_TITLE": _("Django ERP"),
    "SITE_HEADER": _("HR & Payroll Management"),
    "SITE_SUBHEADER": _("Enterprise Resource Planning"),
    "SITE_SYMBOL": "apartment",
    "SHOW_LANGUAGES": True,
    "ENVIRONMENT": "erp.utils.environment_callback",
    "DASHBOARD_CALLBACK": "erp.views.dashboard_callback",
    "LOGIN": {
        "image": lambda request: static("images/login-bg.jpg"),
    },
    "STYLES": [
        lambda request: static("css/styles.css"),
    ],
    "TABS": [
        {
            "models": ["employees.employee"],
            "items": [
                {
                    "title": _("Employees"),
                    "link": reverse_lazy("admin:employees_employee_changelist"),
                },
            ],
        },
        {
            "models": ["leave.leaverequest"],
            "items": [
                {
                    "title": _("Leave Requests"),
                    "link": reverse_lazy("admin:leave_leaverequest_changelist"),
                },
                {
                    "title": _("Leave Balance"),
                    "link": reverse_lazy("admin:leave_leavebalance_changelist"),
                },
            ],
        },
        {
            "models": ["payroll.payslip", "payroll.payrollperiod"],
            "items": [
                {
                    "title": _("Payslips"),
                    "link": reverse_lazy("admin:payroll_payslip_changelist"),
                },
                {
                    "title": _("Payroll Periods"),
                    "link": reverse_lazy("admin:payroll_payrollperiod_changelist"),
                },
            ],
        },
    ],
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": _("Dashboard"),
                "items": [
                    {
                        "title": _("Dashboard"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": _("Organization"),
                "collapsible": True,
                "items": [
                    {
                        "title": _("Companies"),
                        "icon": "apartment",
                        "link": reverse_lazy("admin:organization_company_changelist"),
                    },
                    {
                        "title": _("Departments"),
                        "icon": "account_tree",
                        "link": reverse_lazy("admin:organization_department_changelist"),
                    },
                    {
                        "title": _("Job Grades"),
                        "icon": "stairs",
                        "link": reverse_lazy("admin:organization_jobgrade_changelist"),
                    },
                    {
                        "title": _("Job Positions"),
                        "icon": "badge",
                        "link": reverse_lazy("admin:organization_jobposition_changelist"),
                    },
                ],
            },
            {
                "title": _("HR Management"),
                "collapsible": True,
                "items": [
                    {
                        "title": _("Employees"),
                        "icon": "people",
                        "link": reverse_lazy("admin:employees_employee_changelist"),
                    },
                    {
                        "title": _("Documents"),
                        "icon": "folder",
                        "link": reverse_lazy("admin:employees_employeedocument_changelist"),
                    },
                ],
            },
            {
                "title": _("Attendance"),
                "collapsible": True,
                "items": [
                    {
                        "title": _("Attendance Records"),
                        "icon": "schedule",
                        "link": reverse_lazy("admin:attendance_attendancerecord_changelist"),
                    },
                    {
                        "title": _("Work Schedules"),
                        "icon": "calendar_month",
                        "link": reverse_lazy("admin:attendance_workschedule_changelist"),
                    },
                    {
                        "title": _("Overtime Requests"),
                        "icon": "more_time",
                        "link": reverse_lazy("admin:attendance_overtimerequest_changelist"),
                    },
                    {
                        "title": _("Holidays"),
                        "icon": "event",
                        "link": reverse_lazy("admin:attendance_holiday_changelist"),
                    },
                ],
            },
            {
                "title": _("Leave Management"),
                "collapsible": True,
                "items": [
                    {
                        "title": _("Leave Requests"),
                        "icon": "beach_access",
                        "link": reverse_lazy("admin:leave_leaverequest_changelist"),
                        "badge": "leave.utils.pending_leave_badge",
                    },
                    {
                        "title": _("Leave Types"),
                        "icon": "category",
                        "link": reverse_lazy("admin:leave_leavetype_changelist"),
                    },
                    {
                        "title": _("Leave Balance"),
                        "icon": "account_balance",
                        "link": reverse_lazy("admin:leave_leavebalance_changelist"),
                    },
                ],
            },
            {
                "title": _("Payroll"),
                "collapsible": True,
                "items": [
                    {
                        "title": _("Payroll Periods"),
                        "icon": "date_range",
                        "link": reverse_lazy("admin:payroll_payrollperiod_changelist"),
                    },
                    {
                        "title": _("Payslips"),
                        "icon": "receipt_long",
                        "link": reverse_lazy("admin:payroll_payslip_changelist"),
                    },
                    {
                        "title": _("Allowance Types"),
                        "icon": "add_circle",
                        "link": reverse_lazy("admin:payroll_allowancetype_changelist"),
                    },
                    {
                        "title": _("Deduction Types"),
                        "icon": "remove_circle",
                        "link": reverse_lazy("admin:payroll_deductiontype_changelist"),
                    },
                ],
            },
            {
                "title": _("Evaluation"),
                "collapsible": True,
                "items": [
                    {
                        "title": _("Evaluation Periods"),
                        "icon": "event_note",
                        "link": reverse_lazy("admin:evaluation_evaluationperiod_changelist"),
                    },
                    {
                        "title": _("Employee Evaluations"),
                        "icon": "rate_review",
                        "link": reverse_lazy("admin:evaluation_employeeevaluation_changelist"),
                    },
                ],
            },
            {
                "title": _("Users & Groups"),
                "collapsible": True,
                "items": [
                    {
                        "title": _("Users"),
                        "icon": "account_circle",
                        "link": reverse_lazy("admin:core_user_changelist"),
                    },
                    {
                        "title": _("Groups"),
                        "icon": "group",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            },
            {
                "title": _("Settings"),
                "collapsible": True,
                "items": [
                    {
                        "title": _("Constance"),
                        "icon": "settings",
                        "link": reverse_lazy("admin:constance_config_changelist"),
                    },
                ],
            },
        ],
    },
}

######################################################################
# Money
######################################################################
CURRENCIES = ("KRW", "USD")
DEFAULT_CURRENCY = "KRW"

######################################################################
# Debug toolbar
######################################################################
DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG}

######################################################################
# Sentry
######################################################################
SENTRY_DSN = environ.get("SENTRY_DSN")

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        enable_tracing=False,
    )

######################################################################
# Crispy forms
######################################################################
CRISPY_TEMPLATE_PACK = "unfold_crispy"

CRISPY_ALLOWED_TEMPLATE_PACKS = ["unfold_crispy"]

######################################################################
# Constance
######################################################################
CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"

CONSTANCE_CONFIG = {
    "COMPANY_NAME": ("My Company", _("Company name")),
    "PAYROLL_CALCULATION_DAY": (25, _("Day of month for payroll calculation")),
    "ANNUAL_LEAVE_GRANT_DATE": ("01-01", _("Date for annual leave grant (MM-DD)")),
    "OVERTIME_RATE_WEEKDAY": (1.5, _("Overtime rate for weekdays")),
    "OVERTIME_RATE_HOLIDAY": (2.0, _("Overtime rate for holidays")),
    "NATIONAL_PENSION_RATE": (0.045, _("National pension rate")),
    "HEALTH_INSURANCE_RATE": (0.03545, _("Health insurance rate")),
    "LONG_TERM_CARE_RATE": (0.1295, _("Long-term care rate (% of health insurance)")),
    "EMPLOYMENT_INSURANCE_RATE": (0.009, _("Employment insurance rate")),
}

CONSTANCE_CONFIG_FIELDSETS = OrderedDict(
    {
        "General": {
            "fields": ("COMPANY_NAME",),
        },
        "Payroll Settings": {
            "fields": (
                "PAYROLL_CALCULATION_DAY",
                "OVERTIME_RATE_WEEKDAY",
                "OVERTIME_RATE_HOLIDAY",
            ),
        },
        "Leave Settings": {
            "fields": ("ANNUAL_LEAVE_GRANT_DATE",),
        },
        "Insurance Rates": {
            "fields": (
                "NATIONAL_PENSION_RATE",
                "HEALTH_INSURANCE_RATE",
                "LONG_TERM_CARE_RATE",
                "EMPLOYMENT_INSURANCE_RATE",
            ),
        },
    }
)

######################################################################
# Celery
######################################################################
CELERY_BROKER_URL = environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
