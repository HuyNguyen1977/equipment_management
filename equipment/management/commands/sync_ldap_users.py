"""
Management command để sync tất cả users từ LDAP lên Django database
Usage: python manage.py sync_ldap_users
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User
from ldap3 import Server, Connection, ALL, SUBTREE
import logging

logger = logging.getLogger('equipment')


class Command(BaseCommand):
    help = 'Sync tất cả users từ LDAP lên Django database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Chỉ hiển thị kết quả, không tạo/cập nhật users',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Giới hạn số lượng users để sync (để test)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options.get('limit')
        
        # Cấu hình LDAP
        ldap_server = getattr(settings, 'LDAP_SERVER', '192.168.104.80')
        ldap_domain = getattr(settings, 'LDAP_DOMAIN', 'pegaholdings.local')
        ldap_base_dn = getattr(settings, 'LDAP_BASE_DN', 'DC=pegaholdings,DC=local')
        ldap_search_dn = getattr(settings, 'LDAP_SEARCH_DN', f'CN=Users,{ldap_base_dn}')
        ldap_port = getattr(settings, 'LDAP_PORT', 389)
        ldap_use_ssl = getattr(settings, 'LDAP_USE_SSL', False)
        
        # Service account để search
        service_dn = getattr(settings, 'LDAP_SERVICE_DN', None)
        service_password = getattr(settings, 'LDAP_SERVICE_PASSWORD', None)
        
        self.stdout.write(f'Syncing users from LDAP...')
        self.stdout.write(f'LDAP Server: {ldap_server}:{ldap_port}')
        self.stdout.write(f'Search DN: {ldap_search_dn}')
        self.stdout.write(f'Dry run: {dry_run}')
        self.stdout.write('')
        
        try:
            # Tạo LDAP server
            server = Server(
                ldap_server,
                port=ldap_port,
                use_ssl=ldap_use_ssl,
                get_info=ALL
            )
            
            # Kết nối LDAP
            # Có thể dùng service account, user account, hoặc anonymous
            conn = None
            
            if service_dn and service_password:
                self.stdout.write(f'Connecting with service account: {service_dn}')
                try:
                    conn = Connection(server, service_dn, service_password, auto_bind=True)
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'Service account failed: {str(e)}'))
            
            # Nếu service account không hoạt động, thử dùng một user account để search
            if not conn:
                # Có thể cấu hình một user account để search
                search_user = getattr(settings, 'LDAP_SEARCH_USER', None)
                search_user_password = getattr(settings, 'LDAP_SEARCH_USER_PASSWORD', None)
                
                if search_user and search_user_password:
                    user_dn = f'{search_user}@{ldap_domain}'
                    self.stdout.write(f'Connecting with user account: {search_user}')
                    try:
                        conn = Connection(server, user_dn, search_user_password, auto_bind=True)
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'User account failed: {str(e)}'))
            
            # Nếu vẫn không có, thử anonymous
            if not conn:
                self.stdout.write('Connecting with anonymous bind...')
                try:
                    conn = Connection(server, auto_bind=True)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Failed to connect: {str(e)}'))
                    self.stdout.write('')
                    self.stdout.write('Please configure one of the following:')
                    self.stdout.write('  1. LDAP_SERVICE_DN and LDAP_SERVICE_PASSWORD (recommended)')
                    self.stdout.write('  2. LDAP_SEARCH_USER and LDAP_SEARCH_USER_PASSWORD')
                    self.stdout.write('')
                    self.stdout.write('Example in settings.py:')
                    self.stdout.write('  LDAP_SEARCH_USER = "p.huy.nn"')
                    self.stdout.write('  LDAP_SEARCH_USER_PASSWORD = "Pega@2025"')
                    return
            
            # Search filter - lấy tất cả users
            # Thử nhiều filter khác nhau
            search_filters = [
                '(&(objectClass=user)(objectCategory=person))',  # Filter đơn giản
                '(objectClass=user)',  # Filter cơ bản nhất
                '(sAMAccountName=*)',  # Tất cả có sAMAccountName
            ]
            
            search_attrs = ['sAMAccountName', 'displayName', 'mail', 'givenName', 'sn', 'distinguishedName', 'userPrincipalName']
            
            # Thử search ở base DN trước, nếu không có thì thử search DN
            search_dns = [ldap_base_dn, ldap_search_dn]
            
            entries = None
            used_filter = None
            used_dn = None
            
            for search_dn in search_dns:
                for search_filter in search_filters:
                    self.stdout.write(f'Trying search in {search_dn} with filter: {search_filter}...')
                    try:
                        conn.search(
                            search_dn,
                            search_filter,
                            SUBTREE,
                            attributes=search_attrs
                        )
                        
                        if conn.entries:
                            entries = conn.entries
                            used_filter = search_filter
                            used_dn = search_dn
                            self.stdout.write(self.style.SUCCESS(f'Found {len(entries)} entries!'))
                            break
                    except Exception as e:
                        self.stdout.write(f'  Error: {str(e)}')
                        continue
                
                if entries:
                    break
            
            if not conn.entries:
                self.stdout.write(self.style.WARNING('No users found in LDAP'))
                conn.unbind()
                return
            
            total_users = len(conn.entries)
            self.stdout.write(f'Found {total_users} users in LDAP')
            self.stdout.write('')
            
            # Giới hạn nếu có
            entries = conn.entries[:limit] if limit else conn.entries
            
            # Sync users
            created_count = 0
            updated_count = 0
            skipped_count = 0
            error_count = 0
            
            for entry in entries:
                try:
                    # Lấy thông tin user
                    username = str(entry.sAMAccountName) if hasattr(entry, 'sAMAccountName') and entry.sAMAccountName else None
                    
                    if not username:
                        skipped_count += 1
                        continue
                    
                    display_name = str(entry.displayName) if hasattr(entry, 'displayName') and entry.displayName else ''
                    email = str(entry.mail) if hasattr(entry, 'mail') and entry.mail else ''
                    first_name = str(entry.givenName) if hasattr(entry, 'givenName') and entry.givenName else ''
                    last_name = str(entry.sn) if hasattr(entry, 'sn') and entry.sn else ''
                    
                    # Nếu không có email, dùng userPrincipalName hoặc tạo từ username
                    if not email:
                        if hasattr(entry, 'userPrincipalName') and entry.userPrincipalName:
                            email = str(entry.userPrincipalName)
                        else:
                            email = f'{username}@{ldap_domain}'
                    
                    if dry_run:
                        # Chỉ hiển thị
                        try:
                            existing_user = User.objects.get(username=username)
                            self.stdout.write(f'  [UPDATE] {username} - {display_name or email} (existing)')
                            updated_count += 1
                        except User.DoesNotExist:
                            self.stdout.write(f'  [CREATE] {username} - {display_name or email} (new)')
                            created_count += 1
                    else:
                        # Tạo hoặc cập nhật user
                        try:
                            user = User.objects.get(username=username)
                            # Cập nhật thông tin
                            updated = False
                            if email and user.email != email:
                                user.email = email
                                updated = True
                            if first_name and user.first_name != first_name:
                                user.first_name = first_name
                                updated = True
                            if last_name and user.last_name != last_name:
                                user.last_name = last_name
                                updated = True
                            
                            if updated:
                                user.save()
                                self.stdout.write(f'  [UPDATE] {username} - {display_name or email}')
                                updated_count += 1
                            else:
                                skipped_count += 1
                        except User.DoesNotExist:
                            # Tạo user mới
                            user = User.objects.create_user(
                                username=username,
                                email=email,
                                first_name=first_name,
                                last_name=last_name,
                            )
                            # Set unusable password (chỉ xác thực qua LDAP)
                            user.set_unusable_password()
                            user.save()
                            self.stdout.write(f'  [CREATE] {username} - {display_name or email}')
                            created_count += 1
                            
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  [ERROR] {username if username else "unknown"}: {str(e)}'))
                    error_count += 1
                    logger.error(f"Error syncing user {username}: {str(e)}")
            
            # Đóng connection
            conn.unbind()
            
            # Tổng kết
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 50))
            self.stdout.write(self.style.SUCCESS('Sync Summary:'))
            self.stdout.write(f'  Total users in LDAP: {total_users}')
            self.stdout.write(f'  Processed: {len(entries)}')
            if limit:
                self.stdout.write(f'  (Limited to {limit} users)')
            self.stdout.write(f'  Created: {created_count}')
            self.stdout.write(f'  Updated: {updated_count}')
            self.stdout.write(f'  Skipped: {skipped_count}')
            self.stdout.write(f'  Errors: {error_count}')
            
            if dry_run:
                self.stdout.write(self.style.WARNING('  (DRY RUN - No changes made)'))
            else:
                self.stdout.write(self.style.SUCCESS('  Sync completed!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            logger.error(f"LDAP sync error: {str(e)}")

