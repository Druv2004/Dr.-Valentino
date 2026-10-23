from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("publications/", views.publications, name="publications"),
    path("presentations/", views.presentations, name="presentations"),
    path("projects/", views.projects, name="projects"),
    path("organizations/", views.organizations, name="organizations"),
    path("resources/", views.resources, name="resources"),
    path("contact/", views.contact, name="contact"),
    path("contact/thanks/", views.contact_thanks, name="contact_thanks"),
]
