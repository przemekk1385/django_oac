"""
Django settings for project project.

Generated by 'django-admin startproject' using Django 3.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

import os
from pathlib import Path
from typing import Callable, Union

from django.core.exceptions import ImproperlyConfigured
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


def _bool(value):
    if value not in ("0", "1", "False", "True", "false", "true"):
        raise ValueError(f"cannot map {value} to bool")
    return True if value in ("1", "True", "true") else False


def load_env_var(name, map_to: Callable = str, default: Union[bool, str] = None):
    var = os.environ.get(name)
    if var:
        try:
            return map_to(var)
        except ValueError:
            raise ImproperlyConfigured(f"cannot map {var} to {map_to}")
    elif default is not None:
        return default
    raise ImproperlyConfigured(f"undefined required variable '{name}'")


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = load_env_var("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = load_env_var("DEBUG", _bool, default=False)

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "sslserver",
    "django_oac",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_oac.middleware.OAuthClientMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "django_oac.backends.OAuthClientBackend",
]

ROOT_URLCONF = "project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "project.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(BASE_DIR / "db.sqlite3"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
        ),
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = "/static/"


# OAuth Client settings
# https://github.com/przemekk1385/django_oac

OAC = {
    "authorize_uri": "https://your.oauth.provider/authorize/",
    "token_uri": "https://your.oauth.provider/token/",
    "revoke_uri": "https://your.oauth.provider/revoke/",
    "redirect_uri": "http://your.site/oac/callback/",
    "jwks_uri": "https://your.oauth.provider/jwks/",
    "client_id": load_env_var("OAC_CLIENT_ID"),
    "client_secret": load_env_var("OAC_CLIENT_SECRET"),
    # "scope": "openid",
}
