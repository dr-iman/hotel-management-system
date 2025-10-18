import sys
import os

# اضافه کردن مسیرها به sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, 'models'))

from models.models import Reservation, Guest, Room
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def test_data():
    """تست وجود داده‌ها در پایگاه داده"""
    db_path = os.path.join(current_dir, 'database', 'hotel.db')
    db_url = f"sqlite:///{db_path}"
    
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # شمارش داده‌ها
        room_count = session.query(Room).count()
        guest_count = session.query(Guest).count()
        reservation_count = session.query(Reservation).count()
        
        print(f"📊 آمار پایگاه داده:")
        print(f"   - تعداد اتاق‌ها: {room_count}")
        print(f"   - تعداد مهمانان: {guest_count}")
        print(f"   - تعداد رزرواسیون‌ها: {reservation_count}")
        
        # نمایش چند رزرو نمونه
        print(f"\n📅 نمونه رزروها:")
        reservations = session.query(Reservation).limit(5).all()
        for res in reservations:
            guest = session.query(Guest).filter(Guest.id == res.guest_id).first()
            room = session.query(Room).filter(Room.id == res.room_id).first()
            if guest and room:
                print(f"   - {guest.first_name} {guest.last_name} در اتاق {room.room_number} از {res.check_in} تا {res.check_out}")
                
    except Exception as e:
        print(f"❌ خطا در تست داده‌ها: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    test_data()