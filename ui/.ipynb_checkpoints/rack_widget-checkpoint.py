from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QComboBox, QPushButton, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QColor, QMouseEvent
import jdatetime
import sys
import os

# اضافه کردن مسیر models به sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'models'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from reservation_manager import ReservationManager
from models import Reservation, Guest, Room
from jalali import JalaliDate

class RoomCellWidget(QWidget):
    clicked = pyqtSignal(str, object)  # room_number, jalali_date
    
    def __init__(self, reservation_data=None, room_number=None, jalali_date=None):
        super().__init__()
        self.reservation_data = reservation_data
        self.room_number = room_number
        self.jalali_date = jalali_date
        self.setMinimumSize(120, 60)
        
    def mousePressEvent(self, event: QMouseEvent):
        """هنگام کلیک روی سلول"""
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                if self.room_number and self.jalali_date:
                    self.clicked.emit(self.room_number, self.jalali_date)
            super().mousePressEvent(event)
        except RuntimeError:
            # اگر ویجت حذف شده باشد، خطا را نادیده بگیر
            pass
        
    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            
            if self.reservation_data:
                # بررسی اینکه آیا چندین رزرو داریم یا یک رزرو
                if self.reservation_data.get('multiple_reservations', False):
                    # نمایش چندین رزرو در یک سلول
                    self.paint_multiple_reservations(painter)
                else:
                    # نمایش یک رزرو
                    self.paint_single_reservation(painter)
            else:
                # اتاق خالی
                self.paint_empty_room(painter)
                
        except Exception as e:
            print(f"خطا در paintEvent: {e}")
            # در صورت خطا، سلول خالی رسم کن
            try:
                painter = QPainter(self)
                self.paint_empty_room(painter)
            except:
                pass
    
    def paint_single_reservation(self, painter):
        """رسم یک رزرو در سلول"""
        try:
            # رنگ‌های مختلف برای انواع پکیج
            package_colors = {
                "فول برد": "#FF6B6B",
                "اسکان + صبحانه": "#4ECDC4", 
                "فقط اسکان": "#45B7D1",
                "پکیج ویژه": "#96CEB4"
            }
            
            color = package_colors.get(self.reservation_data.get('package', 'فقط اسکان'), "#45B7D1")
            painter.fillRect(self.rect(), QColor(color))
            
            # رسم border
            painter.setPen(QColor("#2c3e50"))
            painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
            
            # نوشتن اطلاعات
            painter.setPen(QColor("white"))
            painter.setFont(QFont("Tahoma", 8))
            
            # نام مهمان
            guest_name = self.reservation_data.get('guest_name', 'نامشخص')
            if len(guest_name) > 12:
                guest_name = guest_name[:12] + "..."
            painter.drawText(5, 15, guest_name)
            
            # روزهای اقامت
            nights = self.reservation_data.get('nights', 0)
            painter.drawText(5, 30, f"{nights} شب")
            
            # نوع پکیج
            package = self.reservation_data.get('package', 'فقط اسکان')
            if len(package) > 10:
                package = package[:10] + "..."
            painter.drawText(5, 45, package)
        except Exception as e:
            print(f"خطا در paint_single_reservation: {e}")
    
    def paint_multiple_reservations(self, painter):
        """رسم چندین رزرو در یک سلول"""
        try:
            # رنگ زمینه برای رزروهای متعدد
            painter.fillRect(self.rect(), QColor("#FFA500"))  # نارنجی
            
            # رسم border
            painter.setPen(QColor("#2c3e50"))
            painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
            
            # نوشتن اطلاعات
            painter.setPen(QColor("white"))
            painter.setFont(QFont("Tahoma", 8))
            
            # نمایش تعداد رزروها
            reservations_count = len(self.reservation_data.get('reservations', []))
            painter.drawText(5, 15, f"{reservations_count} رزرو")
            painter.drawText(5, 30, "هم‌پوشانی")
            painter.drawText(5, 45, "روز")
        except Exception as e:
            print(f"خطا در paint_multiple_reservations: {e}")
    
    def paint_empty_room(self, painter):
        """رسم سلول خالی"""
        try:
            painter.fillRect(self.rect(), QColor("#ECF0F1"))
            painter.setPen(QColor("#7f8c8d"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "خالی")
        except Exception as e:
            print(f"خطا در paint_empty_room: {e}")

class RackWidget(QWidget):
    cell_clicked = pyqtSignal(str, object)  # room_number, jalali_date
    
    def __init__(self):
        super().__init__()
        try:
            self.reservation_manager = ReservationManager()
            self.current_jalali_date = jdatetime.date.today()
            self.cell_widgets = []  # لیست برای نگهداری reference ویجت‌ها
            self.setup_ui()
            self.load_rack_data()
        except Exception as e:
            print(f"خطا در ایجاد RackWidget: {e}")
    
    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # راست‌چین کردن
        main_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # هدر فشرده
        header_layout = self.create_compact_header()
        main_layout.addLayout(header_layout)
        
        # پیغام در حال بارگذاری
        self.loading_label = QLabel("در حال بارگذاری رک...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("font-size: 16px; color: #7f8c8d; padding: 20px;")
        main_layout.addWidget(self.loading_label)
        
        self.setLayout(main_layout)
    
    def create_compact_header(self):
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # کنترل ماه شمسی
        month_layout = QHBoxLayout()
        month_layout.addWidget(QLabel("ماه:"))
        
        self.month_combo = QComboBox()
        persian_months = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", 
                         "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
        for i, month in enumerate(persian_months, 1):
            self.month_combo.addItem(month, i)
        
        self.month_combo.setCurrentIndex(self.current_jalali_date.month - 1)
        self.month_combo.currentIndexChanged.connect(self.load_rack_data)
        month_layout.addWidget(self.month_combo)
        
        # کنترل سال شمسی
        self.year_combo = QComboBox()
        current_year = self.current_jalali_date.year
        for year in range(current_year - 1, current_year + 2):
            self.year_combo.addItem(str(year), year)
        
        self.year_combo.setCurrentText(str(current_year))
        self.year_combo.currentIndexChanged.connect(self.load_rack_data)
        month_layout.addWidget(self.year_combo)
        month_layout.addWidget(QLabel("سال:"))
        
        header_layout.addLayout(month_layout)
        header_layout.addStretch()
        
        # دکمه‌های ناوبری فشرده
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("◀ ماه قبل")
        self.next_btn = QPushButton("ماه بعد ▶")
        self.today_btn = QPushButton("امروز")
        
        self.prev_btn.clicked.connect(self.previous_month)
        self.next_btn.clicked.connect(self.next_month)
        self.today_btn.clicked.connect(self.go_to_today)
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.today_btn)
        nav_layout.addWidget(self.next_btn)
        
        header_layout.addLayout(nav_layout)
        
        return header_layout
    
    def get_days_in_month(self, year, month):
        """محاسبه تعداد روزهای ماه شمسی"""
        try:
            # ایجاد تاریخ اول ماه بعد
            if month == 12:
                next_month = jdatetime.date(year + 1, 1, 1)
            else:
                next_month = jdatetime.date(year, month + 1, 1)
            
            # آخرین روز ماه جاری
            last_day = next_month - jdatetime.timedelta(days=1)
            return last_day.day
        except:
            # روش ساده‌تر برای ماه‌های عادی
            if month <= 6:
                return 31
            elif month <= 11:
                return 30
            else:  # اسفند
                return 29 if year % 4 == 3 else 30
    
    def load_rack_data(self):
        """بارگذاری داده‌های رک"""
        try:
            print("🔍 شروع بارگذاری رک...")
            
            # پاک کردن ویجت‌های قبلی
            self.cleanup_previous_widgets()
            
            # حذف ویجت loading
            if self.loading_label:
                self.loading_label.setParent(None)
                self.loading_label = None
            
            # ایجاد اسکرول area
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            
            # ویجت اصلی رک
            self.rack_container = QWidget()
            self.rack_layout = QVBoxLayout(self.rack_container)
            self.rack_layout.setContentsMargins(0, 0, 0, 0)
            self.rack_layout.setSpacing(1)
            
            # ایجاد هدر روزهای ماه
            days_header = self.create_days_header()
            self.rack_layout.addLayout(days_header)
            
            # ایجاد ردیف‌های اتاق‌ها
            self.create_room_rows()
            
            scroll_area.setWidget(self.rack_container)
            
            # اضافه کردن اسکرول به layout اصلی
            layout = self.layout()
            if layout.count() > 1:  # اگر ویجت قبلی وجود دارد، حذف کن
                old_widget = layout.itemAt(1).widget()
                if old_widget:
                    old_widget.setParent(None)
            
            layout.addWidget(scroll_area)
            
            print(f"✅ بارگذاری رک کامل شد")
            
        except Exception as e:
            print(f"❌ خطا در بارگذاری رک: {e}")
            import traceback
            traceback.print_exc()
    
    def cleanup_previous_widgets(self):
        """پاک کردن ویجت‌های قبلی از حافظه"""
        try:
            # قطع کردن تمام connection‌ها
            for widget in self.cell_widgets:
                try:
                    if hasattr(widget, 'clicked'):
                        widget.clicked.disconnect()
                except:
                    pass
            
            self.cell_widgets.clear()
            
            # پاک کردن container قبلی
            if hasattr(self, 'rack_container') and self.rack_container:
                self.rack_container.setParent(None)
                self.rack_container = None
                
        except Exception as e:
            print(f"خطا در cleanup: {e}")
    
    def create_days_header(self):
        days_layout = QHBoxLayout()
        days_layout.setContentsMargins(120, 0, 0, 0)  # فضا برای ستون اتاق‌ها
        
        year = self.year_combo.currentData()
        month = self.month_combo.currentData()
        days_in_month = self.get_days_in_month(year, month)
        
        # ایجاد هدر برای هر روز
        for day in range(1, days_in_month + 1):
            day_widget = QLabel(str(day))
            day_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            day_widget.setMinimumSize(120, 30)
            day_widget.setStyleSheet("""
                QLabel {
                    background-color: #34495e;
                    color: white;
                    font-weight: bold;
                    border: 1px solid #2c3e50;
                    border-radius: 3px;
                    padding: 5px;
                }
            """)
            days_layout.addWidget(day_widget)
        
        days_layout.addStretch()
        return days_layout
    
    def create_room_rows(self):
        """ایجاد ردیف‌های اتاق‌ها"""
        year = self.year_combo.currentData()
        month = self.month_combo.currentData()
        days_in_month = self.get_days_in_month(year, month)
        
        # ایجاد یک ردیف برای هر اتاق
        for room_idx in range(126):
            room_layout = QHBoxLayout()
            room_layout.setContentsMargins(0, 0, 0, 0)
            room_layout.setSpacing(1)
            
            # سلول اطلاعات اتاق - با نمایش ظرفیت
            room_number = self.get_room_number(room_idx)
            room_capacity = self.get_room_capacity(room_idx)
            room_info_text = f"اتاق {room_number}\nظرفیت: {room_capacity}"
            room_info = QLabel(room_info_text)
            room_info.setMinimumSize(120, 60)
            room_info.setMaximumSize(120, 60)
            room_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            room_info.setStyleSheet("""
                QLabel {
                    background-color: #ecf0f1;
                    border: 1px solid #bdc3c7;
                    border-radius: 3px;
                    padding: 5px;
                    font-weight: bold;
                    font-size: 10px;
                }
            """)
            room_layout.addWidget(room_info)
            
            # ایجاد سلول‌های روزهای ماه
            for day in range(1, days_in_month + 1):
                try:
                    current_date = jdatetime.date(year, month, day)
                    cell_data = self.get_cell_data(room_idx + 1, current_date)
                    
                    # ایجاد ویجت سلول با قابلیت کلیک
                    cell_widget = RoomCellWidget(cell_data, room_number, current_date)
                    cell_widget.setMinimumSize(120, 60)
                    cell_widget.setMaximumSize(120, 60)
                    cell_widget.clicked.connect(self.on_cell_clicked)
                    
                    # ذخیره reference برای مدیریت حافظه
                    self.cell_widgets.append(cell_widget)
                    
                    room_layout.addWidget(cell_widget)
                except Exception as e:
                    print(f"خطا در ایجاد سلول برای اتاق {room_idx + 1} روز {day}: {e}")
                    # سلول خالی در صورت خطا
                    try:
                        cell_widget = RoomCellWidget(None, room_number, current_date)
                        cell_widget.setMinimumSize(120, 60)
                        cell_widget.setMaximumSize(120, 60)
                        cell_widget.clicked.connect(self.on_cell_clicked)
                        self.cell_widgets.append(cell_widget)
                        room_layout.addWidget(cell_widget)
                    except Exception as inner_e:
                        print(f"خطا در ایجاد سلول جایگزین: {inner_e}")
            
            room_layout.addStretch()
            self.rack_layout.addLayout(room_layout)
    
    def on_cell_clicked(self, room_number, jalali_date):
        """هنگام کلیک روی سلول"""
        try:
            self.cell_clicked.emit(room_number, jalali_date)
        except Exception as e:
            print(f"خطا در ارسال signal کلیک: {e}")
    
    def get_room_number(self, room_idx):
        floor = (room_idx // 21) + 1
        room_num = (room_idx % 21) + 1
        return f"{floor}{room_num:02d}"
    
    def get_room_capacity(self, room_idx):
        """دریافت ظرفیت اتاق"""
        session = self.reservation_manager.Session()
        try:
            room = session.query(Room).filter(Room.id == room_idx + 1).first()
            return room.capacity if room else 0
        except Exception as e:
            print(f"خطا در دریافت ظرفیت اتاق: {e}")
            return 0
        finally:
            session.close()
    
    def get_cell_data(self, room_id, jalali_date):
        """دریافت اطلاعات رزرو برای یک اتاق در تاریخ مشخص"""
        session = None
        try:
            print(f"🔍 بررسی اتاق {room_id} در تاریخ {jalali_date}")
            
            gregorian_date = jalali_date.togregorian()
            
            session = self.reservation_manager.Session()
            
            # دریافت همه رزروهای این اتاق در این تاریخ
            from sqlalchemy import and_
            
            reservations = session.query(Reservation, Guest).join(
                Guest, and_(Reservation.guest_id == Guest.id)
            ).filter(
                Reservation.room_id == room_id,
                Reservation.check_in <= gregorian_date,
                Reservation.check_out > gregorian_date,
                Reservation.status.in_(['confirmed', 'checked_in'])
            ).all()
            
            print(f"📊 تعداد رزروهای پیدا شده برای اتاق {room_id}: {len(reservations)}")
            
            if reservations:
                # اگر چندین رزرو در یک روز وجود دارد
                if len(reservations) > 1:
                    print(f"⚠️ چندین رزرو برای اتاق {room_id} در تاریخ {jalali_date}")
                    return {
                        'multiple_reservations': True,
                        'reservations': [
                            {
                                'guest_name': f"{guest.first_name} {guest.last_name}",
                                'nights': (res.check_out - res.check_in).days,
                                'package': res.package_type,
                                'check_in': res.check_in,
                                'check_out': res.check_out
                            }
                            for res, guest in reservations
                        ]
                    }
                else:
                    # یک رزرو
                    reservation, guest = reservations[0]
                    nights = (reservation.check_out - reservation.check_in).days
                    
                    print(f"✅ رزرو پیدا شد: {guest.first_name} {guest.last_name} - {nights} شب")
                    
                    return {
                        'guest_name': f"{guest.first_name} {guest.last_name}",
                        'nights': nights,
                        'package': reservation.package_type,
                        'check_in': reservation.check_in,
                        'check_out': reservation.check_out,
                        'multiple_reservations': False
                    }
                    
        except Exception as e:
            print(f"❌ خطا در دریافت داده سلول برای اتاق {room_id} در تاریخ {jalali_date}: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            if session:
                session.close()  # ✅ اطمینان از بسته شدن session
    
    def previous_month(self):
        current_index = self.month_combo.currentIndex()
        if current_index > 0:
            self.month_combo.setCurrentIndex(current_index - 1)
        else:
            self.month_combo.setCurrentIndex(11)
            current_year = int(self.year_combo.currentText())
            self.year_combo.setCurrentText(str(current_year - 1))
    
    def next_month(self):
        current_index = self.month_combo.currentIndex()
        if current_index < 11:
            self.month_combo.setCurrentIndex(current_index + 1)
        else:
            self.month_combo.setCurrentIndex(0)
            current_year = int(self.year_combo.currentText())
            self.year_combo.setCurrentText(str(current_year + 1))
    
    def go_to_today(self):
        today = jdatetime.date.today()
        self.month_combo.setCurrentIndex(today.month - 1)
        self.year_combo.setCurrentText(str(today.year))