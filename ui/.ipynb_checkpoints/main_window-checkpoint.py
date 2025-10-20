from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QFrame, QGridLayout, QTabWidget, QLineEdit,
                            QPushButton, QMessageBox, QDialog, QFormLayout,
                            QComboBox, QSpinBox, QDateEdit, QDialogButtonBox,
                            QListWidget, QListWidgetItem, QApplication, QGroupBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon
from datetime import datetime, timedelta
import sys
import os

# اضافه کردن مسیرها به sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'models'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from reservation_manager import ReservationManager
from models.models import Reservation, Room, Guest
from jalali import JalaliDate
import jdatetime

from rack_widget import RackWidget
from guests_tab import GuestsTab
from reports_tab import ReportsTab
from settings_tab import SettingsTab

class JalaliDateEdit(QDateEdit):
    """ویجت ویرایش تاریخ شمسی"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.setDisplayFormat("yyyy/MM/dd")
        
        # تنظیم minimum و maximum date برای جلوگیری از نمایش سال 1131
        from PyQt6.QtCore import QDate
        min_date = QDate(1300, 1, 1)  # سال 1300 شمسی
        max_date = QDate(1500, 12, 29)  # سال 1500 شمسی
        self.setDateRange(min_date, max_date)
        
        # تنظیم تاریخ امروز به شمسی
        today_jalali = jdatetime.date.today()
        self.setJalaliDate(today_jalali)
        
    def setJalaliDate(self, jalali_date):
        """تنظیم تاریخ شمسی"""
        from PyQt6.QtCore import QDate
        # تبدیل مستقیم تاریخ شمسی به QDate
        qdate = QDate(jalali_date.year, jalali_date.month, jalali_date.day)
        self.setDate(qdate)
    
    def getJalaliDate(self):
        """دریافت تاریخ شمسی"""
        qdate = self.date()
        # تبدیل QDate به تاریخ شمسی
        return jdatetime.date(qdate.year(), qdate.month(), qdate.day())

class EditReservationDialog(QDialog):
    def __init__(self, reservation_manager, reservation_id, parent=None):
        super().__init__(parent)
        self.reservation_manager = reservation_manager
        self.reservation_id = reservation_id
        self.setWindowTitle("✏️ ویرایش رزرو")
        self.setModal(True)
        self.setMinimumWidth(700)
        self.setup_ui()
        self.load_reservation_data()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # هدر دیالوگ
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2c3e50, stop:1 #3498db);
                border-radius: 12px;
                padding: 20px;
            }
            QLabel {
                color: white;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        
        title_label = QLabel("✏️ ویرایش رزرو")
        title_label.setFont(QFont("B Titr", 18, QFont.Weight.Bold))
        
        icon_label = QLabel("🏨")
        icon_label.setFont(QFont("Segoe UI Emoji", 24))
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(icon_label)
        
        layout.addWidget(header_frame)
        
        # فیلدهای فرم
        form_container = QFrame()
        form_container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        
        form_layout = QFormLayout(form_container)
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(15, 15, 15, 15)
        
        # فیلدهای غیرقابل ویرایش
        self.room_number = QLineEdit()
        self.room_number.setReadOnly(True)
        self.room_number.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                font-size: 13px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background-color: #f8f9fa;
            }
        """)
        
        # فیلدهای قابل ویرایش مهمان
        self.first_name = QLineEdit()
        self.last_name = QLineEdit()
        self.phone = QLineEdit()
        self.email = QLineEdit()
        
        input_style = """
            QLineEdit {
                padding: 12px;
                font-size: 13px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: #f8f9fa;
            }
        """
        
        self.first_name.setStyleSheet(input_style)
        self.last_name.setStyleSheet(input_style)
        self.phone.setStyleSheet(input_style)
        self.email.setStyleSheet(input_style)
        
        self.adults_spin = QSpinBox()
        self.adults_spin.setRange(1, 10)
        self.adults_spin.setSuffix(" نفر")
        
        self.children_spin = QSpinBox()
        self.children_spin.setRange(0, 10)
        self.children_spin.setSuffix(" نفر")
        
        self.nights_spin = QSpinBox()
        self.nights_spin.setRange(1, 30)
        self.nights_spin.setSuffix(" شب")
        self.nights_spin.valueChanged.connect(self.on_nights_changed)
        
        spin_style = """
            QSpinBox {
                padding: 10px;
                font-size: 13px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background-color: white;
            }
            QSpinBox:focus {
                border: 2px solid #3498db;
            }
        """
        
        self.adults_spin.setStyleSheet(spin_style)
        self.children_spin.setStyleSheet(spin_style)
        self.nights_spin.setStyleSheet(spin_style)
        
        self.package_combo = QComboBox()
        self.package_combo.addItems(["فول برد", "اسکان + صبحانه", "فقط اسکان", "پکیج ویژه"])
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["confirmed", "checked_in", "checked_out", "cancelled"])
        
        self.guest_type_combo = QComboBox()
        self.guest_type_combo.addItems(["حضوری", "آژانس", "رزرو", "سایت", "اینستاگرام", "تلفنی"])
        
        combo_style = """
            QComboBox {
                padding: 10px;
                font-size: 13px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background-color: white;
            }
            QComboBox:focus {
                border: 2px solid #3498db;
            }
        """
        
        self.package_combo.setStyleSheet(combo_style)
        self.status_combo.setStyleSheet(combo_style)
        self.guest_type_combo.setStyleSheet(combo_style)
        
        # تاریخ‌های شمسی - قابل ویرایش
        self.checkin_date = JalaliDateEdit()
        self.checkin_date.dateChanged.connect(self.on_checkin_changed)
        self.checkin_date.setStyleSheet(spin_style)
        
        self.checkout_date = JalaliDateEdit()
        self.checkout_date.setStyleSheet(spin_style)
        
        form_layout.addRow("🏨 شماره اتاق:", self.room_number)
        form_layout.addRow("👤 نام:", self.first_name)
        form_layout.addRow("👤 نام خانوادگی:", self.last_name)
        form_layout.addRow("📱 تلفن:", self.phone)
        form_layout.addRow("📧 ایمیل:", self.email)
        form_layout.addRow("👥 تعداد بزرگسال:", self.adults_spin)
        form_layout.addRow("🧒 تعداد کودک:", self.children_spin)
        form_layout.addRow("🌙 تعداد شب‌های اقامت:", self.nights_spin)
        form_layout.addRow("🍽️ نوع پکیج:", self.package_combo)
        form_layout.addRow("📊 وضعیت:", self.status_combo)
        form_layout.addRow("🎯 نوع مهمان:", self.guest_type_combo)
        form_layout.addRow("📅 تاریخ ورود:", self.checkin_date)
        form_layout.addRow("📆 تاریخ خروج:", self.checkout_date)
        
        layout.addWidget(form_container)
        
        # دکمه‌ها
        button_layout = QHBoxLayout()
        
        self.update_btn = QPushButton("💾 بروزرسانی رزرو")
        self.update_btn.setObjectName("update_button")
        self.update_btn.setMinimumHeight(45)
        self.update_btn.setStyleSheet("""
            QPushButton#update_button {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                color: white;
                border: 3px solid #5dade2;
                padding: 12px 30px;
                border-radius: 10px;
                font-family: "B Titr";
                font-size: 14px;
                font-weight: bold;
                min-width: 180px;
            }
            QPushButton#update_button:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2980b9, stop:1 #21618c);
                border: 3px solid #3498db;
            }
        """)
        
        cancel_btn = QPushButton("❌ انصراف")
        cancel_btn.setMinimumHeight(45)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e74c3c, stop:1 #c0392b);
                color: white;
                border: 3px solid #ec7063;
                padding: 12px 30px;
                border-radius: 10px;
                font-family: "B Titr";
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c0392b, stop:1 #a93226);
            }
        """)
        
        self.update_btn.clicked.connect(self.update_reservation)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.update_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    
    def load_reservation_data(self):
        """بارگذاری داده‌های رزرو برای ویرایش"""
        try:
            reservation = self.reservation_manager.get_reservation_by_id(self.reservation_id)
            if not reservation:
                QMessageBox.warning(self, "خطا", "رزرو یافت نشد")
                self.reject()
                return
            
            session = self.reservation_manager.Session()
            
            # دریافت اطلاعات اتاق
            room = session.query(Room).filter(Room.id == reservation.room_id).first()
            guest = session.query(Guest).filter(Guest.id == reservation.guest_id).first()
            
            if not guest:
                QMessageBox.warning(self, "خطا", "مهمان یافت نشد")
                self.reject()
                return
            
            # پر کردن فرم
            self.room_number.setText(room.room_number if room else "نامشخص")
            self.first_name.setText(guest.first_name)
            self.last_name.setText(guest.last_name)
            self.phone.setText(guest.phone or "")
            self.email.setText(guest.email or "")
            self.adults_spin.setValue(reservation.adults)
            self.children_spin.setValue(reservation.children)
            
            # محاسبه تعداد روزهای اقامت
            nights = (reservation.check_out - reservation.check_in).days
            self.nights_spin.setValue(nights)
            
            self.package_combo.setCurrentText(reservation.package_type)
            self.status_combo.setCurrentText(reservation.status)
            self.guest_type_combo.setCurrentText(getattr(reservation, 'guest_type', 'حضوری'))
            
            # تنظیم تاریخ‌های شمسی
            checkin_jalali = jdatetime.date.fromgregorian(date=reservation.check_in.date())
            checkout_jalali = jdatetime.date.fromgregorian(date=reservation.check_out.date())
            
            self.checkin_date.setJalaliDate(checkin_jalali)
            self.checkout_date.setJalaliDate(checkout_jalali)
            
            # ذخیره ID مهمان برای بروزرسانی
            self.guest_id = guest.id
            
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری داده‌ها: {str(e)}")
            self.reject()
        finally:
            if 'session' in locals():
                session.close()
    
    def on_nights_changed(self):
        """هنگام تغییر تعداد روزهای اقامت"""
        self.update_checkout_date()
    
    def on_checkin_changed(self):
        """هنگام تغییر تاریخ ورود"""
        self.update_checkout_date()
    
    def update_checkout_date(self):
        """بروزرسانی تاریخ خروج"""
        checkin_jalali = self.checkin_date.getJalaliDate()
        nights = self.nights_spin.value()
        checkout_jalali = checkin_jalali + jdatetime.timedelta(days=nights)
        self.checkout_date.setJalaliDate(checkout_jalali)
    
    def update_reservation(self):
        """بروزرسانی رزرو و اطلاعات مهمان"""
        try:
            session = self.reservation_manager.Session()
            
            # بروزرسانی اطلاعات مهمان
            guest = session.query(Guest).filter(Guest.id == self.guest_id).first()
            if guest:
                guest.first_name = self.first_name.text()
                guest.last_name = self.last_name.text()
                guest.phone = self.phone.text()
                guest.email = self.email.text()
            
            # داده‌های بروزرسانی رزرو
            update_data = {
                'adults': self.adults_spin.value(),
                'children': self.children_spin.value(),
                'package_type': self.package_combo.currentText(),
                'status': self.status_combo.currentText(),
                'guest_type': self.guest_type_combo.currentText(),
                'check_in': datetime.combine(
                    self.checkin_date.getJalaliDate().togregorian(), 
                    datetime.min.time()
                ),
                'check_out': datetime.combine(
                    self.checkout_date.getJalaliDate().togregorian(), 
                    datetime.min.time()
                )
            }
            
            session.commit()
            session.close()
            
            # استفاده از متد update_reservation برای ثبت لاگ
            success, message = self.reservation_manager.update_reservation(
                self.reservation_id, 
                update_data, 
                changed_by="اپراتور"
            )
            
            if success:
                QMessageBox.information(self, "✅ موفق", message)
                self.accept()
            else:
                QMessageBox.warning(self, "❌ خطا", message)
                
        except Exception as e:
            QMessageBox.critical(self, "❌ خطا", f"خطا در بروزرسانی: {str(e)}")

class ReservationDialog(QDialog):
    def __init__(self, reservation_manager, selected_room=None, selected_date=None, parent=None):
        super().__init__(parent)
        self.reservation_manager = reservation_manager
        self.selected_room = selected_room
        self.selected_date = selected_date
        self.selected_room_id = None
        
        self.setWindowTitle("🎯 ثبت رزرو جدید - هتل آراد")
        self.setModal(True)
        self.setMinimumWidth(750)
        self.setMinimumHeight(850)
        
        self.setup_ui()
        self.load_available_rooms()
        
        # اگر اتاق و تاریخ مشخص شده، پیش‌پر کردن فرم
        if selected_room and selected_date:
            self.prefill_form()
        
        # تایمر برای بروزرسانی خودکار اتاق‌ها
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.load_available_rooms)
        self.update_timer.start(2000)  # هر 2 ثانیه
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # هدر دیالوگ
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2c3e50, stop:1 #3498db);
                border-radius: 12px;
                padding: 20px;
            }
            QLabel {
                color: white;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        
        title_label = QLabel("📋 فرم ثبت رزرو جدید")
        title_label.setFont(QFont("B Titr", 18, QFont.Weight.Bold))
        
        subtitle_label = QLabel("هتل آراد - سیستم مدیریت رزرواسیون")
        subtitle_label.setFont(QFont("B Titr", 12))
        subtitle_label.setStyleSheet("color: #ecf0f1;")
        
        header_text_layout = QVBoxLayout()
        header_text_layout.addWidget(title_label)
        header_text_layout.addWidget(subtitle_label)
        
        icon_label = QLabel("🏨")
        icon_label.setFont(QFont("Segoe UI Emoji", 24))
        
        header_layout.addLayout(header_text_layout)
        header_layout.addStretch()
        header_layout.addWidget(icon_label)
        
        layout.addWidget(header_frame)
        
        # فرم اصلی
        form_container = QFrame()
        form_container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                padding: 0px;
            }
        """)
        
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(15, 15, 15, 15)
        
        # بخش اطلاعات مهمان
        guest_group = QGroupBox("👤 اطلاعات مهمان")
        guest_group.setFont(QFont("B Titr", 13, QFont.Weight.Bold))
        guest_group.setStyleSheet("""
            QGroupBox {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 5px 15px;
                background-color: #3498db;
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }
        """)
        
        guest_layout = QFormLayout(guest_group)
        guest_layout.setSpacing(12)
        guest_layout.setContentsMargins(15, 20, 15, 15)
        
        # فیلدهای اطلاعات مهمان
        self.first_name = QLineEdit()
        self.first_name.setPlaceholderText("نام مهمان را وارد کنید...")
        self.first_name.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                font-size: 13px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: #f8f9fa;
            }
        """)
        
        self.last_name = QLineEdit()
        self.last_name.setPlaceholderText("نام خانوادگی مهمان را وارد کنید...")
        self.last_name.setStyleSheet(self.first_name.styleSheet())
        
        self.phone = QLineEdit()
        self.phone.setPlaceholderText("09xxxxxxxxx - شماره تلفن همراه...")
        self.phone.setStyleSheet(self.first_name.styleSheet())
        
        self.email = QLineEdit()
        self.email.setPlaceholderText("example@domain.com - آدرس ایمیل (اختیاری)...")
        self.email.setStyleSheet(self.first_name.styleSheet())
        
        guest_layout.addRow("🔸 نام:", self.first_name)
        guest_layout.addRow("🔸 نام خانوادگی:", self.last_name)
        guest_layout.addRow("📱 تلفن:", self.phone)
        guest_layout.addRow("📧 ایمیل:", self.email)
        
        # بخش اطلاعات رزرو
        reservation_group = QGroupBox("📅 اطلاعات رزرو")
        reservation_group.setFont(QFont("B Titr", 13, QFont.Weight.Bold))
        reservation_group.setStyleSheet(guest_group.styleSheet())
        
        reservation_layout = QFormLayout(reservation_group)
        reservation_layout.setSpacing(12)
        reservation_layout.setContentsMargins(15, 20, 15, 15)
        
        # فیلدهای اطلاعات رزرو
        self.adults_spin = QSpinBox()
        self.adults_spin.setRange(1, 10)
        self.adults_spin.setValue(2)
        self.adults_spin.setSuffix(" نفر")
        self.adults_spin.valueChanged.connect(self.on_guests_changed)
        self.adults_spin.setStyleSheet("""
            QSpinBox {
                padding: 10px;
                font-size: 13px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background-color: white;
            }
            QSpinBox:focus {
                border: 2px solid #3498db;
            }
        """)
        
        self.children_spin = QSpinBox()
        self.children_spin.setRange(0, 10)
        self.children_spin.setSuffix(" نفر")
        self.children_spin.valueChanged.connect(self.on_guests_changed)
        self.children_spin.setStyleSheet(self.adults_spin.styleSheet())
        
        self.nights_spin = QSpinBox()
        self.nights_spin.setRange(1, 30)
        self.nights_spin.setValue(1)
        self.nights_spin.setSuffix(" شب")
        self.nights_spin.valueChanged.connect(self.on_nights_changed)
        self.nights_spin.setStyleSheet(self.adults_spin.styleSheet())
        
        # نوع پکیج
        self.package_combo = QComboBox()
        self.package_combo.addItems(["فول برد", "اسکان + صبحانه", "فقط اسکان", "پکیج ویژه"])
        self.package_combo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                font-size: 13px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background-color: white;
            }
            QComboBox:focus {
                border: 2px solid #3498db;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
        """)
        
        # نوع مهمان
        self.guest_type_combo = QComboBox()
        self.guest_type_combo.addItems(["حضوری", "آژانس", "رزرو", "سایت", "اینستاگرام", "تلفنی"])
        self.guest_type_combo.setStyleSheet(self.package_combo.styleSheet())
        
        # تاریخ‌های شمسی
        self.checkin_date = JalaliDateEdit()
        self.checkin_date.dateChanged.connect(self.on_checkin_changed)
        self.checkin_date.setStyleSheet(self.adults_spin.styleSheet())
        
        self.checkout_date = JalaliDateEdit()
        self.checkout_date.setStyleSheet(self.adults_spin.styleSheet())
        self.update_checkout_date()
        
        reservation_layout.addRow("👥 تعداد بزرگسال:", self.adults_spin)
        reservation_layout.addRow("🧒 تعداد کودک:", self.children_spin)
        reservation_layout.addRow("🌙 تعداد شب‌های اقامت:", self.nights_spin)
        reservation_layout.addRow("🍽️ نوع پکیج:", self.package_combo)
        reservation_layout.addRow("🎯 نوع مهمان:", self.guest_type_combo)
        reservation_layout.addRow("📅 تاریخ ورود:", self.checkin_date)
        reservation_layout.addRow("📆 تاریخ خروج:", self.checkout_date)
        
        # بخش اتاق‌های پیشنهادی
        rooms_group = QGroupBox("🏨 اتاق‌های پیشنهادی")
        rooms_group.setFont(QFont("B Titr", 13, QFont.Weight.Bold))
        rooms_group.setStyleSheet(guest_group.styleSheet())
        
        rooms_layout = QVBoxLayout(rooms_group)
        
        rooms_info_label = QLabel("اتاق‌های خالی و مناسب بر اساس تعداد مهمانان و تاریخ انتخاب شده:")
        rooms_info_label.setStyleSheet("color: #7f8c8d; font-size: 11px; padding: 5px;")
        rooms_info_label.setWordWrap(True)
        
        self.suggested_rooms_list = QListWidget()
        self.suggested_rooms_list.setAlternatingRowColors(True)
        self.suggested_rooms_list.itemDoubleClicked.connect(self.on_room_selected)
        self.suggested_rooms_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background-color: white;
                font-family: "B Titr";
                font-size: 12px;
                outline: none;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #ecf0f1;
                background-color: white;
            }
            QListWidget::item:alternate {
                background-color: #f8f9fa;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                color: white;
                border-radius: 4px;
                border: none;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
                border-radius: 4px;
            }
        """)
        
        rooms_layout.addWidget(rooms_info_label)
        rooms_layout.addWidget(self.suggested_rooms_list)
        
        # اضافه کردن گروه‌ها به فرم اصلی
        form_layout.addWidget(guest_group)
        form_layout.addWidget(reservation_group)
        form_layout.addWidget(rooms_group)
        
        layout.addWidget(form_container)
        
        # دکمه‌های پایین
        button_container = QFrame()
        button_container.setStyleSheet("background: transparent;")
        button_layout = QHBoxLayout(button_container)
        
        self.submit_btn = QPushButton("✅ ثبت رزرو")
        self.submit_btn.setObjectName("submit_button")
        self.submit_btn.setMinimumHeight(50)
        self.submit_btn.setStyleSheet("""
            QPushButton#submit_button {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #219a52);
                color: white;
                border: 3px solid #2ecc71;
                padding: 15px 35px;
                border-radius: 10px;
                font-family: "B Titr";
                font-size: 15px;
                font-weight: bold;
                min-width: 150px;
            }
            QPushButton#submit_button:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #219a52, stop:1 #1e8449);
                border: 3px solid #27ae60;
            }
            QPushButton#submit_button:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e8449, stop:1 #196f3d);
                border: 3px solid #229954;
            }
            QPushButton#submit_button:disabled {
                background: #95a5a6;
                border: 3px solid #7f8c8d;
                color: #ecf0f1;
            }
        """)
        
        cancel_btn = QPushButton("❌ انصراف")
        cancel_btn.setMinimumHeight(50)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e74c3c, stop:1 #c0392b);
                color: white;
                border: 3px solid #ec7063;
                padding: 15px 35px;
                border-radius: 10px;
                font-family: "B Titr";
                font-size: 15px;
                font-weight: bold;
                min-width: 150px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c0392b, stop:1 #a93226);
                border: 3px solid #e74c3c;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #a93226, stop:1 #922b21);
            }
        """)
        
        self.submit_btn.clicked.connect(self.submit_reservation)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.submit_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        
        layout.addWidget(button_container)
        
        self.setLayout(layout)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    
    def prefill_form(self):
        """پیش‌پر کردن فرم بر اساس اتاق و تاریخ انتخاب شده"""
        if self.selected_room:
            # پیدا کردن اتاق در لیست پیشنهادی و انتخاب آن
            for i in range(self.suggested_rooms_list.count()):
                item = self.suggested_rooms_list.item(i)
                room_data = item.data(Qt.ItemDataRole.UserRole)
                if room_data and room_data['number'] == self.selected_room:
                    self.suggested_rooms_list.setCurrentItem(item)
                    self.selected_room_id = room_data['id']
                    break
        
        if self.selected_date:
            self.checkin_date.setJalaliDate(self.selected_date)
    
    def on_nights_changed(self):
        """هنگام تغییر تعداد روزهای اقامت"""
        self.update_checkout_date()
        self.on_dates_changed()
    
    def on_checkin_changed(self):
        """هنگام تغییر تاریخ ورود"""
        self.update_checkout_date()
        self.on_dates_changed()
    
    def update_checkout_date(self):
        """بروزرسانی تاریخ خروج بر اساس تاریخ ورود و تعداد روزها"""
        checkin_jalali = self.checkin_date.getJalaliDate()
        nights = self.nights_spin.value()
        checkout_jalali = checkin_jalali + jdatetime.timedelta(days=nights)
        self.checkout_date.setJalaliDate(checkout_jalali)
    
    def on_guests_changed(self):
        """هنگام تغییر تعداد مهمانان"""
        self.load_available_rooms()
    
    def on_dates_changed(self):
        """هنگام تغییر تاریخ‌ها"""
        self.load_available_rooms()
    
    def on_room_selected(self, item):
        """هنگام انتخاب اتاق از لیست پیشنهادی"""
        room_data = item.data(Qt.ItemDataRole.UserRole)
        if room_data:
            self.selected_room_id = room_data['id']
    
    def load_available_rooms(self):
        """بارگذاری اتاق‌های قابل رزرو"""
        try:
            self.suggested_rooms_list.clear()
            
            check_in = self.checkin_date.getJalaliDate().togregorian()
            check_out = self.checkout_date.getJalaliDate().togregorian()
            total_guests = self.adults_spin.value() + self.children_spin.value()
            
            if check_in >= check_out:
                item = QListWidgetItem("⚠️ تاریخ خروج باید بعد از تاریخ ورود باشد")
                item.setForeground(Qt.GlobalColor.red)
                self.suggested_rooms_list.addItem(item)
                return
            
            session = self.reservation_manager.Session()
            
            # پیدا کردن اتاق‌های خالی با ظرفیت مناسب
            available_rooms = session.query(Room).filter(
                Room.is_active == True,
                Room.capacity >= total_guests
            ).all()
            
            suitable_rooms = []
            for room in available_rooms:
                is_available = self.reservation_manager.is_room_available(
                    room.id, check_in, check_out
                )
                
                if is_available:
                    suitable_rooms.append(room)
            
            if suitable_rooms:
                for room in suitable_rooms:
                    # محاسبه قیمت کل
                    stay_duration = (check_out - check_in).days
                    total_price = room.price_per_night * stay_duration
                    
                    # آیکون بر اساس نوع اتاق
                    room_icons = {
                        "سینگل": "👤",
                        "دبل": "👥", 
                        "تویین": "🛏️",
                        "سوئیت": "🏠",
                        "دیلوکس": "⭐"
                    }
                    icon = room_icons.get(room.room_type, "🏨")
                    
                    item_text = f"{icon} اتاق {room.room_number} - {room.room_type}\n"
                    item_text += f"   📊 ظرفیت: {room.capacity} نفر | 💰 قیمت شبانه: {room.price_per_night:,} تومان\n"
                    item_text += f"   💵 قیمت کل ({stay_duration} شب): {total_price:,} تومان"
                    
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.ItemDataRole.UserRole, {
                        'id': room.id,
                        'number': room.room_number,
                        'type': room.room_type,
                        'capacity': room.capacity,
                        'price': room.price_per_night
                    })
                    
                    self.suggested_rooms_list.addItem(item)
                    
                    # اگر اتاق انتخاب شده وجود دارد، آن را انتخاب کن
                    if self.selected_room and room.room_number == self.selected_room:
                        self.suggested_rooms_list.setCurrentItem(item)
                        self.selected_room_id = room.id
            else:
                item = QListWidgetItem("❌ هیچ اتاق خالی با ظرفیت مورد نظر در تاریخ انتخاب شده یافت نشد")
                item.setForeground(Qt.GlobalColor.red)
                self.suggested_rooms_list.addItem(item)
                
        except Exception as e:
            print(f"خطا در بارگذاری اتاق‌ها: {e}")
            item = QListWidgetItem(f"⚠️ خطا در بارگذاری: {str(e)}")
            item.setForeground(Qt.GlobalColor.red)
            self.suggested_rooms_list.addItem(item)
        finally:
            if 'session' in locals():
                session.close()
    
    def validate_form(self):
        """اعتبارسنجی فرم"""
        errors = []
        
        if not self.first_name.text().strip():
            errors.append("وارد کردن نام اجباری است")
        
        if not self.last_name.text().strip():
            errors.append("وارد کردن نام خانوادگی اجباری است")
        
        if not self.phone.text().strip():
            errors.append("وارد کردن شماره تلفن اجباری است")
        
        if self.suggested_rooms_list.currentItem() is None:
            errors.append("لطفاً یک اتاق از لیست انتخاب کنید")
        
        if self.checkin_date.getJalaliDate() >= self.checkout_date.getJalaliDate():
            errors.append("تاریخ خروج باید بعد از تاریخ ورود باشد")
        
        return errors
    
    def submit_reservation(self):
        """ثبت رزرو جدید با استفاده از reservation_manager"""
        try:
            # اعتبارسنجی فرم
            errors = self.validate_form()
            if errors:
                error_msg = "\n".join([f"• {error}" for error in errors])
                QMessageBox.warning(self, "خطا در ثبت", f"لطفاً موارد زیر را بررسی کنید:\n\n{error_msg}")
                return
            
            room_data = self.suggested_rooms_list.currentItem().data(Qt.ItemDataRole.UserRole)
            if not room_data:
                QMessageBox.warning(self, "خطا", "اتاق انتخاب شده معتبر نیست")
                return
            
            # آماده‌سازی داده‌ها
            check_in = datetime.combine(
                self.checkin_date.getJalaliDate().togregorian(), 
                datetime.min.time()
            )
            check_out = datetime.combine(
                self.checkout_date.getJalaliDate().togregorian(), 
                datetime.min.time()
            )
            
            stay_duration = (check_out - check_in).days
            total_amount = room_data['price'] * stay_duration
            
            reservation_data = {
                'room_id': room_data['id'],
                'check_in': check_in,
                'check_out': check_out,
                'status': 'confirmed',
                'adults': self.adults_spin.value(),
                'children': self.children_spin.value(),
                'total_amount': total_amount,
                'paid_amount': 0,
                'package_type': self.package_combo.currentText(),
                'guest_type': self.guest_type_combo.currentText()
            }
            
            guest_data = {
                'first_name': self.first_name.text().strip(),
                'last_name': self.last_name.text().strip(),
                'phone': self.phone.text().strip(),
                'email': self.email.text().strip(),
                'nationality': 'ایرانی'
            }
            
            # غیرفعال کردن دکمه ثبت برای جلوگیری از کلیک‌های مکرر
            self.submit_btn.setEnabled(False)
            self.submit_btn.setText("⏳ در حال ثبت...")
            
            # استفاده از reservation_manager برای ثبت رزرو
            success, message, reservation_id = self.reservation_manager.create_reservation(
                reservation_data, guest_data, "اپراتور"
            )
            
            if success:
                QMessageBox.information(self, "✅ موفق", 
                    f"رزرو با موفقیت ثبت شد!\n\n"
                    f"📋 کد رزرو: {reservation_id}\n"
                    f"👤 مهمان: {guest_data['first_name']} {guest_data['last_name']}\n"
                    f"🏨 اتاق: {room_data['number']}\n"
                    f"💰 مبلغ کل: {total_amount:,} تومان")
                self.accept()
            else:
                QMessageBox.critical(self, "❌ خطا", message)
                self.submit_btn.setEnabled(True)
                self.submit_btn.setText("✅ ثبت رزرو")
                
        except Exception as e:
            QMessageBox.critical(self, "❌ خطا", f"خطا در ثبت رزرو: {str(e)}")
            self.submit_btn.setEnabled(True)
            self.submit_btn.setText("✅ ثبت رزرو")
    
    def closeEvent(self, event):
        """هنگام بسته شدن دیالوگ"""
        self.update_timer.stop()
        super().closeEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.reservation_manager = ReservationManager()
        self.setup_ui()
        
        # تایمر برای بروزرسانی خودکار
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # هر 1 ثانیه
    
    def setup_ui(self):
        self.setWindowTitle("سیستم مدیریت رزرواسیون هتل آراد")
        self.setGeometry(50, 50, 1600, 900)
        
        # راست‌چین کردن کل پنجره
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # هدر برنامه
        header = self.create_header()
        layout.addWidget(header)
        
        # تب‌ها
        tabs = QTabWidget()
        
        # تب رک - با بیشترین فضای ممکن
        self.rack_tab = RackWidget()
        # اضافه کردن signal برای کلیک روی سلول
        self.rack_tab.cell_clicked.connect(self.on_rack_cell_clicked)
        tabs.addTab(self.rack_tab, "📋 رک مرکزی")
        
        # تب مهمانان
        self.guests_tab = GuestsTab(self.reservation_manager)
        tabs.addTab(self.guests_tab, "👥 مهمانان")
        
        # تب گزارشات
        self.reports_tab = ReportsTab(self.reservation_manager)
        tabs.addTab(self.reports_tab, "📊 گزارشات")
        
        # تب تنظیمات - اضافه کردن تب جدید
        self.settings_tab = SettingsTab(self.reservation_manager)
        tabs.addTab(self.settings_tab, "⚙️ تنظیمات و لاگ")
        
        layout.addWidget(tabs)
    
    def create_header(self):
        """ایجاد هدر اصلی برنامه با طراحی مدرن"""
        header_frame = QFrame()
        header_frame.setObjectName("header_frame")
        header_frame.setStyleSheet("""
            QFrame#header_frame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2c3e50, stop:0.5 #3498db, stop:1 #2980b9);
                color: white;
                padding: 15px;
                border-radius: 15px;
                margin: 10px;
                border: 2px solid #34495e;
            }
            QLabel {
                color: white;
                font-weight: bold;
                background: transparent;
                border: none;
            }
            QPushButton {
                font-family: "B Titr";
                font-weight: bold;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # بخش لوگو و عنوان
        title_section = QHBoxLayout()
        
        # لوگو
        logo_label = QLabel("🏨")
        logo_label.setFont(QFont("Segoe UI Emoji", 24))
        logo_label.setStyleSheet("""
            QLabel {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 10px;
                padding: 10px;
                margin-right: 10px;
            }
        """)
        
        # عنوان اصلی
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        
        main_title = QLabel("هتل آراد")
        main_title.setFont(QFont("B Titr", 20, QFont.Weight.Bold))
        main_title.setStyleSheet("color: white; font-size: 20px;")
        
        sub_title = QLabel("سیستم مدیریت رزرواسیون")
        sub_title.setFont(QFont("B Titr", 12))
        sub_title.setStyleSheet("color: #ecf0f1; font-size: 12px; opacity: 0.9;")
        
        title_layout.addWidget(main_title)
        title_layout.addWidget(sub_title)
        
        title_section.addWidget(logo_label)
        title_section.addLayout(title_layout)
        
        layout.addLayout(title_section)
        layout.addStretch()
        
        # بخش دکمه‌های عملیاتی
        buttons_section = QHBoxLayout()
        buttons_section.setSpacing(10)
        
        # دکمه تغییر تم
        self.theme_btn = QPushButton("🌓 تغییر تم")
        self.theme_btn.setObjectName("theme_button")
        self.theme_btn.setToolTip("تغییر بین تم روشن و تاریک")
        self.theme_btn.setStyleSheet("""
            QPushButton#theme_button {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f39c12, stop:1 #e67e22);
                color: white;
                border: 2px solid #f1c40f;
                padding: 10px 20px;
                border-radius: 8px;
                font-family: "B Titr";
                font-size: 12px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton#theme_button:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e67e22, stop:1 #d35400);
                border: 2px solid #f39c12;
            }
            QPushButton#theme_button:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d35400, stop:1 #ba4a00);
            }
        """)
        self.theme_btn.clicked.connect(self.toggle_theme)
        
        # دکمه ثبت رزرو جدید - طراحی ویژه
        self.new_reservation_btn = QPushButton("➕ ثبت رزرو جدید")
        self.new_reservation_btn.setObjectName("new_reservation_btn")
        self.new_reservation_btn.setToolTip("ثبت رزرو جدید برای مهمان")
        self.new_reservation_btn.setStyleSheet("""
            QPushButton#new_reservation_btn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #219a52);
                color: white;
                border: 3px solid #2ecc71;
                padding: 12px 25px;
                border-radius: 10px;
                font-family: "B Titr";
                font-size: 14px;
                font-weight: bold;
                min-width: 150px;
            }
            QPushButton#new_reservation_btn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #219a52, stop:1 #1e8449);
                border: 3px solid #27ae60;
            }
            QPushButton#new_reservation_btn:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e8449, stop:1 #196f3d);
                border: 3px solid #229954;
            }
        """)
        self.new_reservation_btn.clicked.connect(self.show_new_reservation_dialog)
        
        # دکمه راهنما
        help_btn = QPushButton("❓ راهنما")
        help_btn.setObjectName("help_button")
        help_btn.setToolTip("راهنمای استفاده از سیستم")
        help_btn.setStyleSheet("""
            QPushButton#help_button {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #9b59b6, stop:1 #8e44ad);
                color: white;
                border: 2px solid #bb8fce;
                padding: 10px 20px;
                border-radius: 8px;
                font-family: "B Titr";
                font-size: 12px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton#help_button:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8e44ad, stop:1 #7d3c98);
                border: 2px solid #9b59b6;
            }
        """)
        help_btn.clicked.connect(self.show_help)
        
        buttons_section.addWidget(self.theme_btn)
        buttons_section.addWidget(help_btn)
        buttons_section.addWidget(self.new_reservation_btn)
        
        layout.addLayout(buttons_section)
        layout.addStretch()
        
        # بخش تاریخ و زمان
        time_section = QVBoxLayout()
        time_section.setSpacing(2)
        time_section.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # تاریخ شمسی
        self.date_label = QLabel()
        self.date_label.setFont(QFont("B Titr", 12, QFont.Weight.Bold))
        self.date_label.setStyleSheet("color: white; font-size: 12px;")
        
        # ساعت
        self.time_label = QLabel()
        self.time_label.setFont(QFont("B Titr", 14, QFont.Weight.Bold))
        self.time_label.setStyleSheet("""
            QLabel {
                color: #f1c40f;
                font-size: 14px;
                background: rgba(0, 0, 0, 0.3);
                padding: 5px 10px;
                border-radius: 5px;
                border: 1px solid #f39c12;
            }
        """)
        
        time_section.addWidget(self.date_label)
        time_section.addWidget(self.time_label)
        
        layout.addLayout(time_section)
        
        header_frame.setLayout(layout)
        return header_frame

    def update_time(self):
        """بروزرسانی تاریخ و زمان شمسی"""
        try:
            now = jdatetime.datetime.now()
            
            # فرمت تاریخ شمسی
            persian_months = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", 
                             "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
            
            month_name = persian_months[now.month - 1]
            date_text = f"📅 {now.day} {month_name} {now.year}"
            
            # فرمت زمان
            time_text = f"🕒 {now.hour:02d}:{now.minute:02d}:{now.second:02d}"
            
            self.date_label.setText(date_text)
            self.time_label.setText(time_text)
            
        except Exception as e:
            print(f"خطا در بروزرسانی زمان: {e}")
            # حالت fallback
            import datetime
            now = datetime.datetime.now()
            self.date_label.setText("📅 تاریخ شمسی")
            self.time_label.setText(f"🕒 {now.hour:02d}:{now.minute:02d}")

    def toggle_theme(self):
        """تغییر تم برنامه"""
        try:
            from theme_manager import ThemeManager
            theme_manager = ThemeManager()
            success = theme_manager.toggle_theme(QApplication.instance())
            
            if success:
                # تغییر متن دکمه بر اساس تم فعلی
                if theme_manager.current_theme == "dark":
                    self.theme_btn.setText("🌙 تم تاریک")
                    self.theme_btn.setToolTip("تغییر به تم روشن")
                else:
                    self.theme_btn.setText("☀️ تم روشن")
                    self.theme_btn.setToolTip("تغییر به تم تاریک")
                    
                QMessageBox.information(self, "تغییر تم", 
                    f"تم برنامه به {theme_manager.current_theme} تغییر کرد.")
            else:
                QMessageBox.warning(self, "خطا", "خطا در تغییر تم")
                
        except Exception as e:
            print(f"خطا در تغییر تم: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در تغییر تم: {str(e)}")

    def show_help(self):
        """نمایش راهنمای برنامه"""
        help_text = """
        <div style='font-family: "B Titr"; text-align: right; line-height: 1.8;'>
        <h2 style='color: #2c3e50;'>🎯 راهنمای سیستم مدیریت هتل آراد</h2>
        
        <h3 style='color: #3498db;'>📋 تب رک مرکزی:</h3>
        <p>• مشاهده وضعیت تمام اتاق‌ها در تقویم شمسی</p>
        <p>• کلیک روی هر سلول برای ثبت یا ویرایش رزرو</p>
        
        <h3 style='color: #3498db;'>👥 تب مهمانان:</h3>
        <p>• مدیریت اطلاعات مهمانان</p>
        <p>• مشاهده مهمانان فعال و سوابق</p>
        
        <h3 style='color: #3498db;'>📊 تب گزارشات:</h3>
        <p>• آمار اشغال اتاق‌ها</p>
        <p>• گزارشات مالی و درآمدی</p>
        
        <h3 style='color: #3498db;'>⚙️ تب تنظیمات:</h3>
        <p>• مشاهده لاگ تغییرات سیستم</p>
        <p>• مدیریت تنظیمات پیشرفته</p>
        
        <h3 style='color: #27ae60;'>🎯 نکات مهم:</h3>
        <p>• از دکمه <b>ثبت رزرو جدید</b> برای رزرو سریع استفاده کنید</p>
        <p>• امکان تغییر تم از دکمه <b>تغییر تم</b> وجود دارد</p>
        <p>• تاریخ‌ها به صورت شمسی نمایش داده می‌شوند</p>
        </div>
        """
        
        msg = QMessageBox()
        msg.setWindowTitle("📚 راهنمای سیستم")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(help_text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def show_new_reservation_dialog(self, room_number=None, selected_date=None):
        """نمایش دیالوگ ثبت رزرو جدید"""
        dialog = ReservationDialog(self.reservation_manager, room_number, selected_date, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # تاخیر در بروزرسانی رک برای جلوگیری از conflict
            QTimer.singleShot(100, self.delayed_refresh_rack)

    def show_edit_reservation_dialog(self, reservation_id):
        """نمایش دیالوگ ویرایش رزرو"""
        dialog = EditReservationDialog(self.reservation_manager, reservation_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # بروزرسانی رک
            self.delayed_refresh_rack()

    def delayed_refresh_rack(self):
        """بروزرسانی رک با تاخیر"""
        if hasattr(self.rack_tab, 'load_rack_data'):
            try:
                self.rack_tab.load_rack_data()
            except Exception as e:
                print(f"خطا در بروزرسانی رک: {e}")

    def on_rack_cell_clicked(self, room_number, jalali_date):
        """هنگام کلیک روی سلول در رک"""
        print(f"کلیک روی اتاق {room_number} در تاریخ {jalali_date}")
        
        # پیدا کردن رزرو موجود
        reservation = self.find_reservation_for_cell(room_number, jalali_date)
        
        if reservation:
            # ویرایش رزرو موجود
            print(f"ویرایش رزرو موجود با ID: {reservation.id}")
            self.show_edit_reservation_dialog(reservation.id)
        else:
            # ثبت رزرو جدید
            print("ثبت رزرو جدید")
            self.show_new_reservation_dialog(room_number, jalali_date)

    def find_reservation_for_cell(self, room_number, jalali_date):
        """پیدا کردن رزرو برای اتاق و تاریخ مشخص"""
        session = self.reservation_manager.Session()
        try:
            # پیدا کردن اتاق بر اساس شماره
            room = session.query(Room).filter(Room.room_number == room_number).first()
            if not room:
                return None
            
            # تبدیل تاریخ شمسی به میلادی
            gregorian_date = jalali_date.togregorian()
            
            # پیدا کردن رزرو
            from sqlalchemy import and_
            
            reservation = session.query(Reservation).filter(
                and_(
                    Reservation.room_id == room.id,
                    Reservation.check_in <= gregorian_date,
                    Reservation.check_out > gregorian_date,
                    Reservation.status.in_(['confirmed', 'checked_in'])
                )
            ).first()
            
            return reservation
            
        except Exception as e:
            print(f"خطا در پیدا کردن رزرو: {e}")
            return None
        finally:
            session.close()

# اگر این فایل مستقیماً اجرا شود
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())