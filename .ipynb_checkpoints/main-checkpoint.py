import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtCore import QTimer

def create_sample_data(engine):
    """ایجاد داده‌های نمونه فقط برای اولین بار"""
    try:
        from sqlalchemy.orm import sessionmaker
        from models.models import Room, Guest, Reservation
        from datetime import datetime, timedelta
        import random
        
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("🏨 در حال ایجاد اتاق‌ها...")
        room_types = [
            {'type': 'سینگل', 'price': 80, 'capacity': 1, 'max_guests': 1},
            {'type': 'دبل', 'price': 120, 'capacity': 2, 'max_guests': 2},
            {'type': 'تویین', 'price': 130, 'capacity': 2, 'max_guests': 2},
            {'type': 'سوئیت', 'price': 200, 'capacity': 4, 'max_guests': 4},
            {'type': 'دیلوکس', 'price': 180, 'capacity': 3, 'max_guests': 3}
        ]
        
        rooms = []
        room_id = 1
        for floor in range(1, 7):  # 6 طبقه
            rooms_per_floor = 21
            for room_num in range(1, rooms_per_floor + 1):
                room_config = random.choice(room_types)
                room = Room(
                    id=room_id,
                    room_number=f"{floor}{room_num:02d}",
                    room_type=room_config['type'],
                    floor=floor,
                    price_per_night=room_config['price'],
                    capacity=room_config['capacity'],
                    max_guests=room_config['max_guests'],
                    amenities="TV, WiFi, Air Conditioning"
                )
                rooms.append(room)
                room_id += 1
        
        session.add_all(rooms)
        session.commit()
        print(f"✅ {len(rooms)} اتاق ایجاد شد")
        
        # ایجاد مهمانان نمونه
        print("👥 در حال ایجاد مهمانان...")
        first_names = ['علی', 'محمد', 'سارا', 'فاطمه', 'رضا', 'حسین', 'مریم', 'زهرا', 'امیر', 'نرگس']
        last_names = ['احمدی', 'محمدی', 'علوی', 'حسینی', 'رحمتی', 'کاظمی', 'جعفری', 'مرادی', 'قاسمی']
        
        guests = []
        for i in range(50):
            guest = Guest(
                first_name=random.choice(first_names),
                last_name=random.choice(last_names),
                email=f"guest{i}@example.com",
                phone=f"09{random.randint(100000000, 999999999)}",
                nationality="ایرانی"
            )
            guests.append(guest)
        
        session.add_all(guests)
        session.commit()
        print(f"✅ {len(guests)} مهمان ایجاد شد")
        
        # ایجاد رزرواسیون‌های نمونه
        print("📅 در حال ایجاد رزرواسیون‌ها...")
        today = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)
        reservations = []
        
        # انواع پکیج
        packages = ["فول برد", "اسکان + صبحانه", "فقط اسکان"]
        guest_types = ["حضوری", "آژانس", "رزرو", "سایت", "اینستاگرام"]
        
        # استفاده از IDهای واقعی اتاق‌ها و مهمانان
        room_ids = [room.id for room in rooms]
        guest_ids = [guest.id for guest in guests]
        
        # ایجاد 100 رزرو برای دو ماه آینده
        for i in range(100):
            room_id = random.choice(room_ids)
            guest_id = random.choice(guest_ids)
            room = session.query(Room).filter(Room.id == room_id).first()
            
            # تاریخ‌های تصادفی برای رزرو - بیشتر در دو ماه آینده
            days_from_now = random.randint(0, 60)
            stay_duration = random.randint(1, 7)
            
            check_in = today + timedelta(days=days_from_now)
            check_out = check_in + timedelta(days=stay_duration)
            
            # 20% احتمال برای رزروهای هم‌پوشانی در همان روز
            has_same_day_checkout = random.random() < 0.2
            
            if has_same_day_checkout:
                second_guest_id = random.choice([gid for gid in guest_ids if gid != guest_id])
                second_check_in = check_out.replace(hour=14, minute=0)
                second_check_out = second_check_in + timedelta(days=random.randint(1, 3))
                
                second_reservation = Reservation(
                    room_id=room_id,
                    guest_id=second_guest_id,
                    check_in=second_check_in,
                    check_out=second_check_out,
                    status='confirmed',
                    adults=random.randint(1, 2),
                    children=random.randint(0, 1),
                    total_amount=room.price_per_night * (second_check_out - second_check_in).days,
                    paid_amount=room.price_per_night * (second_check_out - second_check_in).days * random.uniform(0.5, 1.0),
                    package_type=random.choice(packages),
                    guest_type=random.choice(guest_types),
                    companion_type=random.choice(["بزرگسال", "کودک", "خردسال"])
                )
                reservations.append(second_reservation)
            
            # وضعیت‌های مختلف
            if check_in <= today:
                status = random.choice(['checked_in', 'checked_in', 'confirmed'])
            else:
                status = 'confirmed'
            
            reservation = Reservation(
                room_id=room_id,
                guest_id=guest_id,
                check_in=check_in,
                check_out=check_out,
                status=status,
                adults=random.randint(1, room.max_guests),
                children=random.randint(0, 2),
                total_amount=room.price_per_night * stay_duration,
                paid_amount=room.price_per_night * stay_duration * random.uniform(0.5, 1.0),
                package_type=random.choice(packages),
                guest_type=random.choice(guest_types),
                companion_type=random.choice(["بزرگسال", "کودک", "خردسال"])
            )
            reservations.append(reservation)
        
        session.add_all(reservations)
        session.commit()
        session.close()
        
        print("✅ داده‌های نمونه با موفقیت ایجاد شد!")
        print("📊 آمار ایجاد شده:")
        print(f"   - تعداد اتاق‌ها: {len(rooms)}")
        print(f"   - تعداد مهمانان: {len(guests)}")
        print(f"   - تعداد رزرواسیون‌ها: {len(reservations)}")
        
    except Exception as e:
        print(f"❌ خطا در ایجاد داده‌های نمونه: {e}")
        import traceback
        traceback.print_exc()

def test_database_persistence():
    """تست ماندگاری داده‌ها در دیتابیس"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, 'database', 'hotel.db')
        
        if os.path.exists(db_path):
            print(f"📊 تست ماندگاری دیتابیس...")
            
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from models.models import Reservation, Guest, Room
            
            db_url = f"sqlite:///{db_path}"
            engine = create_engine(db_url)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # شمارش رکوردها
            reservations_count = session.query(Reservation).count()
            guests_count = session.query(Guest).count()
            rooms_count = session.query(Room).count()
            
            session.close()
            
            print(f"📈 آمار دیتابیس:")
            print(f"   - تعداد رزروها: {reservations_count}")
            print(f"   - تعداد مهمانان: {guests_count}") 
            print(f"   - تعداد اتاق‌ها: {rooms_count}")
            
        else:
            print("❌ دیتابیس وجود ندارد")
            
    except Exception as e:
        print(f"❌ خطا در تست ماندگاری: {e}")

def init_database():
    """تابع مستقیم برای راه‌اندازی پایگاه داده"""
    try:
        print("🔧 در حال راه‌اندازی پایگاه داده...")
        
        # اضافه کردن مسیرها به sys.path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.append(current_dir)
        sys.path.append(os.path.join(current_dir, 'models'))
        
        from models.models import Base, Room, Guest, Reservation
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        # ایجاد دایرکتوری database اگر وجود ندارد
        db_dir = os.path.join(current_dir, 'database')
        os.makedirs(db_dir, exist_ok=True)
        
        db_path = os.path.join(db_dir, 'hotel.db')
        db_url = f"sqlite:///{db_path}"
        
        print(f"📁 مسیر پایگاه داده: {db_path}")
        
        engine = create_engine(db_url)
        
        # ✅ فقط اگر دیتابیس وجود ندارد، ایجاد داده‌های نمونه
        if not os.path.exists(db_path):
            print("🆕 پایگاه داده وجود ندارد، در حال ایجاد...")
            Base.metadata.create_all(engine)
            
            # ایجاد داده‌های نمونه فقط برای اولین بار
            create_sample_data(engine)
        else:
            print("✅ پایگاه داده موجود است")
            # فقط جداول را ایجاد کن اگر وجود ندارند (بدون پاک کردن داده‌های موجود)
            Base.metadata.create_all(engine)
        
        return True
        
    except Exception as e:
        print(f"❌ خطا در ایجاد پایگاه داده: {e}")
        import traceback
        traceback.print_exc()
        return False

class ApplicationController:
    """کنترلر اصلی برنامه برای مدیریت preloader و main window"""
    
    def __init__(self, app):
        self.app = app
        self.main_window = None
        
    def show_preloader(self):
        """نمایش preloader"""
        try:
            from preloader import PreloaderWindow
            self.preloader = PreloaderWindow()
            self.preloader.finished.connect(self.on_preloader_finished)
            self.preloader.show()
            print("✅ Preloader نمایش داده شد")
        except Exception as e:
            print(f"❌ خطا در نمایش preloader: {e}")
            # اگر preloader مشکل داشت، مستقیماً main window را نشان بده
            self.show_main_window()
    
    def on_preloader_finished(self):
        """هنگام اتمام preloader"""
        print("🎯 Preloader به اتمام رسید، در حال نمایش پنجره اصلی...")
        self.show_main_window()
        
    def show_main_window(self):
        """نمایش پنجره اصلی بعد از اتمام preloader"""
        print("🚀 راه‌اندازی برنامه اصلی...")
        
        try:
            # بستن preloader اگر باز است
            if hasattr(self, 'preloader') and self.preloader:
                self.preloader.close()
                self.preloader = None
            
            # اضافه کردن مسیرها به sys.path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            sys.path.append(current_dir)
            sys.path.append(os.path.join(current_dir, 'models'))
            sys.path.append(os.path.join(current_dir, 'ui'))
            sys.path.append(os.path.join(current_dir, 'utils'))
            
            # import و ایجاد پنجره اصلی
            from ui.main_window import MainWindow
            self.main_window = MainWindow()
            
            # نمایش پنجره
            self.main_window.show()
            
            # اگر پنجره maximized نشد، آن را maximize کن
            if not self.main_window.isMaximized():
                self.main_window.showMaximized()
                
            print("✅ برنامه اصلی نمایش داده شد")
            
        except Exception as e:
            print(f"❌ خطا در ایجاد پنجره اصلی: {e}")
            import traceback
            traceback.print_exc()
            
            # نمایش پیام خطا به کاربر
            QMessageBox.critical(
                None, 
                "خطای سیستمی", 
                f"خطا در راه‌اندازی برنامه:\n{str(e)}\n\nلطفاً از صحت نصب پکیج‌ها اطمینان حاصل کنید."
            )

def load_fonts():
    """بارگذاری فونت‌های فارسی"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(current_dir, 'assets', 'fonts', 'B Titr.ttf')
        
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                font_families = QFontDatabase.applicationFontFamilies(font_id)
                if font_families:
                    print(f"✅ فونت B Titr بارگذاری شد: {font_families[0]}")
                    return True
                else:
                    print("⚠️ فونت B Titr بارگذاری شد اما فونت‌فمیلی یافت نشد")
            else:
                print("❌ خطا در بارگذاری فونت B Titr")
        else:
            print(f"⚠️ فایل فونت یافت نشد: {font_path}")
            
    except Exception as e:
        print(f"⚠️ خطا در بارگذاری فونت: {e}")
    
    return False

def load_styles(app):
    """بارگذاری استایل‌های برنامه"""
    try:
        from theme_manager import ThemeManager
        theme_manager = ThemeManager()
        success = theme_manager.load_theme(app)
        
        if success:
            print(f"🎨 تم {theme_manager.current_theme} بارگذاری شد")
        else:
            print("⚠️ خطا در بارگذاری استایل‌ها")
            
    except Exception as e:
        print(f"⚠️ خطا در بارگذاری استایل‌ها: {e}")

def main():
    """تابع اصلی اجرای برنامه"""
    print("=" * 60)
    print("🏨 سیستم مدیریت رزرواسیون هتل آراد")
    print("🔄 در حال راه‌اندازی...")
    print("=" * 60)
    
    try:
        # راه‌اندازی پایگاه داده
        if not init_database():
            print("❌ برنامه به دلیل خطا در پایگاه داده متوقف شد.")
            input("برای خروج Enter را بفشارید...")
            return 1
        
        print("\n" + "=" * 60)
        # تست ماندگاری داده‌ها
        test_database_persistence()
        print("=" * 60)
        
        # ایجاد برنامه Qt
        app = QApplication(sys.argv)
        app.setApplicationName("هتل آراد")
        app.setApplicationVersion("1.0.0")
        
        # بارگذاری فونت‌ها
        print("\n🔤 در حال بارگذاری فونت‌ها...")
        font_loaded = load_fonts()
        
        # تنظیم فونت پیش‌فرض
        if font_loaded:
            font = QFont("B Titr", 10)
        else:
            font = QFont("Tahoma", 9)
            print("⚠️ از فونت پیش‌فرض Tahoma استفاده می‌شود")
        
        app.setFont(font)
        
        # بارگذاری استایل‌ها
        print("🎨 در حال بارگذاری استایل‌ها...")
        load_styles(app)
        
        # ایجاد کنترلر برنامه
        controller = ApplicationController(app)
        
        # نمایش preloader
        print("\n🎬 نمایش preloader...")
        controller.show_preloader()
        
        # اجرای برنامه
        print("🔄 شروع event loop...")
        exit_code = app.exec()
        
        print("👋 برنامه با موفقیت بسته شد")
        return exit_code
        
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")
        import traceback
        traceback.print_exc()
        
        # نمایش پیام خطا
        try:
            app = QApplication(sys.argv)
            QMessageBox.critical(
                None, 
                "خطای سیستمی", 
                f"خطای غیرمنتظره در اجرای برنامه:\n{str(e)}\n\nلطفاً با پشتیبانی تماس بگیرید."
            )
        except:
            pass
            
        input("برای خروج Enter را بفشارید...")
        return 1

if __name__ == "__main__":
    sys.exit(main())