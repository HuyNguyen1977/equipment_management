from django.core.management.base import BaseCommand
from renewals.models import RenewalType


class Command(BaseCommand):
    help = 'Initialize renewal types (Email, Server, Domain, Applications)'

    def handle(self, *args, **options):
        renewal_types = [
            {'name': 'Email', 'description': 'Dịch vụ email (Gmail, Outlook, Exchange...)', 'order': 1},
            {'name': 'Server', 'description': 'Máy chủ và hosting (AWS, Azure, VPS...)', 'order': 2},
            {'name': 'Domain', 'description': 'Tên miền và SSL', 'order': 3},
            {'name': 'Ứng dụng', 'description': 'Các ứng dụng và phần mềm công ty', 'order': 4},
            {'name': 'Cloud Storage', 'description': 'Lưu trữ đám mây (Google Drive, Dropbox...)', 'order': 5},
            {'name': 'Khác', 'description': 'Các dịch vụ khác', 'order': 99},
        ]
        
        created_count = 0
        updated_count = 0
        
        for rt_data in renewal_types:
            renewal_type, created = RenewalType.objects.get_or_create(
                name=rt_data['name'],
                defaults={
                    'description': rt_data['description'],
                    'order': rt_data['order']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS('Created: ' + renewal_type.name)
                )
            else:
                # Update order if it's 0
                if renewal_type.order == 0:
                    renewal_type.order = rt_data['order']
                    renewal_type.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING('Updated order for: ' + renewal_type.name)
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                '\nCompleted! Created: {}, Updated: {}'.format(created_count, updated_count)
            )
        )

