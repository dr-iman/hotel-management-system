import sys
import os

# اضافه کردن مسیر ریشه پروژه
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from models.models import Base, Room, Guest, Reservation, SystemLog
from sqlalchemy import create_engine

def create_all_tables():
    """ایجاد تمام جداول در دیتابیس"""
    try:
        # مسیر پایگاه داده
        db_path = os.path.join(project_root, 'database', 'hotel.db')
        db_url = f"sqlite:///{db_path}"
        
        # ایجاد engine
        engine = create_engine(db_url)
        
        # ایجاد تمام جداول
        Base.metadata.create_all(engine)
        print("✅ تمام جداول با موفقیت ایجاد شدند")
        
        # تست اتصال
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # تست شمارش لاگ‌ها
        log_count = session.query(SystemLog).count()
        print(f"📊 تعداد لاگ‌های موجود: {log_count}")
        
        # اضافه کردن یک لاگ تست
        test_log = SystemLog(
            action="create",
            table_name="test",
            record_id=1,
            changed_by="سیستم",
            description="تست ایجاد جداول"
        )
        session.add(test_log)
        session.commit()
        
        log_count_after = session.query(SystemLog).count()
        print(f"📊 تعداد لاگ‌ها بعد از تست: {log_count_after}")
        
        session.close()
        print("🎉 سیستم لاگ‌گیری آماده است!")
        
    except Exception as e:
        print(f"❌ خطا در ایجاد جداول: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_all_tables()