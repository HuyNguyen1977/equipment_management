"""
Management command để test LDAP connection
Usage: python manage.py test_ldap --username testuser --password testpass
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from equipment.ldap_backend import LDAPBackend
from django.contrib.auth.models import User
import sys


class Command(BaseCommand):
    help = 'Test LDAP authentication'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='LDAP username to test',
            required=True
        )
        parser.add_argument(
            '--password',
            type=str,
            help='LDAP password to test',
            required=True
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        
        self.stdout.write(f'Testing LDAP authentication for user: {username}')
        self.stdout.write(f'LDAP Server: {settings.LDAP_SERVER}')
        self.stdout.write(f'LDAP Domain: {settings.LDAP_DOMAIN}')
        self.stdout.write('')
        
        # Test authentication
        backend = LDAPBackend()
        user = backend.authenticate(None, username=username, password=password)
        
        if user:
            self.stdout.write(self.style.SUCCESS('Authentication successful!'))
            self.stdout.write(f'  User ID: {user.id}')
            self.stdout.write(f'  Username: {user.username}')
            self.stdout.write(f'  Email: {user.email}')
            self.stdout.write(f'  Full Name: {user.get_full_name()}')
            self.stdout.write(f'  Is Staff: {user.is_staff}')
            self.stdout.write(f'  Is Superuser: {user.is_superuser}')
        else:
            self.stdout.write(self.style.ERROR('Authentication failed!'))
            self.stdout.write('  Please check:')
            self.stdout.write('  1. Username and password are correct')
            self.stdout.write('  2. LDAP server is accessible')
            self.stdout.write('  3. LDAP configuration in settings.py is correct')

