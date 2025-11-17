"""
Management command để test lấy logs từ NAS
"""
import sys
import codecs
from django.core.management.base import BaseCommand
from nas_management.models import NASConfig
from nas_management.synology_api import SynologyAPIClient, SynologyAPIError
import json

# Fix encoding cho Windows
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class Command(BaseCommand):
    help = 'Test lấy logs từ NAS Synology'

    def add_arguments(self, parser):
        parser.add_argument(
            '--nas-id',
            type=int,
            help='ID của NAS config để test',
        )

    def handle(self, *args, **options):
        nas_id = options.get('nas_id')
        
        if nas_id:
            nas_configs = NASConfig.objects.filter(id=nas_id, is_active=True)
        else:
            nas_configs = NASConfig.objects.filter(is_active=True)
        
        if not nas_configs.exists():
            self.stdout.write(self.style.ERROR('Khong tim thay NAS config nao!'))
            return
        
        for nas in nas_configs:
            self.stdout.write(f'\n=== Testing Logs API for NAS: {nas.name} ===')
            self.stdout.write(f'Host: {nas.host}:{nas.port}')
            
            try:
                with SynologyAPIClient(nas) as client:
                    self.stdout.write(self.style.SUCCESS('[OK] Dang nhap thanh cong!'))
                    
                    # Kiểm tra API có sẵn
                    self.stdout.write('\n--- Checking available APIs ---')
                    all_apis = client.list_all_apis()
                    log_apis = [api for api in all_apis.keys() if 'log' in api.lower() or 'event' in api.lower()]
                    if log_apis:
                        self.stdout.write(f'Tim thay {len(log_apis)} API lien quan den log:')
                        for api in log_apis[:10]:
                            api_info = all_apis.get(api, {})
                            max_ver = api_info.get('maxVersion', '?')
                            self.stdout.write(f'  - {api} (max version: {max_ver})')
                    else:
                        self.stdout.write(self.style.WARNING('Khong tim thay API log nao'))
                    
                    # Kiểm tra SYNO.Core.EventLog cụ thể
                    eventlog_info = client.get_api_info('SYNO.Core.EventLog')
                    if eventlog_info:
                        self.stdout.write(self.style.SUCCESS(f'\n[OK] SYNO.Core.EventLog co san (max version: {eventlog_info.get("maxVersion", "?")})'))
                    else:
                        self.stdout.write(self.style.WARNING('\n[WARNING] SYNO.Core.EventLog KHONG co san'))
                    
                    # Test get logs
                    self.stdout.write('\n--- Testing get_logs() ---')
                    logs = client.get_logs(limit=10)
                    
                    if logs:
                        self.stdout.write(self.style.SUCCESS(f'[OK] Tim thay {len(logs)} logs!'))
                        self.stdout.write('\nMau log dau tien:')
                        if len(logs) > 0:
                            sample = logs[0]
                            self.stdout.write(json.dumps(sample, indent=2, ensure_ascii=False))
                        
                        # Debug: Thử gọi trực tiếp API để xem raw response
                        self.stdout.write('\n--- Debug: Raw API Response ---')
                        try:
                            all_apis = client.list_all_apis()
                            
                            # Test SYNO.AI.Statistics.Admin.Log
                            if 'SYNO.AI.Statistics.Admin.Log' in all_apis:
                                api_info = all_apis.get('SYNO.AI.Statistics.Admin.Log', {})
                                max_ver = str(api_info.get('maxVersion', '1'))
                                api_path = api_info.get('path', 'entry.cgi')
                                
                                params = {
                                    'api': 'SYNO.AI.Statistics.Admin.Log',
                                    'version': max_ver,
                                    'method': 'list',
                                    'limit': 5,
                                    'offset': 0
                                }
                                raw_data = client._request(api_path, 'GET', params)
                                self.stdout.write('Raw response from SYNO.AI.Statistics.Admin.Log:')
                                self.stdout.write(json.dumps(raw_data, indent=2, ensure_ascii=False))
                            
                            # Test SYNO.AI.Statistics.Request.Log
                            if 'SYNO.AI.Statistics.Request.Log' in all_apis:
                                api_info = all_apis.get('SYNO.AI.Statistics.Request.Log', {})
                                max_ver = str(api_info.get('maxVersion', '1'))
                                api_path = api_info.get('path', 'entry.cgi')
                                
                                params = {
                                    'api': 'SYNO.AI.Statistics.Request.Log',
                                    'version': max_ver,
                                    'method': 'list',
                                    'limit': 5,
                                    'offset': 0
                                }
                                raw_data = client._request(api_path, 'GET', params)
                                self.stdout.write('\nRaw response from SYNO.AI.Statistics.Request.Log:')
                                self.stdout.write(json.dumps(raw_data, indent=2, ensure_ascii=False))
                        except Exception as e:
                            self.stdout.write(f'Could not get raw response: {str(e)}')
                            import traceback
                            self.stdout.write(traceback.format_exc())
                    else:
                        self.stdout.write(self.style.WARNING('[WARNING] Khong tim thay log nao'))
                        self.stdout.write('\nCo the:')
                        self.stdout.write('1. Log Center package chua duoc cai dat')
                        self.stdout.write('2. NAS khong co log nao')
                        self.stdout.write('3. User khong co quyen truy cap logs')
                        self.stdout.write('4. API khong kha dung tren phien ban DSM nay')
                        self.stdout.write('\nVui long:')
                        self.stdout.write('- Kiem tra Log Center trong Package Center cua NAS')
                        self.stdout.write('- Dam bao Log Center da duoc cai dat va kich hoat')
                        self.stdout.write('- Kiem tra quyen cua user trong Log Center')
                    
            except SynologyAPIError as e:
                self.stdout.write(self.style.ERROR(f'[ERROR] Loi API: {str(e)}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'[ERROR] Loi: {str(e)}'))
                import traceback
                self.stdout.write(traceback.format_exc())

