"""
Management command to verify users, especially wallet users.
"""
from django.core.management.base import BaseCommand
from apps.authentication.models import User, UserProfile


class Command(BaseCommand):
    help = 'Verify users, especially those with wallet addresses'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Verify all users with wallet addresses',
        )
        parser.add_argument(
            '--user-id',
            type=str,
            help='Verify specific user by ID',
        )
        parser.add_argument(
            '--wallet',
            type=str,
            help='Verify user by wallet address',
        )

    def handle(self, *args, **options):
        if options['all']:
            self.verify_all_wallet_users()
        elif options['user_id']:
            self.verify_user_by_id(options['user_id'])
        elif options['wallet']:
            self.verify_user_by_wallet(options['wallet'])
        else:
            self.stdout.write('Please specify --all, --user-id, or --wallet')

    def verify_all_wallet_users(self):
        """Verify all users with wallet addresses."""
        profiles = UserProfile.objects.filter(
            wallet_address__isnull=False,
            verification_status__in=['pending', 'rejected']
        )
        
        count = 0
        for profile in profiles:
            profile.verification_status = 'verified'
            profile.save()
            count += 1
            self.stdout.write(f'✓ Verified user: {profile.user.email} ({profile.wallet_address})')
        
        self.stdout.write(
            self.style.SUCCESS(f'Verified {count} wallet users')
        )

    def verify_user_by_id(self, user_id):
        """Verify specific user by ID."""
        try:
            user = User.objects.get(id=user_id)
            user.profile.verification_status = 'verified'
            user.profile.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Verified user: {user.email} (ID: {user_id})'
                )
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with ID {user_id} not found')
            )

    def verify_user_by_wallet(self, wallet_address):
        """Verify user by wallet address."""
        try:
            profile = UserProfile.objects.get(wallet_address__iexact=wallet_address)
            profile.verification_status = 'verified'
            profile.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Verified user: {profile.user.email} ({wallet_address})'
                )
            )
        except UserProfile.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with wallet {wallet_address} not found')
            )
