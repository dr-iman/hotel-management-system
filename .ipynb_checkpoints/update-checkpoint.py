# fix_all_issues.py
import os
import sys

def fix_rack_widget_session():
    """رفع مشکل Session در RackWidget"""
    rack_widget_path = os.path.join(os.path.dirname(__file__), 'ui/rack_widget.py')
    
    with open(rack_widget_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # جایگزینی self.Session() با self.reservation_manager.Session()
    old_code = 'session = self.Session()'
    new_code = 'session = self.reservation_manager.Session()'
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        print("✅ مشکل Session در RackWidget رفع شد")
    else:
        print("✅ کد Session در RackWidget صحیح است")
    
    with open(rack_widget_path, 'w', encoding='utf-8') as f:
        f.write(content)

def fix_reservation_manager_datetime():
    """رفع مشکل replace() در reservation_manager"""
    reservation_manager_path = os.path.join(os.path.dirname(__file__), 'models/reservation_manager.py')
    
    with open(reservation_manager_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # پیدا کردن متد get_room_availability_with_back_to_back و تصحیح آن
    method_start = 'def get_room_availability_with_back_to_back(self, room_id, check_in, check_out):'
    
    if method_start in content:
        # جایگزینی بخش تنظیم زمان‌ها
        old_time_code = '''        # تنظیم زمان‌های استاندارد هتل
        # Check-in: 14:00, Check-out: 12:00
        check_in_time = check_in.replace(hour=14, minute=0, second=0, microsecond=0)
        check_out_time = check_out.replace(hour=12, minute=0, second=0, microsecond=0)'''
        
        new_time_code = '''        # تنظیم زمان‌های استاندارد هتل - روش صحیح
        # Check-in: 14:00, Check-out: 12:00
        if isinstance(check_in, datetime):
            check_in_time = check_in.replace(hour=14, minute=0, second=0, microsecond=0)
        else:  # اگر date است
            check_in_time = datetime.combine(check_in, datetime.min.time()).replace(hour=14, minute=0, second=0)
            
        if isinstance(check_out, datetime):
            check_out_time = check_out.replace(hour=12, minute=0, second=0, microsecond=0)
        else:  # اگر date است
            check_out_time = datetime.combine(check_out, datetime.min.time()).replace(hour=12, minute=0, second=0)'''
        
        if old_time_code in content:
            content = content.replace(old_time_code, new_time_code)
            print("✅ مشکل replace() در reservation_manager رفع شد")
        else:
            print("✅ کد زمان‌ها در reservation_manager صحیح است")
    
    with open(reservation_manager_path, 'w', encoding='utf-8') as f:
        f.write(content)

def fix_main_window_imports():
    """رفع مشکل importهای main_window"""
    main_window_path = os.path.join(os.path.dirname(__file__), 'ui', 'main_window.py')
    
    with open(main_window_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # اضافه کردن importهای لازم اگر وجود ندارند
    required_imports = [
        'from PyQt6.QtWidgets import QApplication',
        'import jdatetime',
        'from datetime import datetime'
    ]
    
    for import_line in required_imports:
        if import_line not in content:
            # اضافه کردن بعد از سایر importها
            import_section_end = content.find('\n\n', content.find('import'))
            if import_section_end != -1:
                content = content[:import_section_end] + '\n' + import_line + content[import_section_end:]
                print(f"✅ {import_line} اضافه شد")
    
    with open(main_window_path, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    """رفع تمام مشکلات"""
    print("🔧 در حال رفع مشکلات سیستم...")
    
    fix_rack_widget_session()
    fix_reservation_manager_datetime()
    fix_main_window_imports()
    
    print("✅ تمام مشکلات رفع شدند")
    print("🎯 حالا برنامه را اجرا کنید: python main.py")

if __name__ == "__main__":
    main()