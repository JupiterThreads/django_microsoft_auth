import logging

from django.contrib.sites.models import Site
from django.core.signing import dumps
from django.middleware.csrf import get_token
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .client import MicrosoftClient
from .conf import LOGIN_TYPE_XBL, config
from .utils import get_scheme

logger = logging.getLogger("django")


def microsoft(request):
    """Adds global template variables for microsoft_auth"""
    login_type = None
    if config.MICROSOFT_AUTH_LOGIN_TYPE == LOGIN_TYPE_XBL:
        login_type = _("Xbox Live")
    else:
        login_type = _("Microsoft")

    if config.DEBUG:  # pragma: no branch
        try:
            current_domain = Site.objects.get_current(request).domain
        except Site.DoesNotExist:
            logger.warning(
                "\nWARNING:\nThe domain configured for the sites framework "
                "does not match the domain you are accessing Django with. "
                "Microsoft authentication may not work.\n"
            )
        else:
            do_warning = get_scheme(
                request
            ) == "http" and not current_domain.startswith("localhost")
            if do_warning:  # pragma: no branch
                logger.warning(
                    "\nWARNING:\nYou are not using HTTPS. Microsoft "
                    "authentication only works over HTTPS unless the hostname "
                    "for your `redirect_uri` is `localhost`\n"
                )

    # Initialize Microsoft client using dict with CSRF token and optional
    # next path as state variable
    if config.MICROSOFT_AUTH_LOGIN_ENABLED:
        next_ = request.GET.get("next")
        state = {"token": get_token(request)}
        if next_:
            state["next"] = next_
        signed_state = dumps(state, salt="microsoft_auth")
        microsoft = MicrosoftClient(state=signed_state, request=request)
        auth_url = microsoft.authorization_url()[0]
        return {
            "microsoft_login_enabled": config.MICROSOFT_AUTH_LOGIN_ENABLED,
            "microsoft_authorization_url": mark_safe(auth_url),  # nosec
            "microsoft_login_type_text": login_type,
        }
    return {
        "microsoft_login_enabled": config.MICROSOFT_AUTH_LOGIN_ENABLED,
    }
