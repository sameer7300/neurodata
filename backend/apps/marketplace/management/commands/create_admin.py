"""
Management command to create admin users for dispute validation.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Create admin user for dispute validation'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Admin username', default='admin')
        parser.add_argument('--email', type=str, help='Admin email', default='admin@neurodata.com')
        parser.add_argument('--password', type=str, help='Admin password', default='admin123')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        try:
            with transaction.atomic():
                if User.objects.filter(username=username).exists():
                    self.stdout.write(
                        self.style.WARNING(f'Admin user "{username}" already exists')
                    )
                    return

                admin_user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    is_staff=True,
                    is_superuser=True
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created admin user "{username}" for dispute validation'
                    )
                )
                self.stdout.write(f'Email: {email}')
                self.stdout.write(f'Password: {password}')
                self.stdout.write(
                    self.style.WARNING(
                        'Please change the password after first login!'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating admin user: {str(e)}')
            )
