import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

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

def main():
    """تابع اصلی اجرای برنامه"""
    try:
        print("🚀 راه‌اندازی برنامه...")
        
        # ایجاد برنامه
        app = QApplication(sys.argv)
        
        # بارگذاری استایل‌ها
        current_dir = os.path.dirname(os.path.abspath(__file__))
        style_path = os.path.join(current_dir, 'ui', 'styles', 'style.qss')
        if os.path.exists(style_path):
            try:
                with open(style_path, 'r', encoding='utf-8') as f:
                    app.setStyleSheet(f.read())
                print("🎨 استایل‌ها بارگذاری شد")
            except Exception as e:
                print(f"⚠️ خطا در بارگذاری استایل: {e}")
        else:
            print("⚠️ فایل استایل یافت نشد")
        
        # تنظیم فونت برای پشتیبانی از فارسی
        font = QFont("Tahoma", 9)
        app.setFont(font)
        
        # اضافه کردن مسیرها به sys.path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.append(current_dir)
        sys.path.append(os.path.join(current_dir, 'models'))
        sys.path.append(os.path.join(current_dir, 'ui'))
        sys.path.append(os.path.join(current_dir, 'utils'))
        
        print("📁 مسیرها به sys.path اضافه شد")
        
        # import پنجره اصلی
        from ui.main_window import MainWindow
        
        # ایجاد و نمایش پنجره اصلی
        print("🖥️ در حال ایجاد پنجره اصلی...")
        window = MainWindow()
        window.show()
        print("✅ برنامه با موفقیت راه‌اندازی شد")
        
        # اجرای برنامه
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ خطا در اجرای برنامه: {e}")
        import traceback
        traceback.print_exc()
        input("برای خروج Enter را بفشارید...")

if __name__ == "__main__":
    print("=" * 50)
    print("🏨 سیستم مدیریت رزرواسیون هتل آراد")
    print("=" * 50)
    
    # راه‌اندازی پایگاه داده
    if init_database():
        print("\n" + "=" * 50)
        # تست ماندگاری داده‌ها
        test_database_persistence()
        print("=" * 50)
        main()
    else:
        print("❌ برنامه به دلیل خطا متوقف شد.")
        input("برای خروج Enter را بفشارید...")