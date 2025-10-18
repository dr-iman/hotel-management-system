from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Room(Base):
    __tablename__ = 'rooms'
    
    id = Column(Integer, primary_key=True)
    room_number = Column(String(10), unique=True, nullable=False)
    room_type = Column(String(50), nullable=False)
    floor = Column(Integer, nullable=False)
    price_per_night = Column(Float, nullable=False)
    capacity = Column(Integer, nullable=False)  # ظرفیت اتاق
    max_guests = Column(Integer, nullable=False)
    amenities = Column(Text)
    is_active = Column(Boolean, default=True)
    status = Column(String(20), default="خالی")  # خالی, اشغال, در حال نظافت, نظافت شده, خارج از سرویس
    
    def __repr__(self):
        return f"<Room({self.room_number}, {self.room_type}, ظرفیت: {self.capacity})>"

class Guest(Base):
    __tablename__ = 'guests'
    
    id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(150))
    phone = Column(String(20))
    id_number = Column(String(50))
    nationality = Column(String(100))
    
    def __repr__(self):
        return f"<Guest({self.first_name} {self.last_name})>"

class Reservation(Base):
    __tablename__ = 'reservations'
    
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, nullable=False)
    guest_id = Column(Integer, nullable=False)
    check_in = Column(DateTime, nullable=False)
    check_out = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False)  # confirmed, checked_in, checked_out, cancelled
    adults = Column(Integer, default=1)
    children = Column(Integer, default=0)
    total_amount = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0)
    package_type = Column(String(50), default="فقط اسکان")
    guest_type = Column(String(50), default="حضوری")  # حضوری, آژانس, رزرو, سایت, اینستاگرام
    companion_type = Column(String(50), default="بزرگسال")  # بزرگسال, کودک, خردسال
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<Reservation(Room: {self.room_id}, Guest: {self.guest_id})>"