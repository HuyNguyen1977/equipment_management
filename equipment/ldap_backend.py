"""
LDAP Authentication Backend cho Pegaholdings
LDAP Server: 192.168.104.80
Domain: pegaholdings.local
Sử dụng ldap3 library (pure Python, dễ cài đặt hơn python-ldap)
"""
from ldap3 import Server, Connection, ALL, SUBTREE
from django.contrib.auth.models import User
from django.contrib.auth.backends import BaseBackend
from django.conf import settings
import logging

logger = logging.getLogger('equipment')


class LDAPBackend(BaseBackend):
    """
    LDAP Authentication Backend
    Sử dụng LDAP để xác thực user, tự động tạo Django User nếu chưa có
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Xác thực user qua LDAP
        """
        if username is None or password is None:
            return None
        
        # Cấu hình LDAP
        ldap_server = getattr(settings, 'LDAP_SERVER', '192.168.104.80')
        ldap_domain = getattr(settings, 'LDAP_DOMAIN', 'pegaholdings.local')
        ldap_base_dn = getattr(settings, 'LDAP_BASE_DN', 'DC=pegaholdings,DC=local')
        ldap_search_dn = getattr(settings, 'LDAP_SEARCH_DN', f'CN=Users,{ldap_base_dn}')
        ldap_port = getattr(settings, 'LDAP_PORT', 389)
        ldap_use_ssl = getattr(settings, 'LDAP_USE_SSL', False)
        
        try:
            # Tạo LDAP server
            server = Server(
                ldap_server,
                port=ldap_port,
                use_ssl=ldap_use_ssl,
                get_info=ALL
            )
            
            # Tìm user trong LDAP
            search_filter = f'(sAMAccountName={username})'
            search_attrs = ['sAMAccountName', 'displayName', 'mail', 'givenName', 'sn', 'memberOf', 'distinguishedName']
            
            # Service account để search (nếu có)
            service_dn = getattr(settings, 'LDAP_SERVICE_DN', None)
            service_password = getattr(settings, 'LDAP_SERVICE_PASSWORD', None)
            
            # Tạo connection để search
            if service_dn and service_password:
                # Dùng service account
                search_conn = Connection(
                    server,
                    service_dn,
                    service_password,
                    auto_bind=True
                )
            else:
                # Thử anonymous bind hoặc bind trực tiếp với user
                # Format user DN: username@domain hoặc CN=username,CN=Users,DC=...
                user_dn_format1 = f'{username}@{ldap_domain}'
                user_dn_format2 = f'CN={username},{ldap_search_dn}'
                
                # Thử bind trực tiếp với user để xác thực
                try:
                    # Thử format 1: username@domain
                    test_conn = Connection(server, user_dn_format1, password, auto_bind=True)
                    test_conn.unbind()
                    logger.info(f"LDAP: User {username} authenticated successfully (format: {user_dn_format1})")
                    
                    # Lấy thông tin user (cần search với service account hoặc anonymous)
                    user_info = self._get_user_info(server, ldap_search_dn, search_filter, search_attrs, service_dn, service_password)
                    
                    return self._get_or_create_user(username, user_info.get('email', ''), 
                                                   user_info.get('first_name', ''), 
                                                   user_info.get('last_name', ''), 
                                                   user_info.get('display_name', ''))
                except Exception as e1:
                    logger.debug(f"LDAP: Format 1 failed, trying format 2: {str(e1)}")
                    try:
                        # Thử format 2: CN=username,CN=Users,DC=...
                        test_conn = Connection(server, user_dn_format2, password, auto_bind=True)
                        test_conn.unbind()
                        logger.info(f"LDAP: User {username} authenticated successfully (format: {user_dn_format2})")
                        
                        # Lấy thông tin user
                        user_info = self._get_user_info(server, ldap_search_dn, search_filter, search_attrs, service_dn, service_password)
                        
                        return self._get_or_create_user(username, user_info.get('email', ''), 
                                                       user_info.get('first_name', ''), 
                                                       user_info.get('last_name', ''), 
                                                       user_info.get('display_name', ''))
                    except Exception as e2:
                        logger.warning(f"LDAP: Authentication failed for {username}: {str(e2)}")
                        return None
            
            # Nếu có service account, search user
            search_conn.search(
                ldap_search_dn,
                search_filter,
                SUBTREE,
                attributes=search_attrs
            )
            
            if not search_conn.entries:
                logger.warning(f"LDAP: User {username} not found")
                search_conn.unbind()
                return None
            
            # Lấy thông tin user
            entry = search_conn.entries[0]
            user_dn = str(entry.distinguishedName) if hasattr(entry, 'distinguishedName') and entry.distinguishedName else f'CN={username},{ldap_search_dn}'
            display_name = str(entry.displayName) if hasattr(entry, 'displayName') and entry.displayName else ''
            email = str(entry.mail) if hasattr(entry, 'mail') and entry.mail else ''
            first_name = str(entry.givenName) if hasattr(entry, 'givenName') and entry.givenName else ''
            last_name = str(entry.sn) if hasattr(entry, 'sn') and entry.sn else ''
            
            # Đóng search connection
            search_conn.unbind()
            
            # Thử bind với user DN và password để xác thực
            try:
                auth_conn = Connection(server, user_dn, password, auto_bind=True)
                auth_conn.unbind()
                logger.info(f"LDAP: User {username} authenticated successfully")
            except Exception as e:
                logger.warning(f"LDAP: Invalid credentials for user {username}: {str(e)}")
                return None
            
            # Tìm hoặc tạo Django User
            return self._get_or_create_user(username, email, first_name, last_name, display_name)
                
        except Exception as e:
            logger.error(f"LDAP: Unexpected error authenticating {username}: {str(e)}")
            return None
    
    def _get_user_info(self, server, search_dn, search_filter, search_attrs, service_dn=None, service_password=None):
        """
        Lấy thông tin user từ LDAP (nếu có service account)
        """
        user_info = {
            'email': '',
            'first_name': '',
            'last_name': '',
            'display_name': ''
        }
        
        try:
            if service_dn and service_password:
                conn = Connection(server, service_dn, service_password, auto_bind=True)
            else:
                # Thử anonymous
                conn = Connection(server, auto_bind=True)
            
            conn.search(search_dn, search_filter, SUBTREE, attributes=search_attrs)
            
            if conn.entries:
                entry = conn.entries[0]
                user_info['display_name'] = str(entry.displayName) if hasattr(entry, 'displayName') and entry.displayName else ''
                user_info['email'] = str(entry.mail) if hasattr(entry, 'mail') and entry.mail else ''
                user_info['first_name'] = str(entry.givenName) if hasattr(entry, 'givenName') and entry.givenName else ''
                user_info['last_name'] = str(entry.sn) if hasattr(entry, 'sn') and entry.sn else ''
            
            conn.unbind()
        except Exception as e:
            logger.debug(f"LDAP: Could not get user info: {str(e)}")
        
        return user_info
    
    def _get_or_create_user(self, username, email, first_name, last_name, display_name):
        """
        Tìm hoặc tạo Django User
        """
        try:
            user = User.objects.get(username=username)
            # Cập nhật thông tin từ LDAP
            updated = False
            if email and not user.email:
                user.email = email
                updated = True
            if first_name and not user.first_name:
                user.first_name = first_name
                updated = True
            if last_name and not user.last_name:
                user.last_name = last_name
                updated = True
            if updated:
                user.save()
        except User.DoesNotExist:
            # Tạo user mới
            user = User.objects.create_user(
                username=username,
                email=email if email else f'{username}@pegaholdings.local',
                first_name=first_name,
                last_name=last_name,
            )
            # Set password ngẫu nhiên (không dùng password LDAP)
            user.set_unusable_password()
            user.save()
            logger.info(f"LDAP: Created new Django user {username}")
        
        return user
    
    def get_user(self, user_id):
        """
        Lấy user từ database
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
