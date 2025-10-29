from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QComboBox, QPushButton, QScrollArea, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QColor, QMouseEvent
import jdatetime
import sys
import os
from datetime import timedelta, datetime

# اضافه کردن مسیر models به sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'models'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from reservation_manager import ReservationManager
from models import Reservation, Guest, Room
from jalali import JalaliDate

class RoomCellWidget(QFrame):
    clicked = pyqtSignal(str, object)  # room_number, jalali_date
    
    def __init__(self, reservation_data=None, room_number=None, jalali_date=None):
        super().__init__()
        self.reservation_data = reservation_data
        self.room_number = room_number
        self.jalali_date = jalali_date
        
        self.setMinimumSize(120, 60)
        self.setMaximumSize(120, 60)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(1)
        
    def mousePressEvent(self, event: QMouseEvent):
        """هنگام کلیک روی سلول"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.room_number and self.jalali_date:
                # تشخیص اینکه کلیک روی کدام نیمه سلول بوده است
                click_x = event.pos().x()
                cell_width = self.width()
                
                # اگر سلول رزرو دارد و از نوع start یا end است
                if self.reservation_data and self.reservation_data.get('cell_type') in ['start', 'end']:
                    # اگر کلیک روی نیمه خالی باشد (برای start نیمه راست، برای end نیمه چپ)
                    if (self.reservation_data.get('cell_type') == 'start' and click_x > cell_width // 2) or \
                       (self.reservation_data.get('cell_type') == 'end' and click_x <= cell_width // 2):
                        # کلیک روی نیمه خالی - ثبت رزرو جدید
                        print(f"کلیک روی نیمه خالی - ثبت رزرو جدید برای اتاق {self.room_number}")
                        self.clicked.emit(self.room_number, self.jalali_date)
                    else:
                        # کلیک روی نیمه پر - ویرایش رزرو موجود
                        print(f"کلیک روی نیمه پر - ویرایش رزرو موجود در اتاق {self.room_number}")
                        self.clicked.emit(self.room_number, self.jalali_date)
                else:
                    # سلول کامل یا خالی - رفتار عادی
                    self.clicked.emit(self.room_number, self.jalali_date)
        super().mousePressEvent(event)
        
    def paintEvent(self, event):
        """رویداد رسم سلول"""
        if not self.isVisible() or self.width() <= 10 or self.height() <= 10:
            return
            
        painter = QPainter(self)
        if not painter.isActive():
            return
            
        try:
            width = self.width()
            height = self.height()
            
            if self.reservation_data:
                # رسم سلول رزرو با حالت‌های مختلف
                self.paint_reservation_cell(painter, width, height)
            else:
                # رسم سلول خالی
                self.paint_empty_cell(painter, width, height)
                
        except Exception as e:
            print(f"خطا در رسم سلول: {e}")
        finally:
            painter.end()
    
    def paint_reservation_cell(self, painter, width, height):
        """رسم سلول رزرو با حالت‌های مختلف برای Back-to-Back"""
        if not self.reservation_data:
            return
            
        cell_type = self.reservation_data.get('cell_type', 'full')
        color = self.get_reservation_color()
        
        # اصلاح: برای شروع رزرو نیمه چپ، برای پایان رزرو نیمه راست
        if cell_type == 'start':
            # نیمه چپ سلول (شروع رزرو)
            rect_x = 0
            rect_width = width // 2
            text_area = (0, 0, width // 2, height)
        elif cell_type == 'end':
            # نیمه راست سلول (پایان رزرو)
            rect_x = width // 2
            rect_width = width // 2
            text_area = (width // 2, 0, width // 2, height)
        else:  # middle, full
            # کل سلول
            rect_x = 0
            rect_width = width
            text_area = (0, 0, width, height)
        
        # رسم پس‌زمینه رنگی
        painter.fillRect(rect_x, 0, rect_width, height, QColor(color))
        
        # رسم border
        painter.setPen(QColor("#2c3e50"))
        painter.drawRect(0, 0, width - 1, height - 1)
        
        # خط جداکننده برای حالت‌های start و end
        if cell_type in ['start', 'end']:
            painter.setPen(QColor("#34495e"))
            painter.drawLine(width // 2, 0, width // 2, height)
        
        # نمایش اطلاعات فقط در حالت full یا middle
        if cell_type in ['full', 'middle']:
            self.draw_reservation_info(painter, text_area[0], text_area[1], text_area[2], text_area[3])
        elif cell_type == 'start':
            # در حالت start فلش به راست
            painter.setPen(QColor("white"))
            painter.setFont(QFont("Tahoma", 10, QFont.Weight.Bold))
            painter.drawText(5, height // 2 + 5, "→")
        elif cell_type == 'end':
            # در حالت end فلش به چپ
            painter.setPen(QColor("white"))
            painter.setFont(QFont("Tahoma", 10, QFont.Weight.Bold))
            painter.drawText(width - 15, height // 2 + 5, "←")
    
    def draw_reservation_info(self, painter, x, y, width, height):
        """رسم اطلاعات رزرو در محدوده مشخص"""
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Tahoma", 8, QFont.Weight.Bold))
        
        guest_name = self.reservation_data.get('guest_name', 'نامشخص')
        nights = self.reservation_data.get('nights', 0)
        package = self.reservation_data.get('package', 'فقط اسکان')
        
        # کوتاه کردن متن اگر طولانی است
        if len(guest_name) > 12:
            guest_name = guest_name[:12] + "..."
            
        # نمایش اطلاعات در سه خط
        line_height = height // 3
        
        # خط اول: نام مهمان و تعداد روزها
        name_text = f"{guest_name} | {nights} روز"
        if len(name_text) > 16:
            name_text = name_text[:16] + "..."
        
        # خط دوم: نوع پکیج
        package_text = package
        if len(package_text) > 14:
            package_text = package_text[:14] + "..."
        
        painter.drawText(x + 5, y + line_height - 5, name_text)
        painter.drawText(x + 5, y + line_height * 2 - 5, package_text)
    
    def paint_empty_cell(self, painter, width, height):
        """رسم سلول خالی"""
        # زمینه خاکستری روشن
        painter.fillRect(0, 0, width, height, QColor("#ECF0F1"))
        
        # border
        painter.setPen(QColor("#BDC3C7"))
        painter.drawRect(0, 0, width - 1, height - 1)
        
        # متن "خالی"
        painter.setPen(QColor("#7F8C8D"))
        painter.setFont(QFont("Tahoma", 9))
        painter.drawText(0, 0, width, height, Qt.AlignmentFlag.AlignCenter, "خالی")
    
    def get_reservation_color(self):
        """رنگ بر اساس نوع پکیج"""
        package = self.reservation_data.get('package', 'فقط اسکان')
        
        colors = {
            "فول برد": "#E74C3C",      # قرمز
            "اسکان + صبحانه": "#27AE60", # سبز
            "فقط اسکان": "#2980B9",    # آبی
            "پکیج ویژه": "#8E44AD"     # بنفش
        }
        
        return colors.get(package, "#2980B9")

class RackWidget(QWidget):
    cell_clicked = pyqtSignal(str, object)  # room_number, jalali_date
    
    def __init__(self):
        super().__init__()
        self.reservation_manager = ReservationManager()
        self.current_jalali_date = jdatetime.date.today()
        self.cell_widgets = []
        self.setup_ui()
        
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(200, self.load_rack_data)
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        header = self.create_header()
        layout.addLayout(header)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)
        
        self.setLayout(layout)
    
    def create_header(self):
        header_layout = QHBoxLayout()
        
        # کنترل‌های تاریخ
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("ماه:"))
        
        self.month_combo = QComboBox()
        months = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", 
                 "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
        for i, month in enumerate(months, 1):
            self.month_combo.addItem(month, i)
        
        self.month_combo.setCurrentIndex(self.current_jalali_date.month - 1)
        self.month_combo.currentIndexChanged.connect(self.on_date_changed)
        date_layout.addWidget(self.month_combo)
        
        self.year_combo = QComboBox()
        current_year = self.current_jalali_date.year
        for year in range(current_year - 1, current_year + 2):
            self.year_combo.addItem(str(year), year)
        
        self.year_combo.setCurrentText(str(current_year))
        self.year_combo.currentIndexChanged.connect(self.on_date_changed)
        date_layout.addWidget(self.year_combo)
        date_layout.addWidget(QLabel("سال:"))
        
        header_layout.addLayout(date_layout)
        header_layout.addStretch()
        
        # دکمه‌های ناوبری
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("ماه قبل")
        self.next_btn = QPushButton("ماه بعد")
        self.today_btn = QPushButton("امروز")
        
        self.prev_btn.clicked.connect(self.previous_month)
        self.next_btn.clicked.connect(self.next_month)
        self.today_btn.clicked.connect(self.go_to_today)
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.today_btn)
        nav_layout.addWidget(self.next_btn)
        
        header_layout.addLayout(nav_layout)
        
        return header_layout
    
    def on_date_changed(self):
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, self.load_rack_data)
    
    def load_rack_data(self):
        """بارگذاری داده‌های رک"""
        try:
            if not self.isVisible():
                return
                
            print("🔍 در حال بارگذاری رک...")
            
            self.cleanup_previous_widgets()
            
            main_widget = QWidget()
            main_layout = QVBoxLayout(main_widget)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(2)
            
            # ایجاد هدر روزهای ماه (فقط یک هدر)
            days_header = self.create_days_header()
            main_layout.addLayout(days_header)
            
            # ایجاد ردیف‌های اتاق‌ها
            self.create_room_rows(main_layout)
            
            self.scroll_area.setWidget(main_widget)
            
            print("✅ رک بارگذاری شد")
            
        except Exception as e:
            print(f"❌ خطا در بارگذاری رک: {e}")
    
    def cleanup_previous_widgets(self):
        """پاک کردن ویجت‌های قبلی"""
        for widget in self.cell_widgets:
            try:
                widget.setParent(None)
                widget.deleteLater()
            except:
                pass
        self.cell_widgets.clear()
    
    def create_days_header(self):
        """ایجاد هدر روزهای ماه - فقط یک هدر"""
        layout = QHBoxLayout()
        
        # سلول خالی برای ستون اتاق‌ها
        empty_label = QLabel("اتاق‌ها")
        empty_label.setMinimumSize(120, 30)
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label.setStyleSheet("""
            QLabel {
                background: #34495E;
                color: white;
                font-weight: bold;
                border: 1px solid #2C3E50;
                border-radius: 3px;
            }
        """)
        layout.addWidget(empty_label)
        
        year = self.year_combo.currentData()
        month = self.month_combo.currentData()
        days = self.get_days_in_month(year, month)
        
        # ایجاد هدر برای هر روز از ماه
        for day in range(1, days + 1):
            label = QLabel(str(day))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setMinimumSize(120, 30)
            label.setStyleSheet("""
                QLabel {
                    background: #2C3E50;
                    color: white;
                    font-weight: bold;
                    border: 1px solid #34495E;
                    border-radius: 3px;
                }
            """)
            layout.addWidget(label)
        
        layout.addStretch()
        return layout
    
    def create_room_rows(self, main_layout):
        """ایجاد ردیف‌های اتاق‌ها با پشتیبانی از Back-to-Back"""
        year = self.year_combo.currentData()
        month = self.month_combo.currentData()
        days = self.get_days_in_month(year, month)
        
        # ایجاد ردیف برای هر اتاق
        for room_idx in range(126):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(2)
            
            # اطلاعات اتاق
            room_number = self.get_room_number(room_idx)
            capacity = self.get_room_capacity(room_idx)
            room_label = QLabel(f"اتاق {room_number}\nظرفیت: {capacity}")
            room_label.setMinimumSize(120, 60)
            room_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            room_label.setStyleSheet("""
                QLabel {
                    background: #ECF0F1;
                    border: 1px solid #BDC3C7;
                    border-radius: 3px;
                    font-weight: bold;
                    padding: 5px;
                }
            """)
            row_layout.addWidget(room_label)
            
            # سلول‌های روزها
            for day in range(1, days + 1):
                date = jdatetime.date(year, month, day)
                cell_data = self.get_cell_data(room_idx + 1, date)
                
                cell = RoomCellWidget(
                    reservation_data=cell_data,
                    room_number=room_number,
                    jalali_date=date
                )
                cell.clicked.connect(self.on_cell_clicked)
                self.cell_widgets.append(cell)
                row_layout.addWidget(cell)
            
            row_layout.addStretch()
            main_layout.addLayout(row_layout)
    
    def on_cell_clicked(self, room_number, jalali_date):
        """هنگام کلیک روی سلول"""
        self.cell_clicked.emit(room_number, jalali_date)
    
    def get_room_number(self, idx):
        floor = (idx // 21) + 1
        room_num = (idx % 21) + 1
        return f"{floor}{room_num:02d}"
    
    def get_room_capacity(self, idx):
        session = self.reservation_manager.Session()
        try:
            room = session.query(Room).filter(Room.id == idx + 1).first()
            return room.capacity if room else 2
        except:
            return 2
        finally:
            session.close()
    
    def get_days_in_month(self, year, month):
        try:
            if month == 12:
                next_month = jdatetime.date(year + 1, 1, 1)
            else:
                next_month = jdatetime.date(year, month + 1, 1)
            return (next_month - jdatetime.timedelta(days=1)).day
        except:
            return 30
    
    def get_cell_data(self, room_id, jalali_date):
        """دریافت اطلاعات رزرو برای یک اتاق در تاریخ مشخص با پشتیبانی از Back-to-Back"""
        session = None
        try:
            gregorian_date = jalali_date.togregorian()
            
            # استفاده از reservation_manager برای ایجاد session
            session = self.reservation_manager.Session()
            
            from sqlalchemy import and_
            
            # پیدا کردن تمام رزروهای فعال برای این اتاق
            reservations = session.query(Reservation, Guest).join(
                Guest, and_(Reservation.guest_id == Guest.id)
            ).filter(
                Reservation.room_id == room_id,
                Reservation.status.in_(['confirmed', 'checked_in'])
            ).order_by(Reservation.check_in).all()  # مرتب‌سازی بر اساس تاریخ ورود
            
            # پیدا کردن رزروی که این تاریخ در بازه آن قرار دارد
            for res, guest in reservations:
                check_in_date = res.check_in.date()
                check_out_date = res.check_out.date()
                
                if check_in_date <= gregorian_date < check_out_date:
                    nights = (check_out_date - check_in_date).days
                    
                    # تعیین نوع سلول با منطق صحیح Back-to-Back
                    day_position = (gregorian_date - check_in_date).days
                    total_nights = nights
                    
                    # بررسی Back-to-Back احتمالی
                    has_previous_reservation = False
                    has_next_reservation = False
                    
                    # بررسی آیا رزرو قبلی در این تاریخ تمام می‌شود
                    for prev_res, prev_guest in reservations:
                        if prev_res.id != res.id and prev_res.check_out.date() == gregorian_date:
                            has_previous_reservation = True
                            break
                    
                    # بررسی آیا رزرو بعدی در این تاریخ شروع می‌شود
                    for next_res, next_guest in reservations:
                        if next_res.id != res.id and next_res.check_in.date() == gregorian_date:
                            has_next_reservation = True
                            break
                    
                    # منطق تعیین نوع سلول
                    if day_position == 0:  # اولین روز رزرو
                        if has_previous_reservation:
                            # اگر رزرو قبلی در این تاریخ تمام می‌شود - حالت start (نیمه راست)
                            cell_type = 'start'
                        else:
                            # روز اول و بدون رزرو قبلی - حالت full
                            cell_type = 'full'
                    elif gregorian_date == check_out_date - timedelta(days=1):  # آخرین روز رزرو
                        if has_next_reservation:
                            # اگر رزرو بعدی در این تاریخ شروع می‌شود - حالت end (نیمه چپ)
                            cell_type = 'end'
                        else:
                            # روز آخر و بدون رزرو بعدی - حالت full
                            cell_type = 'full'
                    else:
                        # روزهای میانی - حالت middle
                        cell_type = 'middle'
                    
                    print(f"🔍 اتاق {room_id} - تاریخ {jalali_date}:")
                    print(f"   رزرو: {check_in_date} تا {check_out_date}")
                    print(f"   موقعیت روز: {day_position}")
                    print(f"   نوع سلول: {cell_type}")
                    print(f"   رزرو قبلی: {has_previous_reservation}")
                    print(f"   رزرو بعدی: {has_next_reservation}")
                    
                    return {
                        'guest_name': f"{guest.first_name} {guest.last_name}",
                        'nights': nights,
                        'package': res.package_type,
                        'check_in': res.check_in,
                        'check_out': res.check_out,
                        'cell_type': cell_type,
                        'day_position': day_position,
                        'total_nights': nights,
                        'reservation_id': res.id
                    }
            
            return None
            
        except Exception as e:
            print(f"خطا در دریافت داده سلول: {e}")
            return None
        finally:
            if session:
                session.close()
    
    def previous_month(self):
        idx = self.month_combo.currentIndex()
        if idx > 0:
            self.month_combo.setCurrentIndex(idx - 1)
        else:
            self.month_combo.setCurrentIndex(11)
            year = int(self.year_combo.currentText()) - 1
            self.year_combo.setCurrentText(str(year))
    
    def next_month(self):
        idx = self.month_combo.currentIndex()
        if idx < 11:
            self.month_combo.setCurrentIndex(idx + 1)
        else:
            self.month_combo.setCurrentIndex(0)
            year = int(self.year_combo.currentText()) + 1
            self.year_combo.setCurrentText(str(year))
    
    def go_to_today(self):
        today = jdatetime.date.today()
        self.month_combo.setCurrentIndex(today.month - 1)
        self.year_combo.setCurrentText(str(today.year))