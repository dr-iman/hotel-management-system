from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QGridLayout, QFrame, QTableWidget, QTableWidgetItem,
                            QHeaderView, QScrollArea)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QBrush
import sys
import os
import jdatetime
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'models'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from reservation_manager import ReservationManager
from models import Reservation, Room, Guest
from jalali import JalaliDate

class ReportsTab(QWidget):
    def __init__(self, reservation_manager):
        super().__init__()
        self.reservation_manager = reservation_manager
        self.setup_ui()
        self.load_reports_data()
    
    def setup_ui(self):
        # ایجاد scroll area اصلی
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # ویجت اصلی
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        
        # عنوان
        title_label = QLabel("📊 گزارشات و آمار هتل")
        title_label.setFont(QFont("B Titr", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("padding: 20px; color: #2c3e50;")
        layout.addWidget(title_label)
        
        # آمار فوری
        stats_layout = QGridLayout()
        
        # ایجاد کارت‌های آمار
        self.occupancy_card = self.create_stat_card("نرخ اشغال", "0%", "#3498db")
        self.active_guests_card = self.create_stat_card("مهمانان فعال", "0", "#2ecc71")
        self.vacant_rooms_card = self.create_stat_card("اتاق‌های خالی", "0", "#e74c3c")
        self.cleaned_rooms_card = self.create_stat_card("اتاق‌های نظافت شده", "0", "#f39c12")
        self.maintenance_rooms_card = self.create_stat_card("اتاق‌های خارج از سرویس", "0", "#9b59b6")
        self.cleaning_rooms_card = self.create_stat_card("اتاق‌های در حال نظافت", "0", "#1abc9c")
        self.total_reservations_card = self.create_stat_card("کل رزروها", "0", "#e67e22")
        self.monthly_revenue_card = self.create_stat_card("درآمد ماه", "0", "#27ae60")
        
        stats_layout.addWidget(self.occupancy_card, 0, 0)
        stats_layout.addWidget(self.active_guests_card, 0, 1)
        stats_layout.addWidget(self.vacant_rooms_card, 0, 2)
        stats_layout.addWidget(self.cleaned_rooms_card, 0, 3)
        stats_layout.addWidget(self.maintenance_rooms_card, 1, 0)
        stats_layout.addWidget(self.cleaning_rooms_card, 1, 1)
        stats_layout.addWidget(self.total_reservations_card, 1, 2)
        stats_layout.addWidget(self.monthly_revenue_card, 1, 3)
        
        layout.addLayout(stats_layout)
        
        # جدول آمار ماهانه
        table_label = QLabel("📈 آمار رزروهای ماهانه")
        table_label.setFont(QFont("B Titr", 14, QFont.Weight.Bold))
        table_label.setStyleSheet("padding: 15px; color: #2c3e50;")
        layout.addWidget(table_label)
        
        self.monthly_table = QTableWidget()
        self.monthly_table.setColumnCount(4)
        self.monthly_table.setHorizontalHeaderLabels(["ماه", "تعداد رزرو", "درآمد", "نرخ اشغال"])
        self.monthly_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.monthly_table.setMinimumHeight(200)
        layout.addWidget(self.monthly_table)
        
        # آمار انواع پکیج
        package_label = QLabel("📦 آمار انواع پکیج")
        package_label.setFont(QFont("B Titr", 14, QFont.Weight.Bold))
        package_label.setStyleSheet("padding: 15px; color: #2c3e50;")
        layout.addWidget(package_label)
        
        self.package_table = QTableWidget()
        self.package_table.setColumnCount(3)
        self.package_table.setHorizontalHeaderLabels(["نوع پکیج", "تعداد رزرو", "درآمد"])
        self.package_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.package_table.setMinimumHeight(150)
        layout.addWidget(self.package_table)
        
        layout.addStretch()
        
        # تنظیم ویجت اصلی برای scroll area
        scroll_area.setWidget(main_widget)
        
        # تنظیم layout اصلی
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.addWidget(scroll_area)
    
    def create_stat_card(self, title, value, color):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
            }}
            QLabel {{
                border: none;
            }}
        """)
        
        layout = QVBoxLayout()
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; color: #7f8c8d; font-size: 12px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        card.setLayout(layout)
        return card
    
    def load_reports_data(self):
        # آمار فعلی
        self.load_current_stats()
        
        # آمار ماهانه
        self.load_monthly_stats()
        
        # آمار پکیج‌ها
        self.load_package_stats()
    
    def load_current_stats(self):
        session = self.reservation_manager.Session()
        try:
            # آمار پایه
            total_rooms = session.query(Room).filter(Room.is_active == True).count()
            today = datetime.now().date()
            
            # اتاق‌های اشغال شده
            occupied_rooms = session.query(Reservation).filter(
                Reservation.check_in <= today,
                Reservation.check_out > today,
                Reservation.status.in_(['confirmed', 'checked_in'])
            ).count()
            
            # مهمانان فعال
            active_guests = session.query(Reservation).filter(
                Reservation.status == 'checked_in'
            ).count()
            
            # کل رزروها
            total_reservations = session.query(Reservation).count()
            
            # درآمد ماه جاری
            current_month_start = jdatetime.date.today().replace(day=1).togregorian()
            current_month_end = (jdatetime.date.today() + jdatetime.timedelta(days=31)).replace(day=1).togregorian()
            
            monthly_revenue = session.query(Reservation).filter(
                Reservation.check_in >= current_month_start,
                Reservation.check_in < current_month_end
            ).with_entities(Reservation.total_amount).all()
            
            total_monthly_revenue = sum([rev[0] for rev in monthly_revenue if rev[0]])
            
            # محاسبات
            occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0
            vacant_rooms = total_rooms - occupied_rooms
            
            # بروزرسانی کارت‌ها
            self.occupancy_card.layout().itemAt(1).widget().setText(f"{occupancy_rate:.1f}%")
            self.active_guests_card.layout().itemAt(1).widget().setText(str(active_guests))
            self.vacant_rooms_card.layout().itemAt(1).widget().setText(str(vacant_rooms))
            self.cleaned_rooms_card.layout().itemAt(1).widget().setText(str(vacant_rooms))
            self.maintenance_rooms_card.layout().itemAt(1).widget().setText("5")
            self.cleaning_rooms_card.layout().itemAt(1).widget().setText("3")
            self.total_reservations_card.layout().itemAt(1).widget().setText(str(total_reservations))
            self.monthly_revenue_card.layout().itemAt(1).widget().setText(f"{total_monthly_revenue:,.0f} تومان")
            
        except Exception as e:
            print(f"خطا در بارگذاری آمار: {e}")
        finally:
            session.close()
    
    def load_monthly_stats(self):
        session = self.reservation_manager.Session()
        try:
            # آمار 6 ماه گذشته و آینده
            monthly_stats = []
            current_jalali = jdatetime.date.today()
            
            for i in range(-2, 4):  # 2 ماه گذشته تا 3 ماه آینده
                month_date = current_jalali + jdatetime.timedelta(days=30*i)
                year = month_date.year
                month = month_date.month
                
                # محاسبه تاریخ‌های میلادی برای ماه شمسی
                start_date = jdatetime.date(year, month, 1).togregorian()
                if month == 12:
                    end_date = jdatetime.date(year + 1, 1, 1).togregorian()
                else:
                    end_date = jdatetime.date(year, month + 1, 1).togregorian()
                
                # تعداد رزروهای ماه
                monthly_reservations = session.query(Reservation).filter(
                    Reservation.check_in >= start_date,
                    Reservation.check_in < end_date
                ).count()
                
                # درآمد ماه
                monthly_revenue = session.query(Reservation).filter(
                    Reservation.check_in >= start_date,
                    Reservation.check_in < end_date
                ).with_entities(Reservation.total_amount).all()
                
                total_revenue = sum([rev[0] for rev in monthly_revenue if rev[0]])
                
                # نام ماه شمسی
                persian_months = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", 
                                 "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
                month_name = persian_months[month - 1]
                
                monthly_stats.append({
                    'month': f"{month_name} {year}",
                    'reservations': monthly_reservations,
                    'revenue': total_revenue,
                    'occupancy': (monthly_reservations / 30) * 3  # تخمین
                })
            
            # پر کردن جدول
            self.monthly_table.setRowCount(len(monthly_stats))
            for row, stat in enumerate(monthly_stats):
                self.monthly_table.setItem(row, 0, QTableWidgetItem(stat['month']))
                self.monthly_table.setItem(row, 1, QTableWidgetItem(str(stat['reservations'])))
                self.monthly_table.setItem(row, 2, QTableWidgetItem(f"{stat['revenue']:,.0f} تومان"))
                self.monthly_table.setItem(row, 3, QTableWidgetItem(f"{stat['occupancy']:.1f}%"))
                
        except Exception as e:
            print(f"خطا در بارگذاری آمار ماهانه: {e}")
        finally:
            session.close()
    
    def load_package_stats(self):
        """بارگذاری آمار انواع پکیج"""
        session = self.reservation_manager.Session()
        try:
            from sqlalchemy import func
            
            package_stats = session.query(
                Reservation.package_type,
                func.count(Reservation.id).label('count'),
                func.sum(Reservation.total_amount).label('revenue')
            ).group_by(Reservation.package_type).all()
            
            self.package_table.setRowCount(len(package_stats))
            for row, stat in enumerate(package_stats):
                self.package_table.setItem(row, 0, QTableWidgetItem(stat.package_type))
                self.package_table.setItem(row, 1, QTableWidgetItem(str(stat.count)))
                self.package_table.setItem(row, 2, QTableWidgetItem(f"{stat.revenue or 0:,.0f} تومان"))
                
        except Exception as e:
            print(f"خطا در بارگذاری آمار پکیج‌ها: {e}")
        finally:
            session.close()