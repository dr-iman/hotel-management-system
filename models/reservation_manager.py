from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os
import sys

# اضافه کردن مسیر جاری به sys.path
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(current_dir)

from models.models import Base, Room, Guest, Reservation

class ReservationManager:
    def __init__(self):
        # مسیر پایگاه داده
        db_path = os.path.join(current_dir, 'database', 'hotel.db')
        db_url = f"sqlite:///{db_path}"
        
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
    
    def get_suggested_rooms(self, check_in, check_out, capacity):
        """دریافت اتاق‌های پیشنهادی با ظرفیت مناسب"""
        session = self.Session()
        try:
            suitable_rooms = session.query(Room).filter(
                Room.is_active == True,
                Room.capacity >= capacity
            ).all()
            
            available_rooms = []
            for room in suitable_rooms:
                if self.is_room_available(room.id, check_in, check_out):
                    available_rooms.append(room)
            
            return available_rooms
            
        except Exception as e:
            print(f"خطا در دریافت اتاق‌های پیشنهادی: {e}")
            return []
        finally:
            session.close()
    
    def get_room_conflicts(self, room_id, check_in, check_out):
        """دریافت رزروهای متضاد برای یک اتاق"""
        session = self.Session()
        try:
            conflicts = session.query(Reservation, Guest).join(
                Guest, and_(Reservation.guest_id == Guest.id)
            ).filter(
                Reservation.room_id == room_id,
                Reservation.status.in_(['confirmed', 'checked_in']),
                or_(
                    and_(Reservation.check_in < check_out, Reservation.check_out > check_in)
                )
            ).all()
            
            conflict_info = []
            for reservation, guest in conflicts:
                conflict_info.append({
                    'guest_name': f"{guest.first_name} {guest.last_name}",
                    'check_in': reservation.check_in,
                    'check_out': reservation.check_out,
                    'status': reservation.status
                })
            
            return conflict_info
            
        except Exception as e:
            print(f"خطا در دریافت تضادها: {e}")
            return []
        finally:
            session.close()
    
    def get_reservation_for_date(self, room_id, date):
        """دریافت رزرو برای یک اتاق در تاریخ مشخص"""
        session = self.Session()
        try:
            from sqlalchemy import and_
            
            reservation = session.query(Reservation, Guest).join(
                Guest, 
                and_(Reservation.guest_id == Guest.id)
            ).filter(
                Reservation.room_id == room_id,
                Reservation.check_in <= date,
                Reservation.check_out > date,
                Reservation.status.in_(['confirmed', 'checked_in'])
            ).first()
            
            return reservation
        except Exception as e:
            print(f"خطا در دریافت رزرو: {e}")
            return None
        finally:
            session.close()
    
    def search_reservations(self, search_text):
        """جستجو بر اساس نام مهمان یا شماره اتاق"""
        session = self.Session()
        
        try:
            from sqlalchemy import and_
            
            # جستجو در مهمانان
            guest_results = session.query(Reservation, Guest).join(
                Guest, and_(Reservation.guest_id == Guest.id)
            ).filter(
                or_(
                    Guest.first_name.ilike(f"%{search_text}%"),
                    Guest.last_name.ilike(f"%{search_text}%")
                )
            ).all()
            
            # جستجو در اتاق‌ها
            room_results = session.query(Reservation, Room).join(
                Room, and_(Reservation.room_id == Room.id)
            ).filter(
                Room.room_number.ilike(f"%{search_text}%")
            ).all()
            
            # ترکیب نتایج
            all_results = list(set([r[0] for r in guest_results] + [r[0] for r in room_results]))
            return all_results
            
        except Exception as e:
            print(f"خطا در جستجو: {e}")
            return []
        finally:
            session.close()
    
    def is_room_available(self, room_id, check_in, check_out):
        """بررسی موجود بودن اتاق در بازه زمانی مشخص"""
        session = self.Session()
        
        try:
            conflicting_reservations = session.query(Reservation).filter(
                Reservation.room_id == room_id,
                Reservation.status.in_(['confirmed', 'checked_in']),
                or_(
                    and_(Reservation.check_in < check_out, Reservation.check_out > check_in)
                )
            ).all()
            
            return len(conflicting_reservations) == 0
        finally:
            session.close()
    
    def get_room_status(self, room_id, date):
        """دریافت وضعیت اتاق در تاریخ مشخص"""
        session = self.Session()
        
        try:
            reservation = session.query(Reservation).filter(
                Reservation.room_id == room_id,
                Reservation.check_in <= date,
                Reservation.check_out > date,
                Reservation.status.in_(['confirmed', 'checked_in'])
            ).first()
            
            return reservation.status if reservation else 'vacant'
        finally:
            session.close()
    
    def get_daily_occupancy(self, date):
        """دریافت آمار اشغال روزانه"""
        session = self.Session()
        
        try:
            total_rooms = session.query(Room).filter(Room.is_active == True).count()
            occupied_rooms = session.query(Reservation).filter(
                Reservation.check_in <= date,
                Reservation.check_out > date,
                Reservation.status.in_(['confirmed', 'checked_in'])
            ).count()
            
            return {
                'total_rooms': total_rooms,
                'occupied_rooms': occupied_rooms,
                'occupancy_rate': (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0
            }
        finally:
            session.close()
    
    def get_todays_arrivals(self):
        """دریافت تعداد ورودی‌های امروز"""
        session = self.Session()
        today = datetime.now().date()
        
        try:
            arrivals = session.query(Reservation).filter(
                Reservation.check_in <= today,
                Reservation.check_out > today,
                Reservation.status == 'confirmed'
            ).count()
            
            return arrivals
        finally:
            session.close()
    
    def get_todays_departures(self):
        """دریافت تعداد خروجی‌های امروز"""
        session = self.Session()
        today = datetime.now().date()
        
        try:
            departures = session.query(Reservation).filter(
                Reservation.check_out == today,
                Reservation.status == 'checked_in'
            ).count()
            
            return departures
        finally:
            session.close()