"""Create (or update) a dashboard login.

    python manage.py create_manager --username manager --password "choose-a-strong-one"
    python manage.py create_manager --username editor1 --password "..." --role editor

Roles: manager (default), editor, viewer, admin. Sign in at /login/.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from core.models import Profile


class Command(BaseCommand):
    help = "Create a Control Center login with a role."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--password", required=True)
        parser.add_argument("--email", default="")
        parser.add_argument("--role", default="manager", choices=[r for r, _ in Profile.ROLES])

    def handle(self, *args, **o):
        try:
            validate_password(o["password"])
        except ValidationError as e:
            raise CommandError(" ".join(e.messages))
        User = get_user_model()
        user, created = User.objects.get_or_create(username=o["username"], defaults={"email": o["email"]})
        user.is_active = True
        user.set_password(o["password"])
        user.save()
        Profile.objects.update_or_create(user=user, defaults={"role": o["role"]})
        self.stdout.write(self.style.SUCCESS(
            f"{'Created' if created else 'Updated'} '{user.username}' as {o['role']}. Sign in at /login/"))
