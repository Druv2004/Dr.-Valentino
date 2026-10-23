from django.urls import path
from . import dashboard as d

urlpatterns = [
    path("login/", d.login_view, name="login"),
    path("logout/", d.logout_view, name="logout"),
    path("dashboard/", d.overview, name="dashboard"),
    path("dashboard/site/", d.settings_manage, name="settings_manage"),
    path("dashboard/password/", d.password_change, name="password_change"),
    path("dashboard/messages/", d.messages_manage, name="messages_manage"),
    path("dashboard/messages/export/", d.messages_export, name="messages_export"),
    path("dashboard/messages/<int:pk>/", d.message_detail, name="message_detail"),
    path("dashboard/messages/<int:pk>/delete/", d.message_delete, name="message_delete"),
    path("dashboard/team/", d.users_manage, name="users_manage"),
    path("dashboard/team/<int:pk>/", d.user_edit, name="user_edit"),
    path("dashboard/<str:key>/", d.section_list, name="dash_list"),
    path("dashboard/<str:key>/new/", d.section_edit, name="dash_new"),
    path("dashboard/<str:key>/<int:pk>/", d.section_edit, name="dash_edit"),
    path("dashboard/<str:key>/<int:pk>/delete/", d.section_delete, name="dash_delete"),
]
