from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QTableWidget, QTableWidgetItem, QTabWidget,
                            QHeaderView, QPushButton, QLineEdit, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QBrush
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'models'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from reservation_manager import ReservationManager
from models import Guest, Reservation, Room
from jalali import JalaliDate

class GuestsTab(QWidget):
    def __init__(self, reservation_manager):
        super().__init__()
        self.reservation_manager = reservation_manager
        self.setup_ui()
        self.load_guests_data()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # عنوان
        title_label = QLabel("👥 مدیریت مهمانان")
        title_label.setFont(QFont("Tahoma", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("padding: 20px; color: #2c3e50;")
        layout.addWidget(title_label)
        
        # نوار جستجو و فیلتر
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("جستجو بر اساس نام، تلفن یا ایمیل...")
        self.search_input.textChanged.connect(self.filter_guests)
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["همه", "مهمانان فعال", "مهمانان خروجی", "دارای رزرو"])
        self.status_filter.currentTextChanged.connect(self.filter_guests)
        
        search_layout.addWidget(QLabel("وضعیت:"))
        search_layout.addWidget(self.status_filter)
        search_layout.addStretch()
        search_layout.addWidget(self.search_input)
        
        layout.addLayout(search_layout)
        
        # تب‌های مهمانان
        self.tabs = QTabWidget()
        
        # تب همه مهمانان
        self.all_guests_tab = self.create_guests_table()
        self.tabs.addTab(self.all_guests_tab, "همه مهمانان")
        
        # تب مهمانان فعال
        self.active_guests_tab = self.create_guests_table()
        self.tabs.addTab(self.active_guests_tab, "مهمانان فعال")
        
        # تب مهمانان خروجی
        self.checked_out_tab = self.create_guests_table()
        self.tabs.addTab(self.checked_out_tab, "مهمانان خروجی")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)
    
    def create_guests_table(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        headers = ["نام", "نام خانوادگی", "تلفن", "ایمیل", "تاریخ آخرین رزرو", 
                  "اتاق فعلی", "وضعیت", "نوع مهمان"]
        self.table.setHorizontalHeaderLabels(headers)
        
        # تنظیمات جدول
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.table)
        return container
    
    def load_guests_data(self):
        session = self.reservation_manager.Session()
        try:
            # دریافت همه مهمانان
            guests = session.query(Guest).all()
            
            # پر کردن تب همه مهمانان
            self.fill_guests_table(self.all_guests_tab.layout().itemAt(0).widget(), guests)
            
            # پر کردن تب مهمانان فعال
            active_guests = self.get_active_guests(session)
            self.fill_guests_table(self.active_guests_tab.layout().itemAt(0).widget(), active_guests)
            
            # پر کردن تب مهمانان خروجی
            checked_out_guests = self.get_checked_out_guests(session)
            self.fill_guests_table(self.checked_out_tab.layout().itemAt(0).widget(), checked_out_guests)
            
        except Exception as e:
            print(f"خطا در بارگذاری داده مهمانان: {e}")
        finally:
            session.close()
    
    def get_active_guests(self, session):
        """دریافت مهمانان فعال"""
        active_reservations = session.query(Reservation).filter(
            Reservation.status == 'checked_in'
        ).all()
        
        guest_ids = [res.guest_id for res in active_reservations]
        return session.query(Guest).filter(Guest.id.in_(guest_ids)).all() if guest_ids else []
    
    def get_checked_out_guests(self, session):
        """دریافت مهمانان خروجی"""
        checked_out_reservations = session.query(Reservation).filter(
            Reservation.status == 'checked_out'
        ).all()
        
        guest_ids = [res.guest_id for res in checked_out_reservations]
        return session.query(Guest).filter(Guest.id.in_(guest_ids)).all() if guest_ids else []
    
    def fill_guests_table(self, table, guests):
        """پر کردن جدول مهمانان"""
        table.setRowCount(len(guests))
        
        session = self.reservation_manager.Session()
        try:
            for row, guest in enumerate(guests):
                # دریافت آخرین رزرو
                last_reservation = session.query(Reservation).filter(
                    Reservation.guest_id == guest.id
                ).order_by(Reservation.check_in.desc()).first()
                
                # دریافت رزرو فعال
                active_reservation = session.query(Reservation).filter(
                    Reservation.guest_id == guest.id,
                    Reservation.status == 'checked_in'
                ).first()
                
                # پر کردن ردیف
                table.setItem(row, 0, QTableWidgetItem(guest.first_name))
                table.setItem(row, 1, QTableWidgetItem(guest.last_name))
                table.setItem(row, 2, QTableWidgetItem(guest.phone or ""))
                table.setItem(row, 3, QTableWidgetItem(guest.email or ""))
                
                # تاریخ آخرین رزرو
                last_res_date = ""
                if last_reservation:
                    last_res_date = JalaliDate.format_date(last_reservation.check_in, "%Y/%m/%d")
                table.setItem(row, 4, QTableWidgetItem(last_res_date))
                
                # اتاق فعلی
                current_room = ""
                if active_reservation:
                    room = session.query(Room).filter(Room.id == active_reservation.room_id).first()
                    current_room = room.room_number if room else ""
                table.setItem(row, 5, QTableWidgetItem(current_room))
                
                # وضعیت
                status = "فعال" if active_reservation else "خروجی"
                status_item = QTableWidgetItem(status)
                if active_reservation:
                    status_item.setBackground(QBrush(QColor("#d4edda")))  # سبز
                else:
                    status_item.setBackground(QBrush(QColor("#f8d7da")))  # قرمز
                table.setItem(row, 6, status_item)
                
                # نوع مهمان
                guest_type = last_reservation.guest_type if last_reservation else "نامشخص"
                table.setItem(row, 7, QTableWidgetItem(guest_type))
                
        except Exception as e:
            print(f"خطا در پر کردن جدول: {e}")
        finally:
            session.close()
    
    def filter_guests(self):
        """فیلتر کردن مهمانان بر اساس جستجو"""
        search_text = self.search_input.text().lower()
        status_filter = self.status_filter.currentText()
        
        # این تابع می‌تواند برای فیلتر کردن real-time گسترش یابد
        pass