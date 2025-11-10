"""
Management command để import dữ liệu ban đầu cho ticket system
Chạy: python manage.py init_ticket_data
"""
from django.core.management.base import BaseCommand
from tickets.models import Company, Department, TicketCategory


class Command(BaseCommand):
    help = 'Import dữ liệu ban đầu cho ticket system (Company, Department, TicketCategory)'

    def handle(self, *args, **options):
        self.stdout.write('Bat dau import du lieu...')
        
        # Tạo các công ty
        self.stdout.write('Tao cac cong ty...')
        pega, _ = Company.objects.get_or_create(
            code='PEGA',
            defaults={'name': 'CÔNG TY CP PEGA HOLDINGS (PEGA HOLDINGS)'}
        )
        sgb, _ = Company.objects.get_or_create(
            code='SGB',
            defaults={'name': 'CÔNG TY CP VĂN HOÁ SÁCH SÀI GÒN'}
        )
        zb, _ = Company.objects.get_or_create(
            code='ZB',
            defaults={'name': 'CÔNG TY CP ZENBOOKS'}
        )
        self.stdout.write(self.style.SUCCESS(f'Da tao {Company.objects.count()} cong ty'))
        
        # Tạo các phòng ban
        self.stdout.write('Tao cac phong ban...')
        departments_data = [
            # Kinh doanh
            ('Kinh doanh', None, None),
            ('Kinh doanh Sách', 'Kinh doanh', None),
            ('BP Kinh doanh (B2B) + Nhà Sách SGB-ZB', 'Kinh doanh Sách', None),
            ('BP Kinh doanh ZB (B2B & Dự án)', 'Kinh doanh Sách', None),
            ('BP In Ấn SGB ZB', 'Kinh doanh Sách', None),
            ('BP Kinh doanh TMĐT', 'Kinh doanh Sách', None),
            ('Phòng Kinh doanh HN', 'Kinh doanh Sách', None),
            ('Truyền thông và Tiếp thị', 'Kinh doanh Sách', None),
            ('Kinh doanh VPP & Quảng cáo', 'Kinh doanh', None),
            ('Phòng Kinh doanh VPP Miền Nam', 'Kinh doanh VPP & Quảng cáo', None),
            ('Kinh doanh VPP & Quảng cáo Miền Bắc', 'Kinh doanh VPP & Quảng cáo', None),
            ('Kinh doanh VPP Miền Trung', 'Kinh doanh VPP & Quảng cáo', None),
            ('Kinh doanh Quảng Cáo Miền Nam', 'Kinh doanh VPP & Quảng cáo', None),
            ('Kinh doanh Textbook', 'Kinh doanh', None),
            # Bản quyền
            ('Bản quyền', None, None),
            # Tài chính - kế toán
            ('Tài chính - kế toán', None, None),
            ('Kế Toán SGB', 'Tài chính - kế toán', None),
            ('Kế Toán ZB', 'Tài chính - kế toán', None),
            ('Kế toán Pega', 'Tài chính - kế toán', None),
            ('Mua hàng', 'Tài chính - kế toán', None),
            # Nhân sự - hành chính
            ('Nhân sự - hành chính', None, None),
            ('SGB & ZB', 'Nhân sự - hành chính', None),
            ('PEGA', 'Nhân sự - hành chính', None),
            # Biên tập & biên soạn
            ('Biên tập & biên soạn', None, None),
            ('SaigonBooks', 'Biên tập & biên soạn', None),
            ('Biên soạn', 'Biên tập & biên soạn', None),
            ('Biên tập HN', 'Biên tập & biên soạn', None),
            # Pháp chế & tuân thủ
            ('Pháp chế & tuân thủ', None, None),
            # Thiết kế & dàn trang
            ('Thiết kế & dàn trang', None, None),
            ('Thiết kế', 'Thiết kế & dàn trang', None),
            ('Dàn Trang', 'Thiết kế & dàn trang', None),
            # Công nghệ
            ('Công nghệ', None, None),
            # Kho và điều vận
            ('Kho và điều vận', None, None),
            ('Kho Zenbooks-Saigonbooks', 'Kho và điều vận', None),
            ('Kho B2B', 'Kho và điều vận', None),
            ('Miền Nam', 'Kho B2B', None),
            ('Miền Trung', 'Kho B2B', None),
            ('Miền Bắc', 'Kho B2B', None),
            ('Điều vận', 'Kho và điều vận', None),
            # VP HÀ NỘI
            ('VP HÀ NỘI', None, None),
        ]
        
        dept_dict = {}
        for dept_name, parent_name, company_code in departments_data:
            parent = dept_dict.get(parent_name) if parent_name else None
            company = Company.objects.get(code=company_code) if company_code else None
            
            dept, created = Department.objects.get_or_create(
                name=dept_name,
                defaults={'parent': parent, 'company': company}
            )
            dept_dict[dept_name] = dept
        
        self.stdout.write(self.style.SUCCESS(f'Da tao {Department.objects.count()} phong ban'))
        
        # Tạo các loại yêu cầu
        self.stdout.write('Tao cac loai yeu cau...')
        categories_data = [
            # Hỗ trợ phần cứng
            ('Hỗ trợ phần cứng', None),
            ('Cài đặt, sửa lỗi máy in', 'Hỗ trợ phần cứng'),
            ('Xử lý sự cố phần cứng PC/Laptop', 'Hỗ trợ phần cứng'),
            ('Đánh giá, đề xuất và triển khai trang bị thiết bị mới', 'Hỗ trợ phần cứng'),
            ('Hỗ trợ kết nối, xử lý sự cố camera phòng họp, cáp kết nối', 'Hỗ trợ phần cứng'),
            ('Tiếp nhận, kiểm tra và xử lý bảo hành/sửa chữa thiết bị', 'Hỗ trợ phần cứng'),
            ('Khác (Phần cứng)', 'Hỗ trợ phần cứng'),
            # Hỗ trợ phần mềm & tài khoản
            ('Hỗ trợ phần mềm & tài khoản', None),
            ('Cài đặt, sửa lỗi phần mềm', 'Hỗ trợ phần mềm & tài khoản'),
            ('Tạo, cấp quyền, khóa tài khoản người dùng', 'Hỗ trợ phần mềm & tài khoản'),
            ('Tạo, cấu hình, khóa và reset mật khẩu Email', 'Hỗ trợ phần mềm & tài khoản'),
            ('Xử lý lỗi Email', 'Hỗ trợ phần mềm & tài khoản'),
            ('Cấp quyền truy cập File Server', 'Hỗ trợ phần mềm & tài khoản'),
            ('Khác (Phần mềm)', 'Hỗ trợ phần mềm & tài khoản'),
            # Hỗ trợ hệ thống & kỹ thuật
            ('Hỗ trợ hệ thống & kỹ thuật', None),
            ('Xử lý sự cố treo Server', 'Hỗ trợ hệ thống & kỹ thuật'),
            ('Khắc phục sự cố hạ tầng CNTT (điện, mạng, thoại)', 'Hỗ trợ hệ thống & kỹ thuật'),
            ('Kiểm tra và khắc phục lỗi hệ thống', 'Hỗ trợ hệ thống & kỹ thuật'),
            ('Xử lý lỗi trên website', 'Hỗ trợ hệ thống & kỹ thuật'),
            ('Khác (Hệ thống)', 'Hỗ trợ hệ thống & kỹ thuật'),
            # Hỗ trợ dự án & triển khai
            ('Hỗ trợ dự án & triển khai', None),
            ('Giám sát triển khai hệ thống LAN (di dời, mở mới)', 'Hỗ trợ dự án & triển khai'),
            ('Đánh giá và triển khai hệ thống công nghệ (phần cứng & phần mềm)', 'Hỗ trợ dự án & triển khai'),
            ('Khác (Dự án)', 'Hỗ trợ dự án & triển khai'),
        ]
        
        cat_dict = {}
        for cat_name, parent_name in categories_data:
            parent = cat_dict.get(parent_name) if parent_name else None
            
            cat, created = TicketCategory.objects.get_or_create(
                name=cat_name,
                defaults={'parent': parent}
            )
            cat_dict[cat_name] = cat
        
        self.stdout.write(self.style.SUCCESS(f'Da tao {TicketCategory.objects.count()} loai yeu cau'))
        
        self.stdout.write(self.style.SUCCESS('\nHoan thanh import du lieu!'))

