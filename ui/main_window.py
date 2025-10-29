from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QFrame, QGridLayout, QTabWidget, QLineEdit,
                            QPushButton, QMessageBox, QDialog, QFormLayout,
                            QComboBox, QSpinBox, QDateEdit, QDialogButtonBox,
                            QListWidget, QListWidgetItem, QApplication, QGroupBox,
                            QCheckBox, QFileDialog, QScrollArea)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QPixmap
from datetime import datetime, timedelta
import os
import sys
import base64

# اضافه کردن مسیرها به sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'models'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from reservation_manager import ReservationManager
from agency_manager import AgencyManager
from models.models import Reservation, Room, Guest, Agency
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
        self.guest_id = None
        
        self.setWindowTitle("✏️ ویرایش رزرو - هتل آراد")
        self.setModal(True)
        self.setFixedSize(850, 650)  # اندازه ثابت
        
        self.setup_ui()
        self.load_reservation_data()
    
    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # اسکرول area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        main_widget = QWidget()
        scroll_area.setWidget(main_widget)
        
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # هدر
        header_label = QLabel("✏️ ویرایش رزرو")
        header_label.setFont(QFont("B Titr", 18, QFont.Weight.Bold))
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setFixedHeight(60)
        header_label.setStyleSheet("""
            QLabel {
                background: #3498db;
                color: white;
                padding: 15px;
                border-radius: 8px;
                font-size: 16px;
            }
        """)
        layout.addWidget(header_label)
        
        # اطلاعات رزرو
        info_group = QGroupBox("📋 اطلاعات رزرو")
        info_group.setFont(QFont("B Titr", 12, QFont.Weight.Bold))
        info_group.setStyleSheet(self.get_groupbox_style())
        
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(15)
        info_layout.setContentsMargins(20, 25, 20, 20)
        
        # فیلدهای بزرگ‌تر و خوانا
        self.room_number = QLineEdit()
        self.room_number.setReadOnly(True)
        self.room_number.setFixedHeight(40)
        self.room_number.setStyleSheet("""
            QLineEdit {
                background-color: #f8f9fa;
                padding: 10px;
                font-size: 14px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
            }
        """)
        
        self.first_name = self.create_large_field("نام مهمان")
        self.last_name = self.create_large_field("نام خانوادگی مهمان")
        
        self.adults_spin = self.create_large_spinbox(1, 10, " نفر")
        self.children_spin = self.create_large_spinbox(0, 10, " نفر")
        self.nights_spin = self.create_large_spinbox(1, 30, " شب")
        self.nights_spin.valueChanged.connect(self.on_nights_changed)
        
        self.package_combo = self.create_large_combobox(["فول برد", "اسکان + صبحانه", "فقط اسکان", "پکیج ویژه"])
        self.status_combo = self.create_large_combobox(["confirmed", "checked_in", "checked_out", "cancelled"])
        self.guest_type_combo = self.create_large_combobox(["حضوری", "آژانس", "رزرو", "سایت", "اینستاگرام", "تلفنی"])
        
        # تاریخ‌های شمسی با اندازه بزرگ‌تر
        self.checkin_date = JalaliDateEdit()
        self.checkin_date.setFixedHeight(40)
        self.checkin_date.dateChanged.connect(self.on_checkin_changed)
        self.checkin_date.setStyleSheet(self.get_large_field_style())
        
        self.checkout_date = JalaliDateEdit()
        self.checkout_date.setFixedHeight(40)
        self.checkout_date.setStyleSheet(self.get_large_field_style())
        
        # اضافه کردن فیلدها با برچسب‌های خوانا
        info_layout.addRow("🏨 شماره اتاق:", self.room_number)
        info_layout.addRow("👤 نام مهمان:", self.first_name)
        info_layout.addRow("👥 نام خانوادگی:", self.last_name)
        info_layout.addRow("🔢 تعداد بزرگسال:", self.adults_spin)
        info_layout.addRow("🧒 تعداد کودک:", self.children_spin)
        info_layout.addRow("🌙 تعداد شب‌ها:", self.nights_spin)
        info_layout.addRow("🍽️ نوع پکیج:", self.package_combo)
        info_layout.addRow("📊 وضعیت رزرو:", self.status_combo)
        info_layout.addRow("🎯 نوع مهمان:", self.guest_type_combo)
        info_layout.addRow("📅 تاریخ ورود:", self.checkin_date)
        info_layout.addRow("📆 تاریخ خروج:", self.checkout_date)
        
        layout.addWidget(info_group)
        
        # دکمه‌ها
        button_layout = QHBoxLayout()
        
        update_btn = QPushButton("💾 بروزرسانی رزرو")
        update_btn.setFixedHeight(50)
        update_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #219a52);
                color: white;
                border: 2px solid #2ecc71;
                padding: 12px 30px;
                border-radius: 8px;
                font-family: "B Titr";
                font-size: 14px;
                font-weight: bold;
                min-width: 150px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #219a52, stop:1 #1e8449);
            }
        """)
        update_btn.clicked.connect(self.update_reservation)
        
        cancel_btn = QPushButton("❌ انصراف")
        cancel_btn.setFixedHeight(50)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e74c3c, stop:1 #c0392b);
                color: white;
                border: 2px solid #ec7063;
                padding: 12px 30px;
                border-radius: 8px;
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
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(update_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    
    def create_large_field(self, placeholder):
        """ایجاد فیلد متنی بزرگ"""
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setFixedHeight(40)
        field.setStyleSheet(self.get_large_field_style())
        return field
    
    def create_large_spinbox(self, min_val, max_val, suffix):
        """ایجاد spinbox بزرگ"""
        spinbox = QSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setSuffix(suffix)
        spinbox.setFixedHeight(40)
        spinbox.setStyleSheet(self.get_large_field_style())
        return spinbox
    
    def create_large_combobox(self, items):
        """ایجاد combobox بزرگ"""
        combobox = QComboBox()
        combobox.addItems(items)
        combobox.setFixedHeight(40)
        combobox.setStyleSheet(self.get_large_field_style())
        return combobox
    
    def get_large_field_style(self):
        return """
            QLineEdit, QSpinBox, QComboBox {
                padding: 10px 12px;
                font-size: 14px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background-color: white;
                min-height: 40px;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border: 2px solid #3498db;
                background-color: #f8f9fa;
            }
        """
    
    def get_groupbox_style(self):
        return """
            QGroupBox {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 8px 20px;
                background-color: #3498db;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
        """
    
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
        """هنگام تغییر تعداد شب‌ها"""
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
        """بروزرسانی رزرو"""
        try:
            session = self.reservation_manager.Session()
            
            # بروزرسانی اطلاعات مهمان
            guest = session.query(Guest).filter(Guest.id == self.guest_id).first()
            if guest:
                guest.first_name = self.first_name.text()
                guest.last_name = self.last_name.text()
            
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
        self.receipt_file_data = None
        self.receipt_filename = None
        
        self.agency_manager = AgencyManager()
        
        self.setWindowTitle("🎯 ثبت رزرو جدید - هتل آراد")
        self.setModal(True)
        self.setFixedSize(900, 700)  # اندازه ثابت برای پنجره
        
        self.setup_ui()
        self.load_available_rooms()
        self.load_agencies()
        
        if selected_room and selected_date:
            self.prefill_form()
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.load_available_rooms)
        self.update_timer.start(2000)
    
    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # ایجاد اسکرول area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # ویجت اصلی برای اسکرول
        main_widget = QWidget()
        scroll_area.setWidget(main_widget)
        
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # هدر
        header_frame = QFrame()
        header_frame.setFixedHeight(100)
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2c3e50, stop:1 #3498db);
                border-radius: 12px;
                padding: 15px;
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
        title_label.setFont(QFont("B Titr", 16, QFont.Weight.Bold))
        
        subtitle_label = QLabel("هتل آراد - سیستم مدیریت رزرواسیون")
        subtitle_label.setFont(QFont("B Titr", 11))
        subtitle_label.setStyleSheet("color: #ecf0f1;")
        
        header_text_layout = QVBoxLayout()
        header_text_layout.addWidget(title_label)
        header_text_layout.addWidget(subtitle_label)
        
        icon_label = QLabel("🏨")
        icon_label.setFont(QFont("Segoe UI Emoji", 28))
        
        header_layout.addLayout(header_text_layout)
        header_layout.addStretch()
        header_layout.addWidget(icon_label)
        
        layout.addWidget(header_frame)
        
        # ایجاد فرم اصلی
        self.create_main_form(layout)
        
        # دکمه‌ها
        self.create_buttons(layout)
        
        # اضافه کردن stretch برای فاصله
        layout.addStretch()
        
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)


    def create_main_tabs(self):
        """ایجاد تب‌های اصلی برنامه"""
        tabs = QTabWidget()
        tabs.setObjectName("main_tabs")
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                background-color: #ffffff;
                margin-top: 5px;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background: #ecf0f1;
                border: 2px solid #bdc3c7;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 12px 25px;
                margin-right: 3px;
                font-family: "B Titr";
                font-size: 12px;
                font-weight: bold;
                color: #2c3e50;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background: #3498db;
                color: white;
                border: 2px solid #2980b9;
                border-bottom: none;
            }
            QTabBar::tab:hover:!selected {
                background: #d6dbdf;
                border: 2px solid #a6acaf;
            }
        """)
        
        # تب رک مرکزی
        self.rack_tab = RackWidget()
        self.rack_tab.cell_clicked.connect(self.on_rack_cell_clicked)
        tabs.addTab(self.rack_tab, "📋 رک مرکزی")
        
        # تب مهمانان
        self.guests_tab = GuestsTab(self.reservation_manager)
        tabs.addTab(self.guests_tab, "👥 مهمانان")
        
        # تب گزارشات
        self.reports_tab = ReportsTab(self.reservation_manager)
        tabs.addTab(self.reports_tab, "📊 گزارشات")
        
        # تب تنظیمات
        self.settings_tab = SettingsTab(self.reservation_manager)
        tabs.addTab(self.settings_tab, "⚙️ تنظیمات و لاگ")
        
        return tabs

    def create_status_bar(self):
        """ایجاد نوار وضعیت"""
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background: #34495e;
                color: white;
                font-family: "B Titr";
                font-size: 11px;
                padding: 5px;
                border-top: 2px solid #2c3e50;
            }
        """)
        
        # وضعیت اتصال به دیتابیس
        self.db_status_label = QLabel("🟢 متصل به دیتابیس")
        self.status_bar.addPermanentWidget(self.db_status_label)
        
        # تعداد رزروهای امروز
        self.today_reservations_label = QLabel("📊 امروز: 0 رزرو")
        self.status_bar.addPermanentWidget(self.today_reservations_label)
        
        # نسخه برنامه
        self.version_label = QLabel("ورژن 1.0.0")
        self.status_bar.addPermanentWidget(self.version_label)
    
    def apply_main_window_styles(self):
        """اعمال استایل‌های کلی پنجره اصلی"""
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ecf0f1, stop:1 #bdc3c7);
            }
            QWidget {
                font-family: "B Titr";
            }
        """)
    
    def initial_data_load(self):
        """بارگذاری اولیه داده‌ها"""
        try:
            # به روزرسانی آمار امروز
            self.update_today_stats()
            
            # بارگذاری اولیه رک
            if hasattr(self.rack_tab, 'load_rack_data'):
                self.rack_tab.load_rack_data()
                
        except Exception as e:
            print(f"خطا در بارگذاری اولیه داده‌ها: {e}")
    
    def update_today_stats(self):
        """به روزرسانی آمار امروز"""
        try:
            today = datetime.now().date()
            
            # تعداد رزروهای امروز
            session = self.reservation_manager.Session()
            today_reservations = session.query(Reservation).filter(
                Reservation.check_in <= today,
                Reservation.check_out > today,
                Reservation.status.in_(['confirmed', 'checked_in'])
            ).count()
            
            # تعداد ورودی‌های امروز
            arrivals = session.query(Reservation).filter(
                Reservation.check_in == today,
                Reservation.status == 'confirmed'
            ).count()
            
            # تعداد خروجی‌های امروز
            departures = session.query(Reservation).filter(
                Reservation.check_out == today,
                Reservation.status == 'checked_in'
            ).count()
            
            session.close()
            
            # به روزرسانی labels
            self.today_reservations_label.setText(
                f"📊 امروز: {today_reservations} رزرو | 🚶‍♂️ ورودی: {arrivals} | 🚶‍♀️ خروجی: {departures}"
            )
            
        except Exception as e:
            print(f"خطا در به روزرسانی آمار: {e}")
            self.today_reservations_label.setText("📊 امروز: خطا در بارگذاری آمار")

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

    def update_reservation(self):
        """بروزرسانی رزرو و اطلاعات مهمان"""
        try:
            session = self.reservation_manager.Session()
            
            # بروزرسانی اطلاعات مهمان
            guest = session.query(Guest).filter(Guest.id == self.guest_id).first()
            if guest:
                guest.first_name = self.first_name.text()
                guest.last_name = self.last_name.text()
            
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
        try:
            room_data = item.data(Qt.ItemDataRole.UserRole)
            if room_data:
                self.selected_room_id = room_data['id']
                
                # نمایش اطلاعات اتاق انتخاب شده
                room_info = (
                    f"🏨 اتاق انتخاب شده:\n"
                    f"• شماره: {room_data['number']}\n"
                    f"• نوع: {room_data['type']}\n"
                    f"• ظرفیت: {room_data['capacity']} نفر\n"
                    f"• قیمت شبانه: {room_data['price']:,} تومان"
                )
                
                # محاسبه قیمت کل
                check_in = self.checkin_date.getJalaliDate().togregorian()
                check_out = self.checkout_date.getJalaliDate().togregorian()
                stay_duration = (check_out - check_in).days
                total_price = room_data['price'] * stay_duration
                
                room_info += f"\n• قیمت کل ({stay_duration} شب): {total_price:,} تومان"
                
                # نمایش اطلاعات در status bar یا tooltip
                self.suggested_rooms_list.setToolTip(room_info)
                
                print(f"✅ اتاق انتخاب شد: {room_data['number']} (ID: {room_data['id']})")
                
        except Exception as e:
            print(f"❌ خطا در انتخاب اتاق: {e}")
    
    def load_available_rooms(self):
        """بارگذاری اتاق‌های قابل رزرو با بررسی Back-to-Back"""
        try:
            self.suggested_rooms_list.clear()
            
            check_in = self.checkin_date.getJalaliDate().togregorian()
            check_out = self.checkout_date.getJalaliDate().togregorian()
            total_guests = self.adults_spin.value() + self.children_spin.value()
            
            # اعتبارسنجی اولیه تاریخ‌ها
            if check_in >= check_out:
                item = QListWidgetItem("⚠️ تاریخ خروج باید بعد از تاریخ ورود باشد")
                item.setForeground(Qt.GlobalColor.red)
                self.suggested_rooms_list.addItem(item)
                return
            
            if check_in < datetime.now().date():
                item = QListWidgetItem("⚠️ تاریخ ورود نمی‌تواند در گذشته باشد")
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
                # بررسی دقیق موجودی اتاق با پشتیبانی از Back-to-Back
                is_available, conflicts = self.reservation_manager.get_room_availability_with_back_to_back(
                    room.id, check_in, check_out
                )
                
                if is_available:
                    suitable_rooms.append({
                        'room': room,
                        'conflicts': conflicts,
                        'back_to_back_possible': any(c['type'] == 'back_to_back_possible' for c in conflicts)
                    })
            
            if suitable_rooms:
                for room_info in suitable_rooms:
                    room = room_info['room']
                    has_back_to_back = room_info['back_to_back_possible']
                    
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
                    
                    # متن آیتم
                    item_text = f"{icon} اتاق {room.room_number} - {room.room_type}\n"
                    item_text += f"   📊 ظرفیت: {room.capacity} نفر | 💰 قیمت شبانه: {room.price_per_night:,} تومان\n"
                    item_text += f"   💵 قیمت کل ({stay_duration} شب): {total_price:,} تومان"
                    
                    if has_back_to_back:
                        item_text += f"\n   🔄 امکان Back-to-Back"
                    
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.ItemDataRole.UserRole, {
                        'id': room.id,
                        'number': room.room_number,
                        'type': room.room_type,
                        'capacity': room.capacity,
                        'price': room.price_per_night,
                        'has_back_to_back': has_back_to_back
                    })
                    
                    # رنگ‌آمیزی برای اتاق‌های با Back-to-Back
                    if has_back_to_back:
                        item.setBackground(QColor("#FFF3CD"))  # زرد روشن
                    
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
            print(f"❌ خطا در بارگذاری اتاق‌ها: {e}")
            item = QListWidgetItem(f"⚠️ خطا در بارگذاری: {str(e)}")
            item.setForeground(Qt.GlobalColor.red)
            self.suggested_rooms_list.addItem(item)
        finally:
            if 'session' in locals():
                session.close()

    def create_main_form(self, layout):
        # کانتینر فرم
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
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(15, 15, 15, 15)
        
        # بخش اطلاعات مهمان
        self.create_guest_section(form_layout)
        
        # بخش اطلاعات رزرو
        self.create_reservation_section(form_layout)
        
        # بخش مالی و پرداخت
        self.create_payment_section(form_layout)
        
        # بخش اتاق‌های پیشنهادی
        self.create_rooms_section(form_layout)
        
        layout.addWidget(form_container)
    
    def create_guest_section(self, layout):
        guest_group = QGroupBox("👤 اطلاعات مهمان")
        guest_group.setFont(QFont("B Titr", 13, QFont.Weight.Bold))
        guest_group.setStyleSheet(self.get_groupbox_style())
        
        guest_layout = QFormLayout(guest_group)
        guest_layout.setSpacing(12)
        guest_layout.setContentsMargins(15, 20, 15, 15)
        
        # فیلدهای اطلاعات مهمان
        self.first_name = self.create_lineedit("نام مهمان")
        self.last_name = self.create_lineedit("نام خانوادگی مهمان")
        self.id_number = self.create_lineedit("کد ملی (اختیاری)")
        
        guest_layout.addRow("🔸 نام:", self.first_name)
        guest_layout.addRow("🔸 نام خانوادگی:", self.last_name)
        guest_layout.addRow("🆔 کد ملی:", self.id_number)
        
        layout.addWidget(guest_group)
    
    def create_reservation_section(self, layout):
        reservation_group = QGroupBox("📅 اطلاعات رزرو")
        reservation_group.setFont(QFont("B Titr", 13, QFont.Weight.Bold))
        reservation_group.setStyleSheet(self.get_groupbox_style())
        
        reservation_layout = QFormLayout(reservation_group)
        reservation_layout.setSpacing(12)
        reservation_layout.setContentsMargins(15, 20, 15, 15)
        
        # فیلدهای اطلاعات رزرو
        self.adults_spin = self.create_spinbox(1, 10, 2, " نفر")
        self.children_spin = self.create_spinbox(0, 10, 0, " نفر")
        self.nights_spin = self.create_spinbox(1, 30, 1, " شب")
        self.nights_spin.valueChanged.connect(self.on_nights_changed)
        
        self.package_combo = self.create_combobox(["فول برد", "اسکان + صبحانه", "فقط اسکان", "پکیج ویژه"])
        
        # نوع مهمان با قابلیت انتخاب آژانس
        self.guest_type_combo = self.create_combobox(["حضوری", "آژانس", "رزرو", "سایت", "اینستاگرام", "تلفنی"])
        self.guest_type_combo.currentTextChanged.connect(self.on_guest_type_changed)
        
        # کامبوب آژانس (در ابتدا غیرفعال)
        self.agency_combo = self.create_combobox([])
        self.agency_combo.setEnabled(False)
        self.agency_combo.setPlaceholderText("انتخاب آژانس")
        
        # تاریخ‌های شمسی
        self.checkin_date = JalaliDateEdit()
        self.checkin_date.dateChanged.connect(self.on_checkin_changed)
        self.checkin_date.setStyleSheet(self.get_field_style())
        
        self.checkout_date = JalaliDateEdit()
        self.checkout_date.setStyleSheet(self.get_field_style())
        self.update_checkout_date()
        
        reservation_layout.addRow("👥 تعداد بزرگسال:", self.adults_spin)
        reservation_layout.addRow("🧒 تعداد کودک:", self.children_spin)
        reservation_layout.addRow("🌙 تعداد شب‌های اقامت:", self.nights_spin)
        reservation_layout.addRow("🍽️ نوع پکیج:", self.package_combo)
        reservation_layout.addRow("🎯 نوع مهمان:", self.guest_type_combo)
        reservation_layout.addRow("🏢 آژانس:", self.agency_combo)
        reservation_layout.addRow("📅 تاریخ ورود:", self.checkin_date)
        reservation_layout.addRow("📆 تاریخ خروج:", self.checkout_date)
        
        layout.addWidget(reservation_group)

    def validate_prepayment(self):
        """اعتبارسنجی مبلغ پیش پرداخت"""
        try:
            prepayment_text = self.prepayment_edit.text().strip()
            if prepayment_text:
                # حذف کاما از اعداد
                prepayment_text = prepayment_text.replace(',', '')
                
                if not prepayment_text.isdigit():
                    self.prepayment_edit.setStyleSheet("""
                        QLineEdit {
                            padding: 10px;
                            font-size: 13px;
                            border: 2px solid #e74c3c;
                            border-radius: 6px;
                            background-color: #ffeaa7;
                        }
                    """)
                    return False
                else:
                    # فرمت کردن عدد با کاما
                    formatted_amount = "{:,}".format(int(prepayment_text))
                    self.prepayment_edit.setText(formatted_amount)
                    self.prepayment_edit.setStyleSheet(self.get_field_style())
                    return True
            return True
            
        except Exception as e:
            print(f"خطا در اعتبارسنجی مبلغ: {e}")
            return False
    
    def create_payment_section(self, layout):
        payment_group = QGroupBox("💰 اطلاعات پرداخت")
        payment_group.setFont(QFont("B Titr", 13, QFont.Weight.Bold))
        payment_group.setStyleSheet(self.get_groupbox_style())
        
        payment_layout = QFormLayout(payment_group)
        payment_layout.setSpacing(12)
        payment_layout.setContentsMargins(15, 20, 15, 15)
        
        # مبلغ پیش پرداخت
        self.prepayment_edit = QLineEdit()
        self.prepayment_edit.setPlaceholderText("مبلغ به تومان (اختیاری)")
        self.prepayment_edit.setStyleSheet(self.get_field_style())
        self.prepayment_edit.textChanged.connect(self.validate_prepayment)
        
        # نوع تسویه
        self.settlement_combo = self.create_combobox(["تسویه با هتل", "تسویه با آژانس", "تسویه شده"])
        
        # کد پیگیری
        self.tracking_code_edit = self.create_lineedit("کد پیگیری واریزی (اختیاری)")
        
        # آپلود فیش پرداخت
        upload_layout = QHBoxLayout()
        self.receipt_label = QLabel("هیچ فایلی انتخاب نشده")
        self.receipt_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        
        self.upload_btn = QPushButton("📎 انتخاب فیش پرداخت")
        self.upload_btn.setStyleSheet("""
            QPushButton {
                background: #95a5a6;
                color: white;
                border: 2px solid #7f8c8d;
                padding: 8px 15px;
                border-radius: 6px;
                font-family: "B Titr";
                font-size: 11px;
            }
            QPushButton:hover {
                background: #7f8c8d;
                border: 2px solid #95a5a6;
            }
        """)
        self.upload_btn.clicked.connect(self.upload_receipt)
        
        self.clear_btn = QPushButton("❌ حذف")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: 2px solid #c0392b;
                padding: 8px 15px;
                border-radius: 6px;
                font-family: "B Titr";
                font-size: 11px;
            }
            QPushButton:hover {
                background: #c0392b;
                border: 2px solid #e74c3c;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_receipt)
        self.clear_btn.setVisible(False)
        
        upload_layout.addWidget(self.upload_btn)
        upload_layout.addWidget(self.clear_btn)
        upload_layout.addStretch()
        upload_layout.addWidget(self.receipt_label)
        
        payment_layout.addRow("💵 مبلغ پیش پرداخت:", self.prepayment_edit)
        payment_layout.addRow("🏦 نوع تسویه:", self.settlement_combo)
        payment_layout.addRow("🔢 کد پیگیری:", self.tracking_code_edit)
        payment_layout.addRow("📄 فیش پرداخت:", upload_layout)
        
        layout.addWidget(payment_group)
    
    def create_rooms_section(self, layout):
        rooms_group = QGroupBox("🏨 اتاق‌های پیشنهادی")
        rooms_group.setFont(QFont("B Titr", 13, QFont.Weight.Bold))
        rooms_group.setStyleSheet(self.get_groupbox_style())
        
        rooms_layout = QVBoxLayout(rooms_group)
        
        rooms_info_label = QLabel("اتاق‌های خالی و مناسب بر اساس تعداد مهمانان و تاریخ انتخاب شده:")
        rooms_info_label.setStyleSheet("color: #7f8c8d; font-size: 11px; padding: 5px;")
        rooms_info_label.setWordWrap(True)
        
        self.suggested_rooms_list = QListWidget()
        self.suggested_rooms_list.setAlternatingRowColors(True)
        self.suggested_rooms_list.itemDoubleClicked.connect(self.on_room_selected)
        self.suggested_rooms_list.setMinimumHeight(250)
        self.suggested_rooms_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background-color: white;
                font-family: "B Titr";
                font-size: 12px;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:alternate {
                background-color: #f8f9fa;
            }
            QListWidget::item:selected {
                background: #3498db;
                color: white;
                border-radius: 4px;
            }
        """)
        
        rooms_layout.addWidget(rooms_info_label)
        rooms_layout.addWidget(self.suggested_rooms_list)
        
        layout.addWidget(rooms_group)
    
    def create_buttons(self, layout):
        button_container = QFrame()
        button_container.setStyleSheet("background: transparent;")
        button_layout = QHBoxLayout(button_container)
        
        self.submit_btn = QPushButton("✅ ثبت رزرو")
        self.submit_btn.setObjectName("submit_button")
        self.submit_btn.setMinimumHeight(50)
        self.submit_btn.setStyleSheet(self.get_submit_button_style())
        self.submit_btn.clicked.connect(self.submit_reservation)
        
        cancel_btn = QPushButton("❌ انصراف")
        cancel_btn.setMinimumHeight(50)
        cancel_btn.setStyleSheet(self.get_cancel_button_style())
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.submit_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        
        layout.addWidget(button_container)
    
    # متدهای کمکی برای ایجاد ویجت‌ها
    def create_lineedit(self, placeholder):
        lineedit = QLineEdit()
        lineedit.setPlaceholderText(placeholder)
        lineedit.setStyleSheet(self.get_field_style())
        return lineedit
    
    def create_spinbox(self, min_val, max_val, default, suffix):
        spinbox = QSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(default)
        spinbox.setSuffix(suffix)
        spinbox.setStyleSheet(self.get_field_style())
        return spinbox
    
    def create_combobox(self, items):
        combobox = QComboBox()
        combobox.addItems(items)
        combobox.setStyleSheet(self.get_field_style())
        return combobox
    
    def get_groupbox_style(self):
        return """
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
        """
    
    def get_field_style(self):
        return """
            QLineEdit, QSpinBox, QComboBox {
                padding: 10px;
                font-size: 13px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background-color: white;
                min-height: 15px;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border: 2px solid #3498db;
            }
        """
    
    def get_submit_button_style(self):
        return """
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
            }
            QPushButton#submit_button:disabled {
                background: #95a5a6;
                border: 3px solid #7f8c8d;
                color: #ecf0f1;
            }
        """
    
    def get_cancel_button_style(self):
        return """
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
        """
    
    # متدهای مدیریت آژانس
    def load_agencies(self):
        """بارگذاری لیست آژانس‌ها"""
        try:
            agencies = self.agency_manager.get_all_agencies()
            self.agency_combo.clear()
            self.agency_combo.addItem("-- انتخاب آژانس --", None)
            for agency in agencies:
                self.agency_combo.addItem(agency.name, agency.id)
        except Exception as e:
            print(f"خطا در بارگذاری آژانس‌ها: {e}")
    
    def on_guest_type_changed(self, guest_type):
        """هنگام تغییر نوع مهمان"""
        if guest_type == "آژانس":
            self.agency_combo.setEnabled(True)
            self.agency_combo.setStyleSheet(self.get_field_style() + "background-color: #fff3cd;")
        else:
            self.agency_combo.setEnabled(False)
            self.agency_combo.setStyleSheet(self.get_field_style())
            self.agency_combo.setCurrentIndex(0)
    
    # متدهای مدیریت فایل
    def upload_receipt(self):
        """آپلود فیش پرداخت"""
        try:
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName(
                self,
                "انتخاب فیش پرداخت",
                "",
                "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;PDF Files (*.pdf);;All Files (*)"
            )
            
            if file_path:
                with open(file_path, 'rb') as file:
                    self.receipt_file_data = file.read()
                
                self.receipt_filename = os.path.basename(file_path)
                self.receipt_label.setText(self.receipt_filename)
                self.receipt_label.setStyleSheet("color: #27ae60; font-size: 12px; font-weight: bold;")
                self.clear_btn.setVisible(True)
                
                print(f"✅ فایل آپلود شد: {self.receipt_filename} ({len(self.receipt_file_data)} bytes)")
                
        except Exception as e:
            QMessageBox.warning(self, "خطا", f"خطا در آپلود فایل: {str(e)}")
    
    def clear_receipt(self):
        """حذف فایل آپلود شده"""
        self.receipt_file_data = None
        self.receipt_filename = None
        self.receipt_label.setText("هیچ فایلی انتخاب نشده")
        self.receipt_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        self.clear_btn.setVisible(False)
    
    def validate_form(self):
        """اعتبارسنجی کامل فرم"""
        errors = []
        
        # اطلاعات مهمان
        if not self.first_name.text().strip():
            errors.append("وارد کردن نام اجباری است")
        
        if not self.last_name.text().strip():
            errors.append("وارد کردن نام خانوادگی اجباری است")
        
        # اعتبارسنجی آژانس
        if self.guest_type_combo.currentText() == "آژانس" and self.agency_combo.currentData() is None:
            errors.append("برای مهمان آژانس، انتخاب آژانس اجباری است")
        
        # اعتبارسنجی اتاق
        if self.suggested_rooms_list.currentItem() is None:
            errors.append("لطفاً یک اتاق از لیست انتخاب کنید")
        
        # اعتبارسنجی تاریخ‌ها
        try:
            check_in = self.checkin_date.getJalaliDate()
            check_out = self.checkout_date.getJalaliDate()
            
            if check_in >= check_out:
                errors.append("تاریخ خروج باید بعد از تاریخ ورود باشد")
            
            today = jdatetime.date.today()
            if check_in < today:
                errors.append("تاریخ ورود نمی‌تواند در گذشته باشد")
                
        except Exception as e:
            errors.append("خطا در تاریخ‌های انتخاب شده")
        
        # اعتبارسنجی مبلغ پیش پرداخت
        prepayment_text = self.prepayment_edit.text().strip()
        if prepayment_text and not prepayment_text.isdigit():
            errors.append("مبلغ پیش پرداخت باید عددی باشد")
        
        return errors
    
    def submit_reservation(self):
        """ثبت رزرو جدید"""
        try:
            # اعتبارسنجی فرم
            errors = self.validate_form()
            if errors:
                error_msg = "\n".join([f"• {error}" for error in errors])
                QMessageBox.warning(self, "خطا در ثبت", f"لطفاً موارد زیر را بررسی کنید:\n\n{error_msg}")
                return

            # بررسی انتخاب اتاق
            if self.suggested_rooms_list.currentItem() is None:
                QMessageBox.warning(self, "خطا", "لطفاً یک اتاق از لیست انتخاب کنید")
                return

            room_data = self.suggested_rooms_list.currentItem().data(Qt.ItemDataRole.UserRole)
            if not room_data:
                QMessageBox.warning(self, "خطا", "اتاق انتخاب شده معتبر نیست")
                return

            # آماده‌سازی داده‌ها
            check_in_jalali = self.checkin_date.getJalaliDate()
            check_out_jalali = self.checkout_date.getJalaliDate()
            
            check_in = datetime.combine(
                check_in_jalali.togregorian(), 
                datetime.min.time()
            )
            check_out = datetime.combine(
                check_out_jalali.togregorian(), 
                datetime.min.time()
            )

            # اعتبارسنجی تاریخ‌ها
            if check_in >= check_out:
                QMessageBox.warning(self, "خطا", "تاریخ خروج باید بعد از تاریخ ورود باشد")
                return

            # محاسبه مدت اقامت و قیمت
            stay_duration = (check_out - check_in).days
            total_amount = room_data['price'] * stay_duration
            
            # محاسبه مبلغ پیش پرداخت
            paid_amount = 0
            prepayment_text = self.prepayment_edit.text().strip()
            if prepayment_text:
                paid_amount = float(prepayment_text)

            # داده‌های رزرو
            reservation_data = {
                'room_id': room_data['id'],
                'check_in': check_in,
                'check_out': check_out,
                'status': 'confirmed',
                'adults': self.adults_spin.value(),
                'children': self.children_spin.value(),
                'total_amount': total_amount,
                'paid_amount': paid_amount,
                'package_type': self.package_combo.currentText(),
                'guest_type': self.guest_type_combo.currentText(),
                'agency_id': self.agency_combo.currentData(),
                'settlement_type': self.settlement_combo.currentText(),
                'tracking_code': self.tracking_code_edit.text().strip() or None,
                'receipt_file': self.receipt_file_data,
                'receipt_filename': self.receipt_filename
            }

            # داده‌های مهمان
            guest_data = {
                'first_name': self.first_name.text().strip(),
                'last_name': self.last_name.text().strip(),
                'id_number': self.id_number.text().strip() or None,
                'nationality': 'ایرانی'
            }

            # غیرفعال کردن دکمه ثبت
            self.submit_btn.setEnabled(False)
            self.submit_btn.setText("⏳ در حال ثبت...")
            
            # استفاده از reservation_manager برای ثبت رزرو
            success, message, reservation_id = self.reservation_manager.create_reservation(
                reservation_data, guest_data, "اپراتور"
            )

            if success:
                success_message = (
                    f"✅ رزرو با موفقیت ثبت شد!\n\n"
                    f"📋 کد رزرو: {reservation_id}\n"
                    f"👤 مهمان: {guest_data['first_name']} {guest_data['last_name']}\n"
                    f"🏨 اتاق: {room_data['number']}\n"
                    f"📅 تاریخ ورود: {check_in_jalali}\n"
                    f"📅 تاریخ خروج: {check_out_jalali}\n"
                    f"🌙 مدت اقامت: {stay_duration} شب\n"
                    f"💰 مبلغ کل: {total_amount:,} تومان\n"
                    f"💵 پیش پرداخت: {paid_amount:,} تومан\n"
                    f"🏦 نوع تسویه: {reservation_data['settlement_type']}"
                )
                
                QMessageBox.information(self, "✅ ثبت موفق", success_message)
                self.accept()
                
            else:
                QMessageBox.critical(self, "❌ خطا در ثبت", message)
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

    def show_help(self):
        """نمایش راهنمای برنامه"""
        try:
            help_text = """
            <div style='font-family: "B Titr"; text-align: right; line-height: 1.8; direction: rtl;'>
            <h3 style='color: #2c3e50;'>📚 راهنمای سیستم مدیریت رزرواسیون هتل آراد</h3>
            
            <h4>🏨 تب رک مرکزی:</h4>
            <p>• مشاهده وضعیت تمام اتاق‌ها در یک نگاه</p>
            <p>• کلیک روی هر سلول برای ثبت یا ویرایش رزرو</p>
            <p>• رنگ‌های مختلف نشان‌دهنده نوع پکیج رزرو هستند</p>
            
            <h4>👥 تب مهمانان:</h4>
            <p>• مدیریت اطلاعات مهمانان</p>
            <p>• جستجو و ویرایش اطلاعات مهمانان</p>
            
            <h4>📊 تب گزارشات:</h4>
            <p>• مشاهده گزارشات مالی و آماری</p>
            <p>• گزارش اشغال اتاق‌ها</p>
            
            <h4>⚙️ تب تنظیمات:</h4>
            <p>• مشاهده لاگ‌های سیستم</p>
            <p>• مدیریت تنظیمات برنامه</p>
            
            <hr style='border: 1px solid #bdc3c7;'>
            <p style='color: #7f8c8d; font-size: 12px;'>
            برای اطلاعات بیشتر با پشتیبانی فنی تماس بگیرید.
            </p>
            </div>
            """
            
            msg = QMessageBox()
            msg.setWindowTitle("📚 راهنمای سیستم")
            msg.setTextFormat(Qt.TextFormat.RichText)
            msg.setText(help_text)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
            
        except Exception as e:
            QMessageBox.information(self, "راهنما", "راهنمای سیستم در دست تهیه است...")

    def toggle_theme(self):
        """تغییر تم برنامه"""
        try:
            from theme_manager import ThemeManager
            theme_manager = ThemeManager()
            success = theme_manager.toggle_theme(QApplication.instance())
            
            if success:
                theme_name = "تاریک" if theme_manager.current_theme == "dark" else "روشن"
                self.statusBar().showMessage(f"✅ تم به {theme_name} تغییر کرد", 3000)
            else:
                self.statusBar().showMessage("❌ خطا در تغییر تم", 3000)
                
        except Exception as e:
            print(f"خطا در تغییر تم: {e}")
            self.statusBar().showMessage("❌ خطا در تغییر تم", 3000)

    def update_time(self):
        """به روزرسانی تاریخ و زمان در هدر"""
        try:
            # تاریخ شمسی
            jalali_date = jdatetime.date.today()
            weekday = jalali_date.strftime("%A")
            self.date_label.setText(f"📅 {jalali_date.strftime('%Y/%m/%d')} - {weekday}")
            
            # ساعت
            current_time = datetime.now().strftime("%H:%M:%S")
            self.time_label.setText(f"🕒 {current_time}")
            
        except Exception as e:
            print(f"خطا در به روزرسانی زمان: {e}")
    
    def create_header(self):
        """ایجاد هدر اصلی برنامه با طراحی مدرن و امکانات کامل"""
        header_frame = QFrame()
        header_frame.setObjectName("header_frame")
        header_frame.setFixedHeight(120)
        header_frame.setStyleSheet("""
            QFrame#header_frame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2c3e50, stop:0.3 #3498db, stop:0.7 #2980b9, stop:1 #2c3e50);
                color: white;
                border-bottom: 3px solid #1a2530;
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
                border: none;
                border-radius: 8px;
                padding: 8px 15px;
                margin: 2px;
            }
        """)
        
        # Layout اصلی هدر
        main_layout = QHBoxLayout(header_frame)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 10, 20, 10)
        
        # بخش لوگو و عنوان
        logo_section = self.create_logo_section()
        main_layout.addLayout(logo_section)
        
        # بخش آمار و اطلاعات
        stats_section = self.create_stats_section()
        main_layout.addLayout(stats_section)
        
        # بخش دکمه‌های عملیاتی
        buttons_section = self.create_buttons_section()
        main_layout.addLayout(buttons_section)
        
        # بخش تاریخ و زمان
        time_section = self.create_time_section()
        main_layout.addLayout(time_section)
        
        return header_frame
    
    def create_logo_section(self):
        """ایجاد بخش لوگو و عنوان"""
        logo_layout = QHBoxLayout()
        logo_layout.setSpacing(15)
        
        # لوگو
        logo_container = QFrame()
        logo_container.setFixedSize(80, 80)
        logo_container.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 40px;
            }
        """)
        
        logo_layout_inner = QVBoxLayout(logo_container)
        logo_label = QLabel("🏨")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("""
            QLabel {
                font-size: 40px;
                background: transparent;
                padding: 5px;
            }
        """)
        logo_layout_inner.addWidget(logo_label)
        
        # عنوان و زیرعنوان
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        main_title = QLabel("هتل آراد")
        main_title.setFont(QFont("B Titr", 24, QFont.Weight.Bold))
        main_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                background: transparent;
                padding: 0px;
                margin: 0px;
            }
        """)
        
        sub_title = QLabel("سیستم مدیریت رزرواسیون پیشرفته")
        sub_title.setFont(QFont("B Titr", 11))
        sub_title.setStyleSheet("""
            QLabel {
                color: #ecf0f1;
                font-size: 11px;
                background: transparent;
                padding: 0px;
                margin: 0px;
                opacity: 0.9;
            }
        """)
        
        title_layout.addWidget(main_title)
        title_layout.addWidget(sub_title)
        
        logo_layout.addWidget(logo_container)
        logo_layout.addLayout(title_layout)
        
        return logo_layout
    
    def create_stats_section(self):
        """ایجاد بخش آمار و اطلاعات"""
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(5)
        stats_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # آمار سریع
        stats_container = QFrame()
        stats_container.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 8px 15px;
            }
        """)
        
        stats_inner_layout = QHBoxLayout(stats_container)
        stats_inner_layout.setSpacing(20)
        
        # آمار اتاق‌های خالی
        self.available_rooms_label = QLabel("🟢 ۰ اتاق خالی")
        self.available_rooms_label.setFont(QFont("B Titr", 10))
        self.available_rooms_label.setToolTip("تعداد اتاق‌های خالی در حال حاضر")
        
        # آمار رزروهای فعال
        self.active_reservations_label = QLabel("📋 ۰ رزرو فعال")
        self.active_reservations_label.setFont(QFont("B Titr", 10))
        self.active_reservations_label.setToolTip("تعداد رزروهای فعال")
        
        # آمار مهمانان امروز
        self.today_guests_label = QLabel("👥 ۰ مهمان امروز")
        self.today_guests_label.setFont(QFont("B Titr", 10))
        self.today_guests_label.setToolTip("تعداد مهمانان امروز")
        
        stats_inner_layout.addWidget(self.available_rooms_label)
        stats_inner_layout.addWidget(self.active_reservations_label)
        stats_inner_layout.addWidget(self.today_guests_label)
        stats_inner_layout.addStretch()
        
        stats_layout.addWidget(stats_container)
        
        # به روزرسانی آمار
        QTimer.singleShot(500, self.update_header_stats)
        
        return stats_layout
    
    def create_buttons_section(self):
        """ایجاد بخش دکمه‌های عملیاتی"""
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(8)
        
        # ردیف اول دکمه‌ها
        top_buttons_layout = QHBoxLayout()
        top_buttons_layout.setSpacing(10)
        
        # دکمه ثبت رزرو جدید
        self.new_reservation_btn = QPushButton("➕ ثبت رزرو جدید")
        self.new_reservation_btn.setObjectName("new_reservation_btn")
        self.new_reservation_btn.setToolTip("ثبت رزرو جدید برای مهمان")
        self.new_reservation_btn.setFixedHeight(35)
        self.new_reservation_btn.setStyleSheet("""
            QPushButton#new_reservation_btn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #219a52);
                color: white;
                border: 2px solid #2ecc71;
                font-family: "B Titr";
                font-size: 13px;
                font-weight: bold;
                min-width: 140px;
            }
            QPushButton#new_reservation_btn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #219a52, stop:1 #1e8449);
                border: 2px solid #27ae60;
            }
            QPushButton#new_reservation_btn:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e8449, stop:1 #196f3d);
            }
        """)
        self.new_reservation_btn.clicked.connect(self.show_new_reservation_dialog)
        
        # دکمه مشاهده گزارشات
        self.reports_btn = QPushButton("📊 گزارشات فوری")
        self.reports_btn.setObjectName("reports_btn")
        self.reports_btn.setToolTip("مشاهده گزارشات سریع")
        self.reports_btn.setFixedHeight(35)
        self.reports_btn.setStyleSheet("""
            QPushButton#reports_btn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f39c12, stop:1 #e67e22);
                color: white;
                border: 2px solid #f1c40f;
                font-family: "B Titr";
                font-size: 13px;
                font-weight: bold;
                min-width: 130px;
            }
            QPushButton#reports_btn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e67e22, stop:1 #d35400);
                border: 2px solid #f39c12;
            }
        """)
        self.reports_btn.clicked.connect(self.show_quick_reports)
        
        top_buttons_layout.addWidget(self.new_reservation_btn)
        top_buttons_layout.addWidget(self.reports_btn)
        
        # ردیف دوم دکمه‌ها
        bottom_buttons_layout = QHBoxLayout()
        bottom_buttons_layout.setSpacing(10)
        
        # دکمه تغییر تم
        self.theme_btn = QPushButton("🌓 تغییر تم")
        self.theme_btn.setObjectName("theme_button")
        self.theme_btn.setToolTip("تغییر بین تم روشن و تاریک")
        self.theme_btn.setFixedHeight(30)
        self.theme_btn.setStyleSheet("""
            QPushButton#theme_button {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #9b59b6, stop:1 #8e44ad);
                color: white;
                border: 2px solid #bb8fce;
                font-family: "B Titr";
                font-size: 11px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton#theme_button:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8e44ad, stop:1 #7d3c98);
                border: 2px solid #9b59b6;
            }
        """)
        self.theme_btn.clicked.connect(self.toggle_theme)
        
        # دکمه راهنما
        help_btn = QPushButton("❓ راهنما")
        help_btn.setObjectName("help_button")
        help_btn.setToolTip("راهنمای استفاده از سیستم")
        help_btn.setFixedHeight(30)
        help_btn.setStyleSheet("""
            QPushButton#help_button {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #95a5a6, stop:1 #7f8c8d);
                color: white;
                border: 2px solid #bdc3c7;
                font-family: "B Titr";
                font-size: 11px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton#help_button:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7f8c8d, stop:1 #707b7c);
                border: 2px solid #95a5a6;
            }
        """)
        help_btn.clicked.connect(self.show_help)
        
        # دکمه خروج
        exit_btn = QPushButton("🚪 خروج")
        exit_btn.setObjectName("exit_button")
        exit_btn.setToolTip("خروج از برنامه")
        exit_btn.setFixedHeight(30)
        exit_btn.setStyleSheet("""
            QPushButton#exit_button {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e74c3c, stop:1 #c0392b);
                color: white;
                border: 2px solid #ec7063;
                font-family: "B Titr";
                font-size: 11px;
                font-weight: bold;
                min-width: 70px;
            }
            QPushButton#exit_button:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c0392b, stop:1 #a93226);
                border: 2px solid #e74c3c;
            }
        """)
        exit_btn.clicked.connect(self.close_application)
        
        bottom_buttons_layout.addWidget(self.theme_btn)
        bottom_buttons_layout.addWidget(help_btn)
        bottom_buttons_layout.addWidget(exit_btn)
        
        buttons_layout.addLayout(top_buttons_layout)
        buttons_layout.addLayout(bottom_buttons_layout)
        
        return buttons_layout
    
    def create_time_section(self):
        """ایجاد بخش تاریخ و زمان"""
        time_layout = QVBoxLayout()
        time_layout.setSpacing(5)
        time_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # تاریخ شمسی
        self.date_label = QLabel()
        self.date_label.setFont(QFont("B Titr", 12, QFont.Weight.Bold))
        self.date_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                background: transparent;
                padding: 3px 0px;
            }
        """)
        
        # ساعت
        self.time_label = QLabel()
        self.time_label.setFont(QFont("B Titr", 14, QFont.Weight.Bold))
        self.time_label.setStyleSheet("""
            QLabel {
                color: #f1c40f;
                font-size: 14px;
                background: rgba(0, 0, 0, 0.3);
                padding: 8px 12px;
                border-radius: 6px;
                border: 1px solid #f39c12;
            }
        """)
        
        time_layout.addWidget(self.date_label)
        time_layout.addWidget(self.time_label)
        
        return time_layout
    
    def update_header_stats(self):
        """به روزرسانی آمار در هدر"""
        try:
            session = self.reservation_manager.Session()
            
            # تعداد کل اتاق‌ها
            total_rooms = session.query(Room).filter(Room.is_active == True).count()
            
            # تعداد اتاق‌های خالی
            today = datetime.now().date()
            occupied_rooms = session.query(Reservation).filter(
                Reservation.check_in <= today,
                Reservation.check_out > today,
                Reservation.status.in_(['confirmed', 'checked_in'])
            ).count()
            
            available_rooms = total_rooms - occupied_rooms
            
            # تعداد رزروهای فعال
            active_reservations = session.query(Reservation).filter(
                Reservation.status.in_(['confirmed', 'checked_in'])
            ).count()
            
            # تعداد مهمانان امروز
            today_guests = session.query(Reservation).filter(
                Reservation.check_in <= today,
                Reservation.check_out > today,
                Reservation.status.in_(['confirmed', 'checked_in'])
            ).count()
            
            session.close()
            
            # به روزرسانی labels
            self.available_rooms_label.setText(f"🟢 {available_rooms} اتاق خالی")
            self.active_reservations_label.setText(f"📋 {active_reservations} رزرو فعال")
            self.today_guests_label.setText(f"👥 {today_guests} مهمان امروز")
            
        except Exception as e:
            print(f"خطا در به روزرسانی آمار هدر: {e}")
            self.available_rooms_label.setText("🟢 خطا در بارگذاری")
            self.active_reservations_label.setText("📋 خطا در بارگذاری")
            self.today_guests_label.setText("👥 خطا در بارگذاری")
    
    def close_application(self):
        """بستن برنامه با تایید کاربر"""
        reply = QMessageBox.question(
            self,
            "تایید خروج",
            "آیا از خروج از برنامه اطمینان دارید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.close()
    
    def show_quick_reports(self):
        """نمایش گزارشات فوری"""
        try:
            session = self.reservation_manager.Session()
            
            # آمار سریع
            total_rooms = session.query(Room).filter(Room.is_active == True).count()
            total_reservations = session.query(Reservation).count()
            total_guests = session.query(Guest).count()
            
            # رزروهای امروز
            today = datetime.now().date()
            today_reservations = session.query(Reservation).filter(
                Reservation.check_in <= today,
                Reservation.check_out > today
            ).count()
            
            session.close()
            
            report_text = f"""
            <div style='font-family: "B Titr"; text-align: right; line-height: 1.8;'>
            <h3 style='color: #2c3e50;'>📊 گزارش فوری سیستم</h3>
            
            <p>🏨 <b>تعداد اتاق‌ها:</b> {total_rooms} اتاق</p>
            <p>📋 <b>کل رزروها:</b> {total_reservations} رزرو</p>
            <p>👥 <b>کل مهمانان:</b> {total_guests} مهمان</p>
            <p>📅 <b>رزروهای امروز:</b> {today_reservations} رزرو</p>
            
            <hr style='border: 1px solid #bdc3c7;'>
            <p style='color: #7f8c8d; font-size: 12px;'>
            برای گزارشات کامل به تب "📊 گزارشات" مراجعه کنید.
            </p>
            </div>
            """
            
            msg = QMessageBox()
            msg.setWindowTitle("📊 گزارشات فوری")
            msg.setTextFormat(Qt.TextFormat.RichText)
            msg.setText(report_text)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
            
        except Exception as e:
            QMessageBox.warning(self, "خطا", f"خطا در تولید گزارش: {str(e)}")

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