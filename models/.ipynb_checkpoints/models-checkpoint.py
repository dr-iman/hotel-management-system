from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float, Text, JSON, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class Agency(Base):
    __tablename__ = 'agencies'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    contact_person = Column(String(100))
    phone = Column(String(20))
    address = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<Agency({self.name})>"

class Room(Base):
    __tablename__ = 'rooms'
    
    id = Column(Integer, primary_key=True)
    room_number = Column(String(10), unique=True, nullable=False)
    room_type = Column(String(50), nullable=False)
    floor = Column(Integer, nullable=False)
    price_per_night = Column(Float, nullable=False)
    capacity = Column(Integer, nullable=False)
    max_guests = Column(Integer, nullable=False)
    amenities = Column(Text)
    is_active = Column(Boolean, default=True)
    status = Column(String(20), default="خالی")
    
    def __repr__(self):
        return f"<Room({self.room_number}, {self.room_type}, ظرفیت: {self.capacity})>"

class Guest(Base):
    __tablename__ = 'guests'
    
    id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    id_number = Column(String(50))
    nationality = Column(String(100), default="ایرانی")
    
    def __repr__(self):
        return f"<Guest({self.first_name} {self.last_name})>"

class Reservation(Base):
    __tablename__ = 'reservations'
    
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, nullable=False)
    guest_id = Column(Integer, nullable=False)
    check_in = Column(DateTime, nullable=False)
    check_out = Column(DateTime, nullable=False)
    check_in_time = Column(String(10), default="14:00")
    check_out_time = Column(String(10), default="12:00")
    is_half_charge = Column(Boolean, default=False)
    status = Column(String(20), nullable=False)
    adults = Column(Integer, default=1)
    children = Column(Integer, default=0)
    total_amount = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0)  # مبلغ پیش پرداخت
    package_type = Column(String(50), default="فقط اسکان")
    guest_type = Column(String(50), default="حضوری")
    agency_id = Column(Integer)  # آیدی آژانس در صورت انتخاب
    settlement_type = Column(String(50), default="تسویه با هتل")  # تسویه با آژانس، تسویه با هتل، تسویه شده
    tracking_code = Column(String(100))  # کد پیگیری واریزی
    receipt_file = Column(LargeBinary)  # فایل فیش پرداخت
    receipt_filename = Column(String(255))  # نام فایل فیش
    companion_type = Column(String(50), default="بزرگسال")
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<Reservation(Room: {self.room_id}, Guest: {self.guest_id})>"

class SystemLog(Base):
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True)
    action = Column(String(50), nullable=False)
    table_name = Column(String(50), nullable=False)
    record_id = Column(Integer, nullable=False)
    old_data = Column(JSON)
    new_data = Column(JSON)
    changed_by = Column(String(100), default="سیستم")
    changed_at = Column(DateTime, default=datetime.now)
    description = Column(Text)
    
    def __repr__(self):
        return f"<SystemLog({self.action} on {self.table_name}.{self.record_id})>"