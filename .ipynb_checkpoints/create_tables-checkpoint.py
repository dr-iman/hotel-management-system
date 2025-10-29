import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from models.models import Base, Room, Guest, Reservation, SystemLog, Agency
from sqlalchemy import create_engine

def create_all_tables():
    """ایجاد تمام جداول در دیتابیس"""
    try:
        db_path = os.path.join(project_root, 'database', 'hotel.db')
        db_url = f"sqlite:///{db_path}"
        
        engine = create_engine(db_url)
        Base.metadata.create_all(engine)
        print("✅ تمام جداول با موفقیت ایجاد شدند")
        
        # تست اتصال
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # تست شمارش
        room_count = session.query(Room).count()
        agency_count = session.query(Agency).count()
        log_count = session.query(SystemLog).count()
        
        print(f"📊 تعداد اتاق‌ها: {room_count}")
        print(f"📊 تعداد آژانس‌ها: {agency_count}")
        print(f"📊 تعداد لاگ‌ها: {log_count}")
        
        session.close()
        print("🎯 سیستم آماده است!")
        
    except Exception as e:
        print(f"❌ خطا در ایجاد جداول: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_all_tables()