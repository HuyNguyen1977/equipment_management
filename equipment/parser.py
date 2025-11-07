"""
Parser cho file DxDiag.txt để trích xuất thông tin hệ thống
"""
import re
from datetime import datetime


def parse_dxdiag(file_path):
    """
    Parse file DxDiag.txt và trả về dictionary chứa thông tin hệ thống
    """
    result = {
        'machine_name': '',
        'operating_system': '',
        'system_manufacturer': '',
        'system_model': '',
        'processor': '',
        'memory': '',
        'graphics_card': '',
        'monitor_name': '',
        'monitor_model': '',
        'technical_specs': {}
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        return result
    
    # Parse Machine name
    machine_match = re.search(r'Machine name:\s*(.+)', content, re.IGNORECASE)
    if machine_match:
        result['machine_name'] = machine_match.group(1).strip()
    
    # Parse Operating System
    os_match = re.search(r'Operating System:\s*(.+)', content, re.IGNORECASE)
    if os_match:
        result['operating_system'] = os_match.group(1).strip()
    
    # Parse System Manufacturer
    manufacturer_match = re.search(r'System Manufacturer:\s*(.+)', content, re.IGNORECASE)
    if manufacturer_match:
        result['system_manufacturer'] = manufacturer_match.group(1).strip()
    
    # Parse System Model
    model_match = re.search(r'System Model:\s*(.+)', content, re.IGNORECASE)
    if model_match:
        result['system_model'] = model_match.group(1).strip()
    
    # Parse Processor
    processor_match = re.search(r'Processor:\s*(.+)', content, re.IGNORECASE)
    if processor_match:
        result['processor'] = processor_match.group(1).strip()
    
    # Parse Memory
    memory_match = re.search(r'Memory:\s*(\d+)\s*MB\s*RAM', content, re.IGNORECASE)
    if memory_match:
        memory_mb = int(memory_match.group(1))
        memory_gb = memory_mb / 1024
        result['memory'] = f"{memory_mb} MB ({memory_gb:.1f} GB)"
    else:
        # Try alternative format
        memory_match = re.search(r'Memory:\s*(.+)', content, re.IGNORECASE)
        if memory_match:
            result['memory'] = memory_match.group(1).strip()
    
    # Parse Graphics Card (first display device - Card name)
    graphics_match = re.search(r'Card name:\s*(.+)', content, re.IGNORECASE)
    if graphics_match:
        card_name = graphics_match.group(1).strip()
        result['graphics_card'] = card_name
        result['technical_specs']['Card name'] = card_name
    
    # Lưu các thông số chính vào technical_specs
    if result['processor']:
        result['technical_specs']['Processor'] = result['processor']
    
    if result['memory']:
        result['technical_specs']['Memory'] = result['memory']
    
    if result['system_manufacturer']:
        result['technical_specs']['System Manufacturer'] = result['system_manufacturer']
    
    if result['system_model']:
        result['technical_specs']['System Model'] = result['system_model']
    
    # Parse Disk & DVD/CD-ROM Drives để lấy SSD/HDD
    disk_section_match = re.search(r'Disk & DVD/CD-ROM Drives\s*-+\s*(.+?)(?=\n-{3,}|\Z)', content, re.IGNORECASE | re.DOTALL)
    if disk_section_match:
        disk_section = disk_section_match.group(1)
        # Tìm tất cả các ổ đĩa
        drives = []
        drive_pattern = r'Drive:\s*([A-Z]:)\s*\n\s*Free Space:\s*(.+?)\s*\n\s*Total Space:\s*(.+?)\s*\n\s*File System:\s*(.+?)\s*\n\s*Model:\s*(.+?)(?=\n\s*Drive:|\n-{3,}|\Z)'
        for match in re.finditer(drive_pattern, disk_section, re.IGNORECASE | re.MULTILINE):
            drive_letter = match.group(1)
            free_space = match.group(2).strip()
            total_space = match.group(3).strip()
            file_system = match.group(4).strip()
            model = match.group(5).strip()
            
            # Xác định loại ổ đĩa (SSD hoặc HDD) dựa trên model
            drive_type = 'Unknown'
            if 'SSD' in model.upper() or 'SOLID' in model.upper():
                drive_type = 'SSD'
            elif 'HDD' in model.upper() or 'HARD' in model.upper():
                drive_type = 'HDD'
            else:
                # Một số model phổ biến của SSD
                ssd_keywords = ['SA400', 'MX500', '860', '870', '970', '980', 'NVMe', 'M.2']
                if any(keyword in model.upper() for keyword in ssd_keywords):
                    drive_type = 'SSD'
                else:
                    drive_type = 'HDD'
            
            drive_info = f"{drive_letter} - {model} ({drive_type}) - Total: {total_space}, Free: {free_space}"
            drives.append(drive_info)
        
        if drives:
            result['technical_specs']['Storage (SSD/HDD)'] = ' | '.join(drives)
    
    # Parse BIOS
    bios_match = re.search(r'BIOS:\s*(.+)', content, re.IGNORECASE)
    if bios_match:
        result['technical_specs']['BIOS'] = bios_match.group(1).strip()
    
    # Parse DirectX Version
    directx_match = re.search(r'DirectX Version:\s*(.+)', content, re.IGNORECASE)
    if directx_match:
        result['technical_specs']['DirectX Version'] = directx_match.group(1).strip()
    
    # Parse Monitor Name
    monitor_match = re.search(r'Monitor Name:\s*(.+)', content, re.IGNORECASE)
    if monitor_match:
        monitor_name = monitor_match.group(1).strip()
        result['monitor_name'] = monitor_name
        result['technical_specs']['Monitor'] = monitor_name
    
    # Parse Monitor Model
    monitor_model_match = re.search(r'Monitor Model:\s*(.+)', content, re.IGNORECASE)
    if monitor_model_match:
        monitor_model = monitor_model_match.group(1).strip()
        result['monitor_model'] = monitor_model
        result['technical_specs']['Monitor Model'] = monitor_model
    
    # Parse Current Mode (resolution)
    resolution_match = re.search(r'Current Mode:\s*(.+)', content, re.IGNORECASE)
    if resolution_match:
        result['technical_specs']['Resolution'] = resolution_match.group(1).strip()
    
    return result

