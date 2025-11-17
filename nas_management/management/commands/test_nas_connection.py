"""
Management command để test kết nối NAS
"""
from django.core.management.base import BaseCommand
from nas_management.models import NASConfig
from nas_management.synology_api import SynologyAPIClient, SynologyAPIError


class Command(BaseCommand):
    help = 'Test kết nối đến NAS Synology'

    def add_arguments(self, parser):
        parser.add_argument(
            '--nas-id',
            type=int,
            help='ID của NAS config để test (nếu không có sẽ test tất cả)',
        )

    def handle(self, *args, **options):
        nas_id = options.get('nas_id')
        
        if nas_id:
            nas_configs = NASConfig.objects.filter(id=nas_id, is_active=True)
        else:
            nas_configs = NASConfig.objects.filter(is_active=True)
        
        if not nas_configs.exists():
            self.stdout.write(self.style.ERROR('Không tìm thấy NAS config nào!'))
            return
        
        for nas in nas_configs:
            self.stdout.write(f'\n=== Testing NAS: {nas.name} ===')
            self.stdout.write(f'Host: {nas.host}')
            self.stdout.write(f'Port: {nas.port}')
            self.stdout.write(f'HTTPS: {nas.use_https}')
            self.stdout.write(f'API URL: {nas.get_api_url()}')
            
            try:
                with SynologyAPIClient(nas) as client:
                    self.stdout.write(self.style.SUCCESS('✓ Kết nối thành công!'))
                    
                    # Test get system info
                    try:
                        system_info = client.get_system_info()
                        self.stdout.write(f'✓ System info: {system_info.get("model", "Unknown")}')
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'⚠ Không thể lấy system info: {str(e)}'))
                    
            except SynologyAPIError as e:
                self.stdout.write(self.style.ERROR(f'✗ Lỗi: {str(e)}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Lỗi không xác định: {str(e)}'))


Management command để test kết nối NAS
"""
from django.core.management.base import BaseCommand
from nas_management.models import NASConfig
from nas_management.synology_api import SynologyAPIClient, SynologyAPIError


class Command(BaseCommand):
    help = 'Test kết nối đến NAS Synology'

    def add_arguments(self, parser):
        parser.add_argument(
            '--nas-id',
            type=int,
            help='ID của NAS config để test (nếu không có sẽ test tất cả)',
        )

    def handle(self, *args, **options):
        nas_id = options.get('nas_id')
        
        if nas_id:
            nas_configs = NASConfig.objects.filter(id=nas_id, is_active=True)
        else:
            nas_configs = NASConfig.objects.filter(is_active=True)
        
        if not nas_configs.exists():
            self.stdout.write(self.style.ERROR('Không tìm thấy NAS config nào!'))
            return
        
        for nas in nas_configs:
            self.stdout.write(f'\n=== Testing NAS: {nas.name} ===')
            self.stdout.write(f'Host: {nas.host}')
            self.stdout.write(f'Port: {nas.port}')
            self.stdout.write(f'HTTPS: {nas.use_https}')
            self.stdout.write(f'API URL: {nas.get_api_url()}')
            
            try:
                with SynologyAPIClient(nas) as client:
                    self.stdout.write(self.style.SUCCESS('✓ Kết nối thành công!'))
                    
                    # Test get system info
                    try:
                        system_info = client.get_system_info()
                        self.stdout.write(f'✓ System info: {system_info.get("model", "Unknown")}')
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'⚠ Không thể lấy system info: {str(e)}'))
                    
            except SynologyAPIError as e:
                self.stdout.write(self.style.ERROR(f'✗ Lỗi: {str(e)}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Lỗi không xác định: {str(e)}'))

