from django.core.management.base import BaseCommand
from equipment.models import Company
import sys


class Command(BaseCommand):
    help = 'Tao 3 cong ty mac dinh: Saigonbooks, Zenbooks, Pegaholdings'

    def handle(self, *args, **options):
        companies = [
            {'name': 'Saigonbooks', 'code': 'SGB'},
            {'name': 'Zenbooks', 'code': 'ZNB'},
            {'name': 'Pegaholdings', 'code': 'PEG'},
        ]
        
        for company_data in companies:
            company, created = Company.objects.get_or_create(
                code=company_data['code'],
                defaults={'name': company_data['name']}
            )
            if created:
                msg = f'Created company: {company.name}'
                self.stdout.write(self.style.SUCCESS(msg))
            else:
                msg = f'Company {company.name} already exists'
                self.stdout.write(self.style.WARNING(msg))

