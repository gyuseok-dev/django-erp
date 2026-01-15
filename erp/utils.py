from django.utils.translation import gettext_lazy as _


def environment_callback(request):
    """Return environment indicator for Unfold admin."""
    from django.conf import settings

    if settings.DEBUG:
        return [_("Development"), "warning"]
    return [_("Production"), "success"]
