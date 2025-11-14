"""
Management command để export SQLite database ra file SQL dump
"""
import os
import sys
import subprocess
from django.core.management.base import BaseCommand
from django.conf import settings

# Fix encoding cho Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class Command(BaseCommand):
    help = 'Export SQLite database ra file SQL dump'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default=None,
            help='Đường dẫn file output (mặc định: db_dump_YYYYMMDD_HHMMSS.sql)',
        )

    def handle(self, *args, **options):
        db_path = settings.DATABASES['default']['NAME']
        
        # Kiểm tra xem database có tồn tại không
        if not os.path.exists(db_path):
            self.stdout.write(
                self.style.ERROR(f'Database không tồn tại: {db_path}')
            )
            return
        
        # Tạo tên file output nếu không được chỉ định
        if options['output']:
            output_file = options['output']
        else:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'db_dump_{timestamp}.sql'
        
        self.stdout.write(f'Đang export database từ: {db_path}')
        self.stdout.write(f'Đến file: {output_file}')
        
        try:
            # Sử dụng sqlite3 command để export
            # sqlite3 db.sqlite3 .dump > output.sql
            with open(output_file, 'w', encoding='utf-8') as f:
                result = subprocess.run(
                    ['sqlite3', str(db_path), '.dump'],
                    stdout=f,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8'
                )
            
            if result.returncode == 0:
                file_size = os.path.getsize(output_file)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n✓ Export thành công!\n'
                        f'File: {output_file}\n'
                        f'Kích thước: {file_size:,} bytes'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'Lỗi khi export: {result.stderr}'
                    )
                )
                
        except FileNotFoundError:
            # Nếu không có sqlite3 command, sử dụng Python để export
            self.stdout.write('Không tìm thấy sqlite3 command, sử dụng Python để export...')
            self.export_with_python(db_path, output_file)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Lỗi: {str(e)}')
            )

    def export_with_python(self, db_path, output_file):
        """Export database sử dụng Python sqlite3 module"""
        import sqlite3
        from datetime import datetime
        
        try:
            conn = sqlite3.connect(str(db_path))
            conn.text_factory = str  # Đảm bảo UTF-8
            
            with open(output_file, 'w', encoding='utf-8') as f:
                # Ghi header
                f.write(f'-- SQLite database dump\n')
                f.write(f'-- Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
                f.write(f'-- Source: {db_path}\n\n')
                f.write('BEGIN TRANSACTION;\n\n')
                
                # Dump schema và data
                for line in conn.iterdump():
                    f.write(f'{line}\n')
                
                f.write('\nCOMMIT;\n')
            
            conn.close()
            
            file_size = os.path.getsize(output_file)
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Export thành công!\n'
                    f'File: {output_file}\n'
                    f'Kích thước: {file_size:,} bytes'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Lỗi khi export với Python: {str(e)}')
            )

