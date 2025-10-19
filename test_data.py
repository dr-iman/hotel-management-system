import sys
import os

# اضافه کردن مسیر ریشه پروژه
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# اضافه کردن مسیر models
sys.path.append(os.path.join(project_root, 'models'))

try:
    from reservation_manager import ReservationManager
    print("✅ reservation_manager import شد")
except ImportError as e:
    print(f"❌ خطا در import reservation_manager: {e}")
    # راه حل جایگزین
    import importlib.util
    spec = importlib.util.spec_from_file_location("reservation_manager", os.path.join(project_root, "reservation_manager.py"))
    reservation_manager = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reservation_manager)
    ReservationManager = reservation_manager.ReservationManager
    print("✅ reservation_manager با روش جایگزین import شد")

try:
    from models.models import Reservation, Guest, Room
    print("✅ models import شد")
except ImportError as e:
    print(f"❌ خطا در import models: {e}")
    # راه حل جایگزین
    import importlib.util
    spec = importlib.util.spec_from_file_location("models", os.path.join(project_root, "models", "models.py"))
    models = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(models)
    Reservation = models.Reservation
    Guest = models.Guest
    Room = models.Room
    print("✅ models با روش جایگزین import شد")

from datetime import datetime, timedelta
import jdatetime

def test_database_operations():
    """تست عملیات دیتابیس"""
    print("🔍 شروع تست دیتابیس...")
    
    manager = ReservationManager()
    
    # تست ۱: بررسی اتصال به دیتابیس
    print("\n1. بررسی اتصال به دیتابیس...")
    db_path = os.path.join(project_root, 'database', 'hotel.db')
    print(f"📁 مسیر دیتابیس: {db_path}")
    print(f"📊 وجود فایل: {os.path.exists(db_path)}")
    
    if not os.path.exists(db_path):
        print("❌ فایل دیتابیس وجود ندارد! ایجاد دیتابیس جدید...")
        manager.create_tables()
    
    # تست ۲: بررسی جداول
    print("\n2. بررسی جداول...")
    session = manager.Session()
    try:
        # بررسی وجود جدول رزروها
        reservations_count = session.query(Reservation).count()
        guests_count = session.query(Guest).count()
        rooms_count = session.query(Room).count()
        
        print(f"📊 تعداد رزروها: {reservations_count}")
        print(f"📊 تعداد مهمانان: {guests_count}")
        print(f"📊 تعداد اتاق‌ها: {rooms_count}")
        
        # نمایش ۵ رزرو آخر
        recent_reservations = session.query(Reservation).order_by(Reservation.id.desc()).limit(5).all()
        print(f"\n📋 ۵ رزرو آخر:")
        for res in recent_reservations:
            guest = session.query(Guest).filter(Guest.id == res.guest_id).first()
            room = session.query(Room).filter(Room.id == res.room_id).first()
            guest_name = f"{guest.first_name} {guest.last_name}" if guest else "نامشخص"
            room_number = room.room_number if room else "نامشخص"
            print(f"  - رزرو {res.id}: {guest_name} در اتاق {room_number} - {res.check_in} تا {res.check_out}")
            
    except Exception as e:
        print(f"❌ خطا در بررسی جداول: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
    
    # تست ۳: ایجاد رزرو تستی
    print("\n3. ایجاد رزرو تستی...")
    try:
        # پیدا کردن یک اتاق فعال
        session = manager.Session()
        available_room = session.query(Room).filter(Room.is_active == True).first()
        
        if available_room:
            print(f"🏨 اتاق پیدا شد: {available_room.room_number}")
            
            # داده‌های تست
            guest_data = {
                'first_name': 'تست',
                'last_name': 'کاربر',
                'phone': '09123456789',
                'email': 'test@example.com',
                'nationality': 'ایرانی'
            }
            
            reservation_data = {
                'room_id': available_room.id,
                'check_in': datetime.now(),
                'check_out': datetime.now() + timedelta(days=2),
                'status': 'confirmed',
                'adults': 2,
                'children': 0,
                'total_amount': 500000,
                'paid_amount': 0,
                'package_type': 'فقط اسکان',
                'guest_type': 'حضوری'
            }
            
            success, message, reservation_id = manager.create_reservation(
                reservation_data, 
                guest_data, 
                changed_by="تست سیستم"
            )
            
            if success:
                print(f"✅ رزرو تستی ایجاد شد: {reservation_id}")
                print(f"📝 پیام: {message}")
                
                # تأیید ذخیره‌سازی
                session = manager.Session()
                saved_reservation = session.query(Reservation).filter(Reservation.id == reservation_id).first()
                if saved_reservation:
                    print(f"✅ رزرو در دیتابیس پیدا شد: {saved_reservation.id}")
                else:
                    print("❌ رزرو در دیتابیس پیدا نشد!")
                session.close()
            else:
                print(f"❌ خطا در ایجاد رزرو: {message}")
        else:
            print("❌ هیچ اتاق فعالی پیدا نشد")
            
    except Exception as e:
        print(f"❌ خطا در ایجاد رزرو تستی: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'session' in locals():
            session.close()
    
    # تست ۴: بررسی مجدد رزروها
    print("\n4. بررسی مجدد رزروها...")
    session = manager.Session()
    try:
        new_count = session.query(Reservation).count()
        print(f"📊 تعداد رزروها بعد از تست: {new_count}")
        
        if new_count > reservations_count:
            print("✅ رزرو تستی با موفقیت ذخیره شد")
        else:
            print("❌ رزرو تستی ذخیره نشد!")
            
    except Exception as e:
        print(f"❌ خطا در بررسی مجدد: {e}")
    finally:
        session.close()

def check_database_file():
    """بررسی فایل دیتابیس"""
    print("\n🔍 بررسی فایل دیتابیس...")
    
    db_path = os.path.join(project_root, 'database', 'hotel.db')
    database_dir = os.path.join(project_root, 'database')
    
    # بررسی وجود پوشه database
    if not os.path.exists(database_dir):
        print("❌ پوشه database وجود ندارد! ایجاد پوشه...")
        os.makedirs(database_dir)
    
    # بررسی وجود فایل
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print(f"📁 دیتابیس اصلی: {size} بایت")
        
        # ایجاد backup
        import shutil
        backup_path = os.path.join(project_root, 'database', 'hotel_backup.db')
        shutil.copy2(db_path, backup_path)
        print(f"📁 بکاپ ایجاد شد: {backup_path}")
        
        # محتوای پوشه database
        print(f"📁 محتوای پوشه database: {os.listdir(database_dir)}")
    else:
        print("❌ فایل دیتابیس وجود ندارد!")
        print(f"📁 محتوای پوشه database: {os.listdir(database_dir) if os.path.exists(database_dir) else 'پوشه وجود ندارد'}")

def test_reservation_persistence():
    """تست ماندگاری رزروها بعد از بستن برنامه"""
    print("\n🔍 تست ماندگاری رزروها...")
    
    # ایجاد manager اول
    manager1 = ReservationManager()
    session1 = manager1.Session()
    
    try:
        # تعداد رزروهای فعلی
        initial_count = session1.query(Reservation).count()
        print(f"📊 تعداد رزروهای اولیه: {initial_count}")
        
        # ایجاد رزرو جدید
        available_room = session1.query(Room).filter(Room.is_active == True).first()
        if available_room:
            guest_data = {
                'first_name': 'تست',
                'last_name': 'ماندگاری',
                'phone': '09120000000',
                'email': 'persistence@test.com',
                'nationality': 'ایرانی'
            }
            
            reservation_data = {
                'room_id': available_room.id,
                'check_in': datetime.now(),
                'check_out': datetime.now() + timedelta(days=1),
                'status': 'confirmed',
                'adults': 1,
                'children': 0,
                'total_amount': 250000,
                'paid_amount': 0,
                'package_type': 'فقط اسکان',
                'guest_type': 'حضوری'
            }
            
            success, message, reservation_id = manager1.create_reservation(reservation_data, guest_data, "تست ماندگاری")
            
            if success:
                print(f"✅ رزرو ماندگاری ایجاد شد: {reservation_id}")
                
                # کامیت و بستن session اول
                session1.commit()
                session1.close()
                
                # ایجاد manager جدید (شبیه‌سازی بستن و باز کردن برنامه)
                print("🔄 شبیه‌سازی بستن و باز کردن برنامه...")
                manager2 = ReservationManager()
                session2 = manager2.Session()
                
                # بررسی وجود رزرو
                persisted_reservation = session2.query(Reservation).filter(Reservation.id == reservation_id).first()
                if persisted_reservation:
                    print(f"✅ رزرو بعد از باز کردن برنامه پیدا شد: {persisted_reservation.id}")
                    guest = session2.query(Guest).filter(Guest.id == persisted_reservation.guest_id).first()
                    print(f"📋 اطلاعات رزرو: {guest.first_name} {guest.last_name} - اتاق {available_room.room_number}")
                else:
                    print("❌ رزرو بعد از باز کردن برنامه پیدا نشد!")
                
                session2.close()
            else:
                print(f"❌ خطا در ایجاد رزرو ماندگاری: {message}")
        else:
            print("❌ هیچ اتاق فعالی برای تست پیدا نشد")
            
    except Exception as e:
        print(f"❌ خطا در تست ماندگاری: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if not session1.closed:
            session1.close()

if __name__ == "__main__":
    print("🎯 تست سیستم ذخیره‌سازی رزروها")
    print("=" * 50)
    
    check_database_file()
    test_database_operations()
    test_reservation_persistence()
    
    print("\n" + "=" * 50)
    print("✅ تست کامل شد")
    
    input("برای خروج Enter بزنید...")