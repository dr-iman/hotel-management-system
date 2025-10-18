from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QFrame, QGridLayout, QTabWidget, QLineEdit,
                            QPushButton, QMessageBox, QDialog, QFormLayout,
                            QComboBox, QSpinBox, QDateEdit, QDialogButtonBox,
                            QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor
from datetime import datetime, timedelta
import sys
import os

# اضافه کردن مسیرها به sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'models'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from reservation_manager import ReservationManager
from models import Reservation, Room, Guest
from jalali import JalaliDate
import jdatetime

from rack_widget import RackWidget
from ui.guests_tab import GuestsTab
from ui.reports_tab import ReportsTab

class JalaliDateEdit(QDateEdit):
    """ویجت ویرایش تاریخ شمسی"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.setDisplayFormat("yyyy/MM/dd")
        
    def setJalaliDate(self, jalali_date):
        """تنظیم تاریخ شمسی"""
        gregorian_date = jalali_date.togregorian()
        self.setDate(gregorian_date)
    
    def getJalaliDate(self):
        """دریافت تاریخ شمسی"""
        gregorian_date = self.date().toPyDate()
        return jdatetime.date.fromgregorian(date=gregorian_date)

class ReservationDialog(QDialog):
    def __init__(self, reservation_manager, selected_room=None, selected_date=None, parent=None):
        super().__init__(parent)
        self.reservation_manager = reservation_manager
        self.selected_room = selected_room
        self.selected_date = selected_date
        self.setWindowTitle("ثبت رزرو جدید")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setup_ui()
        self.load_available_rooms()
        
        # اگر اتاق و تاریخ مشخص شده، پیش‌پر کردن فرم
        if selected_room and selected_date:
            self.prefill_form()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # فیلدهای فرم
        form_layout = QFormLayout()
        
        self.first_name = QLineEdit()
        self.last_name = QLineEdit()
        self.phone = QLineEdit()
        self.email = QLineEdit()
        
        self.adults_spin = QSpinBox()
        self.adults_spin.setRange(1, 10)
        self.adults_spin.setValue(2)
        self.adults_spin.valueChanged.connect(self.on_guests_changed)
        
        self.children_spin = QSpinBox()
        self.children_spin.setRange(0, 10)
        self.children_spin.valueChanged.connect(self.on_guests_changed)
        
        # فیلد تعداد روزهای اقامت
        self.nights_spin = QSpinBox()
        self.nights_spin.setRange(1, 30)
        self.nights_spin.setValue(1)
        self.nights_spin.valueChanged.connect(self.on_nights_changed)
        
        # نوع پکیج
        self.package_combo = QComboBox()
        self.package_combo.addItems(["فول برد", "اسکان + صبحانه", "فقط اسکان"])
        
        # نوع مهمان
        self.guest_type_combo = QComboBox()
        self.guest_type_combo.addItems(["حضوری", "آژانس", "رزرو", "سایت", "اینستاگرام"])
        
        # تاریخ‌های شمسی
        self.checkin_date = JalaliDateEdit()
        today_jalali = jdatetime.date.today()
        self.checkin_date.setJalaliDate(today_jalali)
        self.checkin_date.dateChanged.connect(self.on_checkin_changed)
        
        self.checkout_date = JalaliDateEdit()
        self.update_checkout_date()
        
        # لیست اتاق‌های پیشنهادی
        self.suggested_rooms_list = QListWidget()
        self.suggested_rooms_list.itemDoubleClicked.connect(self.on_room_selected)
        
        form_layout.addRow("نام:", self.first_name)
        form_layout.addRow("نام خانوادگی:", self.last_name)
        form_layout.addRow("تلفن:", self.phone)
        form_layout.addRow("ایمیل:", self.email)
        form_layout.addRow("تعداد بزرگسال:", self.adults_spin)
        form_layout.addRow("تعداد کودک:", self.children_spin)
        form_layout.addRow("تعداد روزهای اقامت:", self.nights_spin)
        form_layout.addRow("نوع پکیج:", self.package_combo)
        form_layout.addRow("نوع مهمان:", self.guest_type_combo)
        form_layout.addRow("تاریخ ورود:", self.checkin_date)
        form_layout.addRow("تاریخ خروج:", self.checkout_date)
        form_layout.addRow("اتاق‌های پیشنهادی:", self.suggested_rooms_list)
        
        layout.addLayout(form_layout)
        
        # دکمه‌ها
        button_layout = QHBoxLayout()
        self.submit_btn = QPushButton("ثبت رزرو")
        self.submit_btn.clicked.connect(self.submit_reservation)
        
        cancel_btn = QPushButton("انصراف")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.submit_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
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
                self.suggested_rooms_list.addItem("⚠️ تاریخ خروج باید بعد از تاریخ ورود باشد")
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
                    item_text = f"اتاق {room.room_number} - {room.room_type} - ظرفیت: {room.capacity} - قیمت: {room.price_per_night:,} تومان"
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
                self.suggested_rooms_list.addItem("❌ هیچ اتاق خالی با ظرفیت مورد نظر یافت نشد")
                
        except Exception as e:
            print(f"خطا در بارگذاری اتاق‌ها: {e}")
            self.suggested_rooms_list.addItem(f"خطا در بارگذاری: {str(e)}")
        finally:
            if 'session' in locals():
                session.close()
    
    def submit_reservation(self):
        """ثبت رزرو جدید"""
        try:
            if self.suggested_rooms_list.currentItem() is None:
                QMessageBox.warning(self, "خطا", "لطفاً یک اتاق از لیست انتخاب کنید")
                return
            
            room_data = self.suggested_rooms_list.currentItem().data(Qt.ItemDataRole.UserRole)
            if not room_data:
                QMessageBox.warning(self, "خطا", "اتاق انتخاب شده معتبر نیست")
                return
            
            # ایجاد مهمان جدید
            session = self.reservation_manager.Session()
            
            guest = Guest(
                first_name=self.first_name.text(),
                last_name=self.last_name.text(),
                phone=self.phone.text(),
                email=self.email.text(),
                nationality="ایرانی"
            )
            session.add(guest)
            session.commit()
            
            # ایجاد رزرو
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
            
            reservation = Reservation(
                room_id=room_data['id'],
                guest_id=guest.id,
                check_in=check_in,
                check_out=check_out,
                status='confirmed',
                adults=self.adults_spin.value(),
                children=self.children_spin.value(),
                total_amount=total_amount,
                paid_amount=0,
                package_type=self.package_combo.currentText(),
                guest_type=self.guest_type_combo.currentText()
            )
            
            session.add(reservation)
            session.commit()
            session.close()
            
            QMessageBox.information(self, "موفق", "رزرو با موفقیت ثبت شد!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در ثبت رزرو: {str(e)}")

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
        if hasattr(self.rack_tab, 'cell_clicked'):
            self.rack_tab.cell_clicked.connect(self.on_rack_cell_clicked)
        tabs.addTab(self.rack_tab, "📋 رک مرکزی")
        
        # تب مهمانان
        self.guests_tab = GuestsTab(self.reservation_manager)
        tabs.addTab(self.guests_tab, "👥 مهمانان")
        
        # تب گزارشات
        self.reports_tab = ReportsTab(self.reservation_manager)
        tabs.addTab(self.reports_tab, "📊 گزارشات")
        
        # تب تنظیمات
        tabs.addTab(QWidget(), "⚙️ تنظیمات")
        
        layout.addWidget(tabs)
    
    def create_header(self):
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2c3e50, stop:1 #3498db);
                color: white;
                padding: 10px;
                border-radius: 4px;
            }
            QLabel {
                color: white;
                font-weight: bold;
            }
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        
        layout = QHBoxLayout()
        
        # عنوان
        title_label = QLabel("هتل آراد - سیستم مدیریت رزرواسیون")
        title_label.setFont(QFont("Tahoma", 14, QFont.Weight.Bold))
        
        # دکمه ثبت رزرو جدید
        new_reservation_btn = QPushButton("➕ ثبت رزرو جدید")
        new_reservation_btn.clicked.connect(self.show_new_reservation_dialog)
        
        # تاریخ و ساعت شمسی
        self.time_label = QLabel()
        self.update_time()
        
        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(new_reservation_btn)
        layout.addWidget(self.time_label)
        
        header_frame.setLayout(layout)
        return header_frame
    
    def update_time(self):
        current_time = JalaliDate.now().strftime("%Y/%m/%d %H:%M:%S")
        self.time_label.setText(f"📅 {current_time}")
    

    def show_new_reservation_dialog(self, room_number=None, selected_date=None):
        """نمایش دیالوگ ثبت رزرو جدید"""
        dialog = ReservationDialog(self.reservation_manager, room_number, selected_date, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # تاخیر در بروزرسانی رک برای جلوگیری از conflict
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, self.delayed_refresh_rack)
    
    def delayed_refresh_rack(self):
        """بروزرسانی رک با تاخیر"""
        if hasattr(self.rack_tab, 'load_rack_data'):
            try:
                self.rack_tab.load_rack_data()
            except Exception as e:
                print(f"خطا در بروزرسانی رک: {e}")
    
    def on_rack_cell_clicked(self, room_number, jalali_date):
        """هنگام کلیک روی سلول در رک"""
        self.show_new_reservation_dialog(room_number, jalali_date)