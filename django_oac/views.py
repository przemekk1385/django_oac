from logging import LoggerAdapter, getLogger
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from ipware import get_client_ip
from jwt.exceptions import PyJWTError

from .apps import DjangoOACConfig
from .exceptions import (
    ExpiredStateError,
    OACError,
    ProviderRequestError,
    ProviderResponseError,
)


def authenticate_view(request: WSGIRequest) -> HttpResponse:
    state_str = uuid4().hex
    client_ip, is_routable = get_client_ip(request)

    request.session["OAC_STATE_STR"] = request.session.get("OAC_STATE_STR") or state_str
    request.session["OAC_STATE_TIMESTAMP"] = (
        request.session.get("OAC_STATE_STR") or timezone.now().timestamp()
    )
    request.session["OAC_CLIENT_IP"] = (
        request.session.get("OAC_CLIENT_IP") or client_ip or "unknown"
    )

    logger = LoggerAdapter(
        getLogger(DjangoOACConfig.name),
        {
            "scope": "authenticate_view",
            "ip_state": (
                f"{request.session['OAC_CLIENT_IP']}"
                f":{request.session['OAC_STATE_STR']}"
            ),
        },
    )
    logger.info("authentication request")

    if not settings.OAC.get("authorize_uri"):
        logger.error("missing 'authorize_uri'")
        return render(
            request,
            "error.html",
            {"message": "App config is incomplete, cannot continue."},
            status=500,
        )
    else:
        return redirect(
            f"{settings.OAC['authorize_uri']}"
            f"?scope={settings.OAC.get('scope', 'openid')}"
            f"&client_id={settings.OAC.get('client_id', '')}"
            f"&redirect_uri={settings.OAC.get('redirect_uri', '')}"
            f"&state={state_str}"
            "&response_type=code"
        )


def callback_view(request: WSGIRequest) -> HttpResponse:
    logger = LoggerAdapter(
        getLogger(DjangoOACConfig.name),
        {
            "scope": "callback_view",
            "ip_state": (
                f"{request.session.get('OAC_CLIENT_IP', 'n/a')}"
                f":{request.session.get('OAC_STATE_STR', 'n/a')}"
            ),
        },
    )
    logger.info("callback request")

    try:
        user = authenticate(request)
    except ProviderRequestError as e:
        logger.error(f"raised ProviderRequestError: {e}")
        ret = render(request, "error.html", {"message": "Bad request."}, status=400,)
    except ExpiredStateError:
        logger.info(f"state expired")
        ret = render(
            request,
            "error.html",
            {
                "redirect": reverse("django_oac:authenticate"),
                "message": "Logging attempt took too long, try again.",
            },
            status=400,
        )
    except KeyError as e:
        logger.error(f"configuration error, missing {e}")
        ret = render(
            request,
            "error.html",
            {"message": "App config is incomplete, cannot continue."},
            status=500,
        )
    except (OACError, PyJWTError) as e:
        logger.error(f"raised {e.__class__.__name__}: {e}")
        ret = render(
            request,
            "error.html",
            {"message": "Something went wrong, cannot continue."},
            status=500,
        )
    else:
        if user:
            logger.info(f"user '{user.email}' authenticated")
            login(request, user, backend="django_oac.backends.OAuthClientBackend")
            ret = redirect("django_oac:profile")
        else:
            ret = render(request, "error.html", {"message": "Forbidden."}, status=403)

    request.session["OAC_STATE_TIMESTAMP"] = 0

    return ret


def logout_view(request: WSGIRequest) -> HttpResponse:
    logger = LoggerAdapter(
        getLogger(DjangoOACConfig.name),
        {
            "scope": "logout_view",
            "ip_state": (
                f"{request.session.get('OAC_CLIENT_IP', 'n/a')}"
                f":{request.session.get('OAC_STATE_STR', 'n/a')}"
            ),
        },
    )
    logger.info("logout request")

    token = request.user.token_set.last()

    ret = redirect("django_oac:profile")
    if token:
        try:
            token.revoke()
        except KeyError as e:
            logger.error(f"configuration error, missing {e}")
            ret = render(
                request,
                "error.html",
                {"message": "App config is incomplete, cannot continue."},
                status=500,
            )
        except ProviderResponseError as e:
            logger.error(f"raised ProviderResponseError: {e}")
            ret = render(
                request,
                "error.html",
                {"message": "Something went wrong, cannot continue."},
                status=500,
            )
        else:
            logger.info(
                f"refresh token for user '{request.user.email}' has been revoked"
            )
            token.delete()

    logout(request)
    logger.info(f"user '{request.user.email}' logged out")

    return ret


def profile_view(request: WSGIRequest) -> JsonResponse:
    return JsonResponse(
        {
            field: getattr(request.user, field, "")
            for field in ("first_name", "last_name", "email", "username")
        }
    )
