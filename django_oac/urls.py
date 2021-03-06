from django.urls import re_path

from . import views
from .apps import DjangoOACConfig

app_name = DjangoOACConfig.name
urlpatterns = [
    re_path(r"^authenticate/$", views.authenticate_view, name="authenticate"),
    re_path(r"^callback/$", views.callback_view, name="callback"),
    re_path(r"^logout/$", views.logout_view, name="logout"),
    re_path(r"^profile/$", views.profile_view, name="profile"),
]
