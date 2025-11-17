"""
Synology DSM API Client
Tài liệu: https://global.download.synology.com/download/Document/Software/DeveloperGuide/Package/FileStation/All/enu/Synology_File_Station_API_Guide.pdf
"""
import requests
import json
import os
from typing import Dict, List, Optional, Any
from django.utils import timezone
from .models import NASConfig


class SynologyAPIError(Exception):
    """Lỗi khi gọi Synology API"""
    pass


class SynologyAPIClient:
    """Client để giao tiếp với Synology DSM API"""
    
    def __init__(self, nas_config: NASConfig):
        self.nas_config = nas_config
        self.base_url = nas_config.get_api_url()
        self.session = requests.Session()
        self.session.verify = False  # Tắt SSL verification cho development
        self.sid = None  # Session ID
        
    def _request(self, api: str, method: str, params: Dict = None) -> Dict:
        """Gửi request đến Synology API"""
        if params is None:
            params = {}
        
        # Thêm SID nếu đã đăng nhập
        if self.sid:
            params['_sid'] = self.sid
        
        url = f"{self.base_url}/webapi/{api}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, timeout=30)
            else:
                response = self.session.post(url, data=params, timeout=30)
            
            response.raise_for_status()
            
            # Kiểm tra content-type
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' not in content_type:
                # Nếu không phải JSON, có thể là lỗi HTML
                raise SynologyAPIError(f"Unexpected response type: {content_type}. URL: {url}")
            
            try:
                data = response.json()
            except ValueError:
                raise SynologyAPIError(f"Invalid JSON response. Response: {response.text[:200]}")
            
            if not data.get('success', False):
                error_code = data.get('error', {}).get('code', 0)
                error_msg = data.get('error', {}).get('errors', data.get('error', {}).get('message', 'Unknown error'))
                raise SynologyAPIError(f"API Error {error_code}: {error_msg}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            raise SynologyAPIError(f"Request failed: {str(e)}. URL: {url}")
    
    def login(self) -> bool:
        """Đăng nhập vào NAS"""
        try:
            # Kiểm tra API info trước
            info_params = {
                'api': 'SYNO.API.Info',
                'version': '1',
                'method': 'query',
                'query': 'SYNO.API.Auth'
            }
            
            # Thử lấy API info (không bắt buộc)
            try:
                self._request('query.cgi', 'GET', info_params)
            except:
                pass  # Bỏ qua nếu không có API info
            
            # Đăng nhập với session FileStation (cho file operations)
            params = {
                'api': 'SYNO.API.Auth',
                'version': '3',
                'method': 'login',
                'account': self.nas_config.username,
                'passwd': self.nas_config.password,
                'session': 'FileStation',
                'format': 'sid'
            }
            
            data = self._request('auth.cgi', 'GET', params)
            self.sid = data.get('data', {}).get('sid')
            
            # Nếu cần logs, thử đăng nhập với session khác
            # Thử với session 'SYNO.Core.EventLog' nếu có
            return self.sid is not None
            
        except Exception as e:
            raise SynologyAPIError(f"Login failed: {str(e)}")
    
    def logout(self):
        """Đăng xuất khỏi NAS"""
        if self.sid:
            try:
                # Thử logout với các session khác nhau
                sessions = ['FileStation', 'SYNO.Core.EventLog']
                for session in sessions:
                    try:
                        params = {
                            'api': 'SYNO.API.Auth',
                            'version': '1',
                            'method': 'logout',
                            'session': session
                        }
                        self._request('auth.cgi', 'GET', params)
                    except:
                        pass
            except:
                pass
            finally:
                self.sid = None
    
    def get_system_info(self) -> Dict:
        """Lấy thông tin hệ thống"""
        try:
            params = {
                'api': 'SYNO.Core.System',
                'version': '1',
                'method': 'info'
            }
            data = self._request('entry.cgi', 'GET', params)
            return data.get('data', {})
        except Exception as e:
            raise SynologyAPIError(f"Failed to get system info: {str(e)}")
    
    def get_cpu_info(self) -> Dict:
        """Lấy thông tin CPU"""
        try:
            params = {
                'api': 'SYNO.Core.System.Utilization',
                'version': '1',
                'method': 'get'
            }
            data = self._request('entry.cgi', 'GET', params)
            return data.get('data', {})
        except Exception as e:
            raise SynologyAPIError(f"Failed to get CPU info: {str(e)}")
    
    def get_memory_info(self) -> Dict:
        """Lấy thông tin Memory"""
        try:
            params = {
                'api': 'SYNO.Core.System.Utilization',
                'version': '1',
                'method': 'get'
            }
            data = self._request('entry.cgi', 'GET', params)
            return data.get('data', {}).get('memory', {})
        except Exception as e:
            raise SynologyAPIError(f"Failed to get memory info: {str(e)}")
    
    def get_disk_info(self) -> List[Dict]:
        """Lấy thông tin Disk"""
        try:
            params = {
                'api': 'SYNO.Storage.CGI.Storage',
                'version': '1',
                'method': 'load_info'
            }
            data = self._request('entry.cgi', 'GET', params)
            return data.get('data', {}).get('disks', [])
        except Exception as e:
            raise SynologyAPIError(f"Failed to get disk info: {str(e)}")
    
    def get_login_history(self, limit: int = 100) -> List[Dict]:
        """Lấy lịch sử đăng nhập"""
        try:
            params = {
                'api': 'SYNO.Core.SecurityAudit.Log',
                'version': '1',
                'method': 'list',
                'limit': limit,
                'type': 'login'
            }
            data = self._request('entry.cgi', 'GET', params)
            return data.get('data', {}).get('logs', [])
        except Exception as e:
            # Nếu API không khả dụng, trả về danh sách rỗng
            return []
    
    def get_api_info(self, api_name: str) -> Dict:
        """Lấy thông tin về API"""
        try:
            params = {
                'api': 'SYNO.API.Info',
                'version': '1',
                'method': 'query',
                'query': api_name
            }
            data = self._request('query.cgi', 'GET', params)
            return data.get('data', {}).get(api_name, {})
        except:
            return {}
    
    def list_all_apis(self) -> Dict:
        """Lấy danh sách tất cả API có sẵn"""
        try:
            params = {
                'api': 'SYNO.API.Info',
                'version': '1',
                'method': 'query',
                'query': 'all'
            }
            data = self._request('query.cgi', 'GET', params)
            return data.get('data', {})
        except:
            return {}
    
    def get_logs(self, limit: int = 100, level: str = None) -> List[Dict]:
        """Lấy logs của hệ thống - thử nhiều API khác nhau"""
        import logging
        logger = logging.getLogger('nas_management')
        logs = []
        
        # Kiểm tra API nào có sẵn
        logger.info("Checking available APIs...")
        try:
            eventlog_info = self.get_api_info('SYNO.Core.EventLog')
            if eventlog_info:
                max_version = eventlog_info.get('maxVersion', 'unknown')
                logger.info(f"SYNO.Core.EventLog available, max version: {max_version}")
            else:
                logger.warning("SYNO.Core.EventLog API not found - Log Center may not be installed")
            
            # Kiểm tra các API SYNO.AI.Statistics.*
            all_apis = self.list_all_apis()
            ai_stat_apis = [api for api in all_apis.keys() if api.startswith('SYNO.AI.Statistics')]
            if ai_stat_apis:
                logger.info(f"Found {len(ai_stat_apis)} SYNO.AI.Statistics APIs: {', '.join(ai_stat_apis[:5])}")
        except Exception as e:
            logger.warning(f"Could not check API info: {str(e)}")
        
        # Lưu SID hiện tại
        original_sid = self.sid
        
        # Thử đăng nhập với session SYNO.Core.EventLog nếu chưa có
        try:
            logger.info("Trying to login with SYNO.Core.EventLog session...")
            params = {
                'api': 'SYNO.API.Auth',
                'version': '3',
                'method': 'login',
                'account': self.nas_config.username,
                'passwd': self.nas_config.password,
                'session': 'SYNO.Core.EventLog',
                'format': 'sid'
            }
            data = self._request('auth.cgi', 'GET', params)
            eventlog_sid = data.get('data', {}).get('sid')
            if eventlog_sid:
                self.sid = eventlog_sid
                logger.info("Logged in with SYNO.Core.EventLog session")
        except Exception as e:
            logger.warning(f"Could not login with SYNO.Core.EventLog session: {str(e)}")
            # Giữ nguyên SID cũ
            self.sid = original_sid
        
        # Thử API SYNO.Core.EventLog version 1 (API chính cho Log Center)
        try:
            logger.info("Trying SYNO.Core.EventLog v1 with method 'list'...")
            params = {
                'api': 'SYNO.Core.EventLog',
                'version': '1',
                'method': 'list',
                'limit': limit,
                'offset': 0
            }
            if level:
                params['level'] = level
            data = self._request('entry.cgi', 'GET', params)
            events = data.get('data', {}).get('events', [])
            logger.info(f"SYNO.Core.EventLog v1 returned {len(events)} events")
            if events:
                for event in events:
                    logs.append({
                        'level': event.get('level', 'info').lower(),
                        'category': event.get('category', '') or event.get('program', ''),
                        'message': event.get('message', '') or event.get('msg', ''),
                        'source': event.get('host_name', '') or event.get('source', '') or event.get('program', ''),
                        'time': str(event.get('time', 0)) or str(event.get('timestamp', 0))
                    })
                if logs:
                    logger.info(f"Successfully got {len(logs)} logs from SYNO.Core.EventLog v1")
                    # Khôi phục SID cũ
                    self.sid = original_sid
                    return logs
        except SynologyAPIError as e:
            logger.warning(f"SYNO.Core.EventLog v1 failed: {str(e)}")
            # Thử với method 'query' thay vì 'list'
            try:
                logger.info("Trying SYNO.Core.EventLog v1 with method 'query'...")
                params = {
                    'api': 'SYNO.Core.EventLog',
                    'version': '1',
                    'method': 'query',
                    'limit': limit,
                    'offset': 0
                }
                if level:
                    params['level'] = level
                data = self._request('entry.cgi', 'GET', params)
                events = data.get('data', {}).get('events', [])
                if events:
                    for event in events:
                        logs.append({
                            'level': event.get('level', 'info').lower(),
                            'category': event.get('category', '') or event.get('program', ''),
                            'message': event.get('message', '') or event.get('msg', ''),
                            'source': event.get('host_name', '') or event.get('source', '') or event.get('program', ''),
                            'time': str(event.get('time', 0)) or str(event.get('timestamp', 0))
                        })
                    if logs:
                        logger.info(f"Successfully got {len(logs)} logs from SYNO.Core.EventLog v1 (query)")
                        self.sid = original_sid
                        return logs
            except Exception as e2:
                logger.warning(f"SYNO.Core.EventLog v1 query also failed: {str(e2)}")
        except Exception as e:
            logger.warning(f"SYNO.Core.EventLog v1 error: {str(e)}")
        
        # Khôi phục SID cũ trước khi thử các API khác
        self.sid = original_sid
        
        # Thử API SYNO.Core.EventLog version 2
        try:
            logger.info("Trying SYNO.Core.EventLog v2...")
            params = {
                'api': 'SYNO.Core.EventLog',
                'version': '2',
                'method': 'list',
                'limit': limit,
                'offset': 0
            }
            if level:
                params['level'] = level
            data = self._request('entry.cgi', 'GET', params)
            events = data.get('data', {}).get('events', [])
            logger.info(f"SYNO.Core.EventLog v2 returned {len(events)} events")
            if events:
                for event in events:
                    logs.append({
                        'level': event.get('level', 'info').lower(),
                        'category': event.get('category', '') or event.get('program', ''),
                        'message': event.get('message', '') or event.get('msg', ''),
                        'source': event.get('host_name', '') or event.get('source', '') or event.get('program', ''),
                        'time': str(event.get('time', 0)) or str(event.get('timestamp', 0))
                    })
                if logs:
                    logger.info(f"Successfully got {len(logs)} logs from SYNO.Core.EventLog v2")
                    return logs
        except SynologyAPIError as e:
            logger.warning(f"SYNO.Core.EventLog v2 failed: {str(e)}")
        except Exception as e:
            logger.warning(f"SYNO.Core.EventLog v2 error: {str(e)}")
        
        # Thử API SYNO.LogCenter.Log (Log Center package)
        try:
            logger.info("Trying SYNO.LogCenter.Log v1...")
            params = {
                'api': 'SYNO.LogCenter.Log',
                'version': '1',
                'method': 'list',
                'limit': limit,
                'offset': 0
            }
            if level:
                params['level'] = level
            data = self._request('entry.cgi', 'GET', params)
            log_entries = data.get('data', {}).get('logs', []) or data.get('data', {}).get('events', [])
            logger.info(f"SYNO.LogCenter.Log v1 returned {len(log_entries)} entries")
            if log_entries:
                for entry in log_entries:
                    logs.append({
                        'level': entry.get('level', 'info').lower(),
                        'category': entry.get('category', '') or entry.get('program', ''),
                        'message': entry.get('message', '') or entry.get('msg', ''),
                        'source': entry.get('host_name', '') or entry.get('source', '') or entry.get('program', ''),
                        'time': str(entry.get('time', 0)) or str(entry.get('timestamp', 0))
                    })
                if logs:
                    logger.info(f"Successfully got {len(logs)} logs from SYNO.LogCenter.Log v1")
                    return logs
        except SynologyAPIError as e:
            logger.warning(f"SYNO.LogCenter.Log v1 failed: {str(e)}")
        except Exception as e:
            logger.warning(f"SYNO.LogCenter.Log v1 error: {str(e)}")
        
        # Thử API SYNO.Core.System với method get_log
        try:
            logger.info("Trying SYNO.Core.System v1 get_log...")
            params = {
                'api': 'SYNO.Core.System',
                'version': '1',
                'method': 'get_log',
                'limit': limit
            }
            if level:
                params['level'] = level
            data = self._request('entry.cgi', 'GET', params)
            system_logs = data.get('data', {}).get('logs', [])
            logger.info(f"SYNO.Core.System v1 get_log returned {len(system_logs)} logs")
            if system_logs:
                logger.info(f"Successfully got {len(system_logs)} logs from SYNO.Core.System v1")
                return system_logs
        except SynologyAPIError as e:
            logger.warning(f"SYNO.Core.System v1 get_log failed: {str(e)}")
        except Exception as e:
            logger.warning(f"SYNO.Core.System v1 get_log error: {str(e)}")
        
        # Thử API SYNO.Core.System với version khác
        try:
            logger.info("Trying SYNO.Core.System v2 get_log...")
            params = {
                'api': 'SYNO.Core.System',
                'version': '2',
                'method': 'get_log',
                'limit': limit
            }
            if level:
                params['level'] = level
            data = self._request('entry.cgi', 'GET', params)
            system_logs = data.get('data', {}).get('logs', [])
            logger.info(f"SYNO.Core.System v2 get_log returned {len(system_logs)} logs")
            if system_logs:
                logger.info(f"Successfully got {len(system_logs)} logs from SYNO.Core.System v2")
                return system_logs
        except SynologyAPIError as e:
            logger.warning(f"SYNO.Core.System v2 get_log failed: {str(e)}")
        except Exception as e:
            logger.warning(f"SYNO.Core.System v2 get_log error: {str(e)}")
        
        # Thử API SYNO.Core.System.Log
        try:
            logger.info("Trying SYNO.Core.System.Log v1...")
            params = {
                'api': 'SYNO.Core.System.Log',
                'version': '1',
                'method': 'list',
                'limit': limit
            }
            if level:
                params['level'] = level
            data = self._request('entry.cgi', 'GET', params)
            log_data = data.get('data', {}).get('logs', [])
            logger.info(f"SYNO.Core.System.Log v1 returned {len(log_data)} logs")
            if log_data:
                logger.info(f"Successfully got {len(log_data)} logs from SYNO.Core.System.Log v1")
                return log_data
        except SynologyAPIError as e:
            logger.warning(f"SYNO.Core.System.Log v1 failed: {str(e)}")
        except Exception as e:
            logger.warning(f"SYNO.Core.System.Log v1 error: {str(e)}")
        
        # Thử các API SYNO.AI.Statistics.* nếu có
        try:
            all_apis = self.list_all_apis()
            ai_stat_apis = [api for api in all_apis.keys() if api.startswith('SYNO.AI.Statistics') and 'Log' in api]
            
            if ai_stat_apis:
                logger.info(f"Trying SYNO.AI.Statistics APIs: {', '.join(ai_stat_apis[:3])}")
                
                # Thử SYNO.AI.Statistics.Admin.Log
                if 'SYNO.AI.Statistics.Admin.Log' in ai_stat_apis:
                    try:
                        api_info = all_apis.get('SYNO.AI.Statistics.Admin.Log', {})
                        max_ver = str(api_info.get('maxVersion', '1'))
                        api_path = api_info.get('path', 'entry.cgi')
                        logger.info(f"Trying SYNO.AI.Statistics.Admin.Log v{max_ver}...")
                        
                        # Thử method 'list' trước
                        params = {
                            'api': 'SYNO.AI.Statistics.Admin.Log',
                            'version': max_ver,
                            'method': 'list',
                            'limit': limit,
                            'offset': 0
                        }
                        data = self._request(api_path, 'GET', params)
                        
                        # Debug: log raw response để hiểu structure
                        logger.debug(f"SYNO.AI.Statistics.Admin.Log raw response keys: {list(data.keys())}")
                        if 'data' in data:
                            logger.debug(f"data keys: {list(data['data'].keys()) if isinstance(data['data'], dict) else 'not dict'}")
                        
                        # Thử nhiều cách lấy logs
                        ai_logs = []
                        if isinstance(data.get('data'), list):
                            ai_logs = data.get('data', []) if len(data.get('data', [])) > 0 else []
                        elif isinstance(data.get('data'), dict):
                            data_dict = data.get('data', {})
                            # Kiểm tra các keys có thể chứa logs
                            for key in ['logs', 'data', 'items', 'events']:
                                if key in data_dict and isinstance(data_dict[key], list) and len(data_dict[key]) > 0:
                                    ai_logs = data_dict[key]
                                    break
                        else:
                            # Nếu data không phải dict hoặc list, thử lấy trực tiếp
                            if isinstance(data.get('logs'), list) and len(data.get('logs', [])) > 0:
                                ai_logs = data.get('logs', [])
                            elif isinstance(data.get('data'), list) and len(data.get('data', [])) > 0:
                                ai_logs = data.get('data', [])
                        
                        # Nếu không có, thử method 'get'
                        if not ai_logs:
                            try:
                                params = {
                                    'api': 'SYNO.AI.Statistics.Admin.Log',
                                    'version': max_ver,
                                    'method': 'get',
                                    'limit': limit,
                                    'offset': 0
                                }
                                data = self._request(api_path, 'GET', params)
                                if isinstance(data.get('data'), list):
                                    ai_logs = data.get('data', [])
                                elif isinstance(data.get('data'), dict):
                                    ai_logs = (data.get('data', {}).get('logs', []) or 
                                              data.get('data', {}).get('data', []) or 
                                              data.get('data', {}).get('items', []) or
                                              data.get('data', {}).get('events', []))
                                else:
                                    ai_logs = data.get('logs', []) or data.get('data', [])
                            except Exception as e:
                                logger.warning(f"Method 'get' failed: {str(e)}")
                        
                        if ai_logs:
                            logger.info(f"SYNO.AI.Statistics.Admin.Log returned {len(ai_logs)} logs")
                            # Convert format
                            converted_logs = []
                            for entry in ai_logs:
                                if isinstance(entry, dict):
                                    # Thử nhiều field names khác nhau
                                    level_raw = (entry.get('level') or entry.get('severity') or 
                                                entry.get('log_level') or 'info')
                                    level = level_raw.lower() if isinstance(level_raw, str) else 'info'
                                    if level not in ['info', 'warning', 'error', 'critical', 'debug']:
                                        level = 'info'
                                    
                                    category = (entry.get('category') or entry.get('type') or 
                                               entry.get('module') or entry.get('component') or 
                                               'AI.Statistics.Admin')
                                    
                                    message = (entry.get('message') or entry.get('content') or 
                                              entry.get('description') or entry.get('text') or
                                              entry.get('log') or str(entry))
                                    
                                    source = (entry.get('source') or entry.get('user') or 
                                             entry.get('username') or entry.get('account') or
                                             entry.get('host') or entry.get('ip') or
                                             'AI.Statistics')
                                    
                                    timestamp = (entry.get('time') or entry.get('timestamp') or 
                                                entry.get('date') or entry.get('created_at') or
                                                entry.get('datetime') or entry.get('time_stamp') or
                                                str(timezone.now().timestamp()))
                                    
                                    converted_logs.append({
                                        'level': level,
                                        'category': str(category)[:100],  # Giới hạn độ dài
                                        'message': str(message)[:500],  # Giới hạn độ dài
                                        'source': str(source)[:200],  # Giới hạn độ dài
                                        'time': str(timestamp)
                                    })
                                else:
                                    # Nếu entry không phải dict, convert thành string
                                    converted_logs.append({
                                        'level': 'info',
                                        'category': 'AI.Statistics.Admin',
                                        'message': str(entry)[:500],
                                        'source': 'AI.Statistics',
                                        'time': str(timezone.now().timestamp())
                                    })
                            
                            if converted_logs:
                                logger.info(f"Successfully got {len(converted_logs)} logs from SYNO.AI.Statistics.Admin.Log")
                                return converted_logs
                    except Exception as e:
                        logger.warning(f"SYNO.AI.Statistics.Admin.Log failed: {str(e)}")
                
                # Thử SYNO.AI.Statistics.Request.Log
                if 'SYNO.AI.Statistics.Request.Log' in ai_stat_apis:
                    try:
                        api_info = all_apis.get('SYNO.AI.Statistics.Request.Log', {})
                        max_ver = str(api_info.get('maxVersion', '1'))
                        api_path = api_info.get('path', 'entry.cgi')
                        logger.info(f"Trying SYNO.AI.Statistics.Request.Log v{max_ver}...")
                        
                        # Thử method 'list' trước
                        params = {
                            'api': 'SYNO.AI.Statistics.Request.Log',
                            'version': max_ver,
                            'method': 'list',
                            'limit': limit,
                            'offset': 0
                        }
                        data = self._request(api_path, 'GET', params)
                        
                        # Debug: log raw response để hiểu structure
                        logger.debug(f"SYNO.AI.Statistics.Request.Log raw response keys: {list(data.keys())}")
                        if 'data' in data:
                            logger.debug(f"data keys: {list(data['data'].keys()) if isinstance(data['data'], dict) else 'not dict'}")
                        
                        # Thử nhiều cách lấy logs
                        ai_logs = []
                        if isinstance(data.get('data'), list):
                            ai_logs = data.get('data', []) if len(data.get('data', [])) > 0 else []
                        elif isinstance(data.get('data'), dict):
                            data_dict = data.get('data', {})
                            # Kiểm tra các keys có thể chứa logs
                            for key in ['logs', 'data', 'items', 'events']:
                                if key in data_dict and isinstance(data_dict[key], list) and len(data_dict[key]) > 0:
                                    ai_logs = data_dict[key]
                                    break
                        else:
                            # Nếu data không phải dict hoặc list, thử lấy trực tiếp
                            if isinstance(data.get('logs'), list) and len(data.get('logs', [])) > 0:
                                ai_logs = data.get('logs', [])
                            elif isinstance(data.get('data'), list) and len(data.get('data', [])) > 0:
                                ai_logs = data.get('data', [])
                        
                        # Nếu không có, thử method 'get'
                        if not ai_logs:
                            try:
                                params = {
                                    'api': 'SYNO.AI.Statistics.Request.Log',
                                    'version': max_ver,
                                    'method': 'get',
                                    'limit': limit,
                                    'offset': 0
                                }
                                data = self._request(api_path, 'GET', params)
                                if isinstance(data.get('data'), list):
                                    ai_logs = data.get('data', [])
                                elif isinstance(data.get('data'), dict):
                                    ai_logs = (data.get('data', {}).get('logs', []) or 
                                              data.get('data', {}).get('data', []) or 
                                              data.get('data', {}).get('items', []) or
                                              data.get('data', {}).get('events', []))
                                else:
                                    ai_logs = data.get('logs', []) or data.get('data', [])
                            except Exception as e:
                                logger.warning(f"Method 'get' failed: {str(e)}")
                        
                        if ai_logs and len(ai_logs) > 0:
                            logger.info(f"SYNO.AI.Statistics.Request.Log returned {len(ai_logs)} logs")
                            # Convert format
                            converted_logs = []
                            for entry in ai_logs:
                                if isinstance(entry, dict):
                                    converted_logs.append({
                                        'level': 'info',  # Request logs thường là info
                                        'category': entry.get('category', '') or entry.get('type', '') or 'AI.Request',
                                        'message': str(entry.get('message', '')) or str(entry.get('content', '')) or str(entry.get('request', '')) or str(entry),
                                        'source': entry.get('source', '') or entry.get('ip', '') or entry.get('client_ip', '') or 'AI.Request',
                                        'time': str(entry.get('time', 0)) or str(entry.get('timestamp', 0)) or str(entry.get('date', '')) or str(entry.get('created_at', ''))
                                    })
                                else:
                                    converted_logs.append({
                                        'level': 'info',
                                        'category': 'AI.Request',
                                        'message': str(entry),
                                        'source': 'AI.Request',
                                        'time': str(timezone.now().timestamp())
                                    })
                            
                            if converted_logs:
                                logger.info(f"Successfully got {len(converted_logs)} logs from SYNO.AI.Statistics.Request.Log")
                                return converted_logs
                    except Exception as e:
                        logger.warning(f"SYNO.AI.Statistics.Request.Log failed: {str(e)}")
        except Exception as e:
            logger.warning(f"Error trying SYNO.AI.Statistics APIs: {str(e)}")
        
        # Nếu không có API nào hoạt động, thử đọc file log trực tiếp
        logger.info("Tất cả các API logs đều không hoạt động, thử đọc file log trực tiếp...")
        try:
            # Thử đọc file log từ /var/log/
            log_paths = [
                '/var/log/messages',
                '/var/log/syslog',
                '/var/log/system.log',
                '/var/log/daemon.log',
            ]
            
            for log_path in log_paths:
                try:
                    logger.info(f"Trying to read log file: {log_path}")
                    file_content = self.download_file(log_path)
                    if file_content:
                        # Parse log file (thường là text format)
                        lines = file_content.decode('utf-8', errors='ignore').split('\n')
                        # Lấy các dòng gần nhất
                        recent_lines = lines[-limit:] if len(lines) > limit else lines
                        
                        parsed_logs = []
                        for line in recent_lines:
                            if line.strip():
                                # Parse log line (format có thể khác nhau)
                                # Ví dụ: "2024-01-01 12:00:00 [INFO] message"
                                parts = line.strip().split(' ', 3) if len(line.split()) >= 4 else [line]
                                if len(parts) >= 4:
                                    timestamp_str = f"{parts[0]} {parts[1]}"
                                    level_str = parts[2].strip('[]').lower() if len(parts) > 2 else 'info'
                                    message = parts[3] if len(parts) > 3 else line
                                    
                                    parsed_logs.append({
                                        'level': level_str if level_str in ['info', 'warning', 'error', 'critical'] else 'info',
                                        'category': '',
                                        'message': message[:500],
                                        'source': '',
                                        'time': timestamp_str
                                    })
                        
                        if parsed_logs:
                            logger.info(f"Successfully read {len(parsed_logs)} logs from file: {log_path}")
                            self.sid = original_sid
                            return parsed_logs
                except Exception as e:
                    logger.warning(f"Could not read log file {log_path}: {str(e)}")
                    continue
        except Exception as e:
            logger.warning(f"Error reading log files: {str(e)}")
        
        # Khôi phục SID cũ
        self.sid = original_sid
        
        # Nếu không có API nào hoạt động
        logger.error("Tất cả các API logs đều không hoạt động và không thể đọc file log!")
        return []
    
    def list_files(self, folder_path: str = '/', limit: int = 1000) -> List[Dict]:
        """Liệt kê files trong folder"""
        try:
            params = {
                'api': 'SYNO.FileStation.List',
                'version': '2',
                'method': 'list',
                'folder_path': folder_path,
                'limit': limit,
                'additional': '["size","owner","time","perm","type"]'
            }
            data = self._request('entry.cgi', 'GET', params)
            return data.get('data', {}).get('files', [])
        except Exception as e:
            raise SynologyAPIError(f"Failed to list files: {str(e)}")
    
    def upload_file(self, file_path: str, file_content: bytes, overwrite: bool = True) -> bool:
        """Upload file lên NAS"""
        try:
            # Tạo upload URL
            params = {
                'api': 'SYNO.FileStation.Upload',
                'version': '2',
                'method': 'upload',
                'path': file_path,
                'overwrite': 'true' if overwrite else 'false',
                'create_parents': 'true'
            }
            
            # Upload file
            upload_url = f"{self.base_url}/webapi/entry.cgi"
            files = {'file': file_content}
            params['_sid'] = self.sid
            
            response = self.session.post(upload_url, data=params, files=files, timeout=300)
            response.raise_for_status()
            data = response.json()
            
            return data.get('success', False)
            
        except Exception as e:
            raise SynologyAPIError(f"Failed to upload file: {str(e)}")
    
    def download_file(self, file_path: str) -> bytes:
        """Download file từ NAS"""
        try:
            params = {
                'api': 'SYNO.FileStation.Download',
                'version': '2',
                'method': 'download',
                'path': file_path,
                'mode': 'download'
            }
            
            download_url = f"{self.base_url}/webapi/entry.cgi"
            params['_sid'] = self.sid
            
            response = self.session.get(download_url, params=params, stream=True, timeout=300)
            response.raise_for_status()
            
            return response.content
            
        except Exception as e:
            raise SynologyAPIError(f"Failed to download file: {str(e)}")
    
    def create_folder(self, folder_path: str, name: str, force_parent: bool = True) -> bool:
        """Tạo folder mới"""
        try:
            params = {
                'api': 'SYNO.FileStation.CreateFolder',
                'version': '2',
                'method': 'create',
                'folder_path': folder_path,
                'name': name,
                'force_parent': 'true' if force_parent else 'false'
            }
            
            data = self._request('entry.cgi', 'GET', params)
            return data.get('success', False)
            
        except Exception as e:
            raise SynologyAPIError(f"Failed to create folder: {str(e)}")
    
    def delete_file(self, file_path: str) -> bool:
        """Xóa file/folder"""
        try:
            params = {
                'api': 'SYNO.FileStation.Delete',
                'version': '2',
                'method': 'delete',
                'path': json.dumps([file_path]),
                'recursive': 'true'
            }
            
            data = self._request('entry.cgi', 'GET', params)
            return data.get('success', False)
            
        except Exception as e:
            raise SynologyAPIError(f"Failed to delete file: {str(e)}")
    
    def __enter__(self):
        """Context manager entry"""
        self.login()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.logout()

