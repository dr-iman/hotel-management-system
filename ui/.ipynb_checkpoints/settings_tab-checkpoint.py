from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QTableWidget, QTableWidgetItem, QHeaderView,
                            QComboBox, QLineEdit, QPushButton, QDateEdit,
                            QFormLayout, QGroupBox, QMessageBox, QScrollArea,
                            QTabWidget, QSpinBox, QDoubleSpinBox, QCheckBox,
                            QColorDialog, QInputDialog, QToolBar, QStatusBar,
                            QSplitter, QTextEdit, QDialog, QDialogButtonBox,
                            QListWidget, QListWidgetItem, QStackedWidget)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QAction, QPixmap
import sys
import os
import jdatetime
import json
import hashlib
from datetime import datetime, timedelta
import secrets
import string

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'models'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from reservation_manager import ReservationManager
from models.models import SystemLog
from jalali import JalaliDate

class JalaliDateFilterEdit(QDateEdit):
    """ویجت ویرایش تاریخ شمسی برای فیلتر"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.setDisplayFormat("yyyy/MM/dd")
        
        # تنظیم minimum و maximum date
        from PyQt6.QtCore import QDate
        min_date = QDate(1400, 1, 1)  # سال 1400 شمسی
        max_date = QDate(1500, 12, 29)  # سال 1500 شمسی
        self.setDateRange(min_date, max_date)
        
        # تنظیم تاریخ پیش‌فرض
        today_jalali = jdatetime.date.today()
        self.setJalaliDate(today_jalali)
        
    def setJalaliDate(self, jalali_date):
        """تنظیم تاریخ شمسی"""
        from PyQt6.QtCore import QDate
        qdate = QDate(jalali_date.year, jalali_date.month, jalali_date.day)
        self.setDate(qdate)
    
    def getJalaliDate(self):
        """دریافت تاریخ شمسی"""
        qdate = self.date()
        return jdatetime.date(qdate.year(), qdate.month(), qdate.day())

class SettingsTab(QWidget):
    def __init__(self, reservation_manager):
        super().__init__()
        self.reservation_manager = reservation_manager
        self.setup_ui()
        self.load_logs_data()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_logs_data)
        self.timer.start(30000)
    
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
        title_label = QLabel("⚙️ تنظیمات سیستم - لاگ تغییرات")
        title_label.setFont(QFont("B Titr", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("padding: 20px; color: #2c3e50;")
        layout.addWidget(title_label)
        
        # فیلترهای جستجو
        filter_group = self.create_filters()
        layout.addWidget(filter_group)
        
        # آمار سریع
        stats_layout = self.create_quick_stats()
        layout.addLayout(stats_layout)
        
        # جدول لاگ‌ها
        logs_label = QLabel("📋 تاریخچه تغییرات سیستم")
        logs_label.setFont(QFont("B Titr", 14, QFont.Weight.Bold))
        logs_label.setStyleSheet("padding: 10px; color: #2c3e50;")
        layout.addWidget(logs_label)
        
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(7)
        self.logs_table.setHorizontalHeaderLabels([
            "تاریخ و زمان", 
            "عملیات", 
            "جدول", 
            "رکورد ID", 
            "کاربر", 
            "توضیحات", 
            "تغییرات"
        ])
        self.logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.logs_table.setAlternatingRowColors(True)
        self.logs_table.setMinimumHeight(300)
        self.logs_table.setStyleSheet("""
            QTableWidget {
                alternate-background-color: #f8f9fa;
                background-color: white;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #dee2e6;
            }
        """)
        layout.addWidget(self.logs_table)
        
        # دکمه‌های مدیریت
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 بروزرسانی")
        refresh_btn.clicked.connect(self.load_logs_data)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        clear_filters_btn = QPushButton("🗑️ حذف فیلترها")
        clear_filters_btn.clicked.connect(self.clear_filters)
        clear_filters_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        
        clear_old_btn = QPushButton("🗑️ پاک کردن لاگ‌های قدیمی")
        clear_old_btn.clicked.connect(self.clear_old_logs)
        clear_old_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        export_btn = QPushButton("📤 خروجی Excel")
        export_btn.clicked.connect(self.export_logs)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        
        button_layout.addWidget(refresh_btn)
        button_layout.addWidget(clear_filters_btn)
        button_layout.addWidget(clear_old_btn)
        button_layout.addWidget(export_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        # تنظیم ویجت اصلی برای scroll area
        scroll_area.setWidget(main_widget)
        
        # تنظیم layout اصلی
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.addWidget(scroll_area)
    
    def create_filters(self):
        """ایجاد فیلترهای جستجو"""
        group = QGroupBox("فیلترهای پیشرفته جستجو")
        layout = QVBoxLayout()
        
        # ردیف اول فیلترها
        first_row = QHBoxLayout()
        
        # فیلتر عملیات
        first_row.addWidget(QLabel("عملیات:"))
        self.action_filter = QComboBox()
        self.action_filter.addItems(["همه", "create", "update", "delete"])
        self.action_filter.currentTextChanged.connect(self.load_logs_data)
        first_row.addWidget(self.action_filter)
        
        # فیلتر جدول
        first_row.addWidget(QLabel("جدول:"))
        self.table_filter = QComboBox()
        self.table_filter.addItems(["همه", "reservations", "guests", "rooms"])
        self.table_filter.currentTextChanged.connect(self.load_logs_data)
        first_row.addWidget(self.table_filter)
        
        # فیلتر کاربر
        first_row.addWidget(QLabel("کاربر:"))
        self.user_filter = QLineEdit()
        self.user_filter.setPlaceholderText("نام کاربر...")
        self.user_filter.textChanged.connect(self.load_logs_data)
        first_row.addWidget(self.user_filter)
        
        first_row.addStretch()
        
        # ردیف دوم فیلترها - تاریخ
        second_row = QHBoxLayout()
        
        # فیلتر تاریخ از
        second_row.addWidget(QLabel("تاریخ از:"))
        self.date_from_filter = JalaliDateFilterEdit()
        self.date_from_filter.dateChanged.connect(self.load_logs_data)
        second_row.addWidget(self.date_from_filter)
        
        # فیلتر تاریخ تا
        second_row.addWidget(QLabel("تاریخ تا:"))
        self.date_to_filter = JalaliDateFilterEdit()
        self.date_to_filter.dateChanged.connect(self.load_logs_data)
        second_row.addWidget(self.date_to_filter)
        
        # دکمه امروز
        today_btn = QPushButton("امروز")
        today_btn.clicked.connect(self.set_today_filter)
        today_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        second_row.addWidget(today_btn)
        
        # دکمه هفته جاری
        week_btn = QPushButton("هفته جاری")
        week_btn.clicked.connect(self.set_week_filter)
        week_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        second_row.addWidget(week_btn)
        
        # دکمه ماه جاری
        month_btn = QPushButton("ماه جاری")
        month_btn.clicked.connect(self.set_month_filter)
        month_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        second_row.addWidget(month_btn)
        
        second_row.addStretch()
        
        layout.addLayout(first_row)
        layout.addLayout(second_row)
        group.setLayout(layout)
        return group
    
    def create_quick_stats(self):
        """ایجاد آمار سریع"""
        layout = QHBoxLayout()
        
        # کارت آمار
        stats_data = [
            ("تغییرات امروز", "0", "#3498db"),
            ("تغییرات هفته", "0", "#2ecc71"),
            ("تغییرات ماه", "0", "#e74c3c"),
            ("کاربران فعال", "0", "#f39c12")
        ]
        
        for title, value, color in stats_data:
            card = self.create_stat_card(title, value, color)
            layout.addWidget(card)
        
        return layout
    
    def create_stat_card(self, title, value, color):
        """ایجاد کارت آمار"""
        from PyQt6.QtWidgets import QFrame
        
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
    
    def set_today_filter(self):
        """تنظیم فیلتر برای امروز"""
        today = jdatetime.date.today()
        self.date_from_filter.setJalaliDate(today)
        self.date_to_filter.setJalaliDate(today)
        self.load_logs_data()
    
    def set_week_filter(self):
        """تنظیم فیلتر برای هفته جاری"""
        today = jdatetime.date.today()
        start_of_week = today - jdatetime.timedelta(days=today.weekday())
        end_of_week = start_of_week + jdatetime.timedelta(days=6)
        
        self.date_from_filter.setJalaliDate(start_of_week)
        self.date_to_filter.setJalaliDate(end_of_week)
        self.load_logs_data()
    
    def set_month_filter(self):
        """تنظیم فیلتر برای ماه جاری"""
        today = jdatetime.date.today()
        start_of_month = jdatetime.date(today.year, today.month, 1)
        
        # پیدا کردن آخرین روز ماه
        if today.month == 12:
            end_of_month = jdatetime.date(today.year + 1, 1, 1) - jdatetime.timedelta(days=1)
        else:
            end_of_month = jdatetime.date(today.year, today.month + 1, 1) - jdatetime.timedelta(days=1)
        
        self.date_from_filter.setJalaliDate(start_of_month)
        self.date_to_filter.setJalaliDate(end_of_month)
        self.load_logs_data()
    
    def clear_filters(self):
        """حذف تمام فیلترها"""
        self.action_filter.setCurrentText("همه")
        self.table_filter.setCurrentText("همه")
        self.user_filter.clear()
        
        # تنظیم تاریخ به محدوده وسیع
        from PyQt6.QtCore import QDate
        self.date_from_filter.setDate(QDate(1400, 1, 1))
        self.date_to_filter.setDate(QDate(1500, 12, 29))
        
        self.load_logs_data()
    
    def load_logs_data(self):
        """بارگذاری داده‌های لاگ با فیلترها"""
        try:
            # دریافت لاگ‌ها از reservation_manager
            date_from = self.date_from_filter.getJalaliDate()
            date_to = self.date_to_filter.getJalaliDate()
            
            # تبدیل تاریخ شمسی به میلادی
            date_from_gregorian = datetime.combine(date_from.togregorian(), datetime.min.time()) if date_from else None
            date_to_gregorian = datetime.combine(date_to.togregorian(), datetime.max.time()) if date_to else None
            
            logs = self.reservation_manager.get_system_logs(
                action_filter=self.action_filter.currentText() if self.action_filter.currentText() != "همه" else None,
                table_filter=self.table_filter.currentText() if self.table_filter.currentText() != "همه" else None,
                user_filter=self.user_filter.text().strip() or None,
                date_from=date_from_gregorian,
                date_to=date_to_gregorian,
                limit=1000
            )
            
            # پر کردن جدول
            self.logs_table.setRowCount(len(logs))
            
            for row, log in enumerate(logs):
                # تاریخ و زمان شمسی
                jalali_datetime = jdatetime.datetime.fromgregorian(datetime=log.changed_at)
                date_time_str = jalali_datetime.strftime("%Y/%m/%d %H:%M")
                
                # عملیات با آیکون
                action_icons = {"create": "➕", "update": "✏️", "delete": "🗑️"}
                action_text = f"{action_icons.get(log.action, '📝')} {log.action}"
                
                # ایجاد آیتم‌های جدول
                self.logs_table.setItem(row, 0, QTableWidgetItem(date_time_str))
                self.logs_table.setItem(row, 1, QTableWidgetItem(action_text))
                self.logs_table.setItem(row, 2, QTableWidgetItem(log.table_name))
                self.logs_table.setItem(row, 3, QTableWidgetItem(str(log.record_id)))
                self.logs_table.setItem(row, 4, QTableWidgetItem(log.changed_by))
                self.logs_table.setItem(row, 5, QTableWidgetItem(log.description or ""))
                
                # نمایش تغییرات - با هندلینگ خطا
                try:
                    changes_text = self.format_changes(log.old_data, log.new_data)
                except Exception as e:
                    changes_text = f"خطا در نمایش تغییرات: {str(e)}"
                
                changes_item = QTableWidgetItem(changes_text)
                
                # رنگ‌بندی بر اساس نوع عملیات
                if log.action == "create":
                    changes_item.setBackground(QColor("#d4edda"))  # سبز روشن
                elif log.action == "update":
                    changes_item.setBackground(QColor("#fff3cd"))  # زرد روشن
                elif log.action == "delete":
                    changes_item.setBackground(QColor("#f8d7da"))  # قرمز روشن
                
                self.logs_table.setItem(row, 6, changes_item)
            
            # بروزرسانی آمار
            self.update_quick_stats()
            
        except Exception as e:
            print(f"خطا در بارگذاری لاگ‌ها: {e}")
            import traceback
            traceback.print_exc()
    
    def safe_json_load(self, data):
        """تبدیل امن JSON به دیکشنری"""
        if data is None:
            return None
        try:
            if isinstance(data, str):
                return json.loads(data)
            elif isinstance(data, dict):
                return data
            else:
                return None
        except:
            return None
    
    def format_changes(self, old_data, new_data):
        """فرمت‌دهی تغییرات برای نمایش"""
        # تبدیل امن JSON به دیکشنری
        old_dict = self.safe_json_load(old_data)
        new_dict = self.safe_json_load(new_data)
        
        if not old_dict and not new_dict:
            return "بدون تغییرات جزئیات"
        
        if not old_dict:  # ایجاد جدید
            return "رکورد جدید ایجاد شد"
        
        if not new_dict:  # حذف
            return "رکورد حذف شد"
        
        # پیدا کردن فیلدهای تغییر کرده
        changes = []
        all_keys = set()
        if old_dict:
            all_keys.update(old_dict.keys())
        if new_dict:
            all_keys.update(new_dict.keys())
        
        for key in all_keys:
            old_val = old_dict.get(key) if old_dict else None
            new_val = new_dict.get(key) if new_dict else None
            
            if old_val != new_val:
                # فرمت‌دهی مقادیر
                old_display = self.format_value(key, old_val)
                new_display = self.format_value(key, new_val)
                
                changes.append(f"{key}: {old_display} → {new_display}")
        
        return " | ".join(changes) if changes else "بدون تغییرات جزئیات"
    
    def format_value(self, key, value):
        """فرمت‌دهی مقدار برای نمایش"""
        if value is None:
            return "خالی"
        
        if key in ['check_in', 'check_out'] and value:
            try:
                # تبدیل تاریخ میلادی به شمسی
                if 'T' in value:
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                else:
                    dt = datetime.fromisoformat(value)
                jalali_date = jdatetime.date.fromgregorian(date=dt.date())
                return jalali_date.strftime("%Y/%m/%d")
            except:
                return str(value)
        
        if key in ['total_amount', 'price_per_night'] and value:
            return f"{float(value):,} تومان"
        
        return str(value)
    
    def update_quick_stats(self):
        """بروزرسانی آمار سریع"""
        try:
            # دریافت آمار از reservation_manager
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = today_start - timedelta(days=7)
            month_start = today_start.replace(day=1)
            
            # استفاده از فیلترهای فعلی برای آمار
            date_from = self.date_from_filter.getJalaliDate()
            date_to = self.date_to_filter.getJalaliDate()
            
            date_from_gregorian = datetime.combine(date_from.togregorian(), datetime.min.time()) if date_from else None
            date_to_gregorian = datetime.combine(date_to.togregorian(), datetime.max.time()) if date_to else None
            
            # دریافت لاگ‌ها برای آمار
            today_logs = self.reservation_manager.get_system_logs(
                date_from=today_start,
                limit=10000
            )
            
            week_logs = self.reservation_manager.get_system_logs(
                date_from=week_start,
                limit=10000
            )
            
            month_logs = self.reservation_manager.get_system_logs(
                date_from=month_start,
                limit=10000
            )
            
            # کاربران فعال
            active_users = len(self.reservation_manager.get_active_users())
            
            # بروزرسانی کارت‌ها
            stats_layout = self.layout().itemAt(2)  # موقعیت آمار در layout
            if stats_layout:
                for i, count in enumerate([len(today_logs), len(week_logs), len(month_logs), active_users]):
                    card = stats_layout.itemAt(i).widget()
                    if card:
                        value_label = card.layout().itemAt(1).widget()
                        value_label.setText(str(count))
                        
        except Exception as e:
            print(f"خطا در بروزرسانی آمار: {e}")
    
    def clear_old_logs(self):
        """پاک کردن لاگ‌های قدیمی"""
        reply = QMessageBox.question(
            self, 
            "تأیید پاک کردن", 
            "آیا از پاک کردن لاگ‌های قدیمی تر از 3 ماه اطمینان دارید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                deleted_count = self.reservation_manager.clear_old_logs(days=90)
                self.load_logs_data()
                
                QMessageBox.information(
                    self, 
                    "موفق", 
                    f"{deleted_count} لاگ قدیمی پاک شد"
                )
                
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در پاک کردن لاگ‌ها: {str(e)}")
    
    def export_logs(self):
        """خروجی گرفتن از لاگ‌ها (نمایشی)"""
        QMessageBox.information(
            self, 
            "خروجی", 
            "این قابلیت در نسخه بعدی پیاده‌سازی خواهد شد"
        )
        
class UserManager:
    """مدیریت کاربران سیستم"""
    
    def __init__(self):
        self.users_file = "users.json"
        self.default_users = {
            "admin": {
                "password": self.hash_password("admin123"),
                "role": "admin",
                "full_name": "مدیر سیستم",
                "email": "admin@hotel.com",
                "phone": "09123456789",
                "is_active": True,
                "permissions": ["all"],
                "created_at": datetime.now().isoformat()
            },
            "reception": {
                "password": self.hash_password("reception123"),
                "role": "reception",
                "full_name": "اپراتور پذیرش",
                "email": "reception@hotel.com", 
                "phone": "09123456780",
                "is_active": True,
                "permissions": ["reservation_view", "reservation_edit", "guest_management"],
                "created_at": datetime.now().isoformat()
            }
        }
        self.load_users()
    
    def hash_password(self, password):
        """هش کردن رمز عبور"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def generate_password(self, length=12):
        """تولید رمز عبور تصادفی"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def load_users(self):
        """بارگذاری کاربران از فایل"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
            else:
                self.users = self.default_users
                self.save_users()
        except Exception as e:
            print(f"خطا در بارگذاری کاربران: {e}")
            self.users = self.default_users
    
    def save_users(self):
        """ذخیره کاربران در فایل"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"خطا در ذخیره کاربران: {e}")
    
    def authenticate(self, username, password):
        """احراز هویت کاربر"""
        user = self.users.get(username)
        if user and user.get('is_active', True):
            return user['password'] == self.hash_password(password)
        return False
    
    def add_user(self, username, user_data):
        """افزودن کاربر جدید"""
        if username in self.users:
            return False, "نام کاربری تکراری است"
        
        self.users[username] = user_data
        self.save_users()
        return True, "کاربر با موفقیت افزوده شد"
    
    def update_user(self, username, user_data):
        """بروزرسانی کاربر"""
        if username not in self.users:
            return False, "کاربر یافت نشد"
        
        self.users[username] = {**self.users[username], **user_data}
        self.save_users()
        return True, "کاربر با موفقیت بروزرسانی شد"
    
    def delete_user(self, username):
        """حذف کاربر"""
        if username not in self.users:
            return False, "کاربر یافت نشد"
        
        if username == "admin":
            return False, "کاربر admin قابل حذف نیست"
        
        del self.users[username]
        self.save_users()
        return True, "کاربر با موفقیت حذف شد"

class ColorManager:
    """مدیریت رنگ‌بندی سیستم"""
    
    def __init__(self):
        self.color_schemes_file = "color_schemes.json"
        self.default_schemes = {
            "default": {
                "name": "پالت پیشفرض",
                "colors": {
                    "فول برد": "#E74C3C",
                    "اسکان + صبحانه": "#27AE60",
                    "فقط اسکان": "#2980B9",
                    "پکیج ویژه": "#8E44AD",
                    "اتاق خالی": "#ECF0F1",
                    "اتاق اشغال شده": "#E74C3C",
                    "اتاق رزرو شده": "#3498DB",
                    "اتاق در حال نظافت": "#F39C12",
                    "اتاق تعمیر": "#95A5A6",
                    "back_to_back_start": "#FFA500",
                    "back_to_back_end": "#FF8C00"
                }
            },
            "pastel": {
                "name": "پالت پاستل",
                "colors": {
                    "فول برد": "#FFB8B8",
                    "اسکان + صبحانه": "#B8FFC8", 
                    "فقط اسکان": "#B8D4FF",
                    "پکیج ویژه": "#E8B8FF",
                    "اتاق خالی": "#F5F5F5",
                    "اتاق اشغال شده": "#FFB8B8",
                    "اتاق رزرو شده": "#B8D4FF",
                    "اتاق در حال نظافت": "#FFE6B8",
                    "اتاق تعمیر": "#E0E0E0",
                    "back_to_back_start": "#FFD700",
                    "back_to_back_end": "#FFA500"
                }
            }
        }
        self.load_color_schemes()
    
    def load_color_schemes(self):
        """بارگذاری پالت‌های رنگی"""
        try:
            if os.path.exists(self.color_schemes_file):
                with open(self.color_schemes_file, 'r', encoding='utf-8') as f:
                    self.schemes = json.load(f)
            else:
                self.schemes = self.default_schemes
                self.save_color_schemes()
        except Exception as e:
            print(f"خطا در بارگذاری پالت‌ها: {e}")
            self.schemes = self.default_schemes
    
    def save_color_schemes(self):
        """ذخیره پالت‌های رنگی"""
        try:
            with open(self.color_schemes_file, 'w', encoding='utf-8') as f:
                json.dump(self.schemes, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"خطا در ذخیره پالت‌ها: {e}")
    
    def get_color(self, scheme_name, color_key):
        """دریافت رنگ از پالت"""
        return self.schemes.get(scheme_name, {}).get('colors', {}).get(color_key, "#CCCCCC")
    
    def set_color(self, scheme_name, color_key, color_hex):
        """تنظیم رنگ در پالت"""
        if scheme_name not in self.schemes:
            self.schemes[scheme_name] = {"name": scheme_name, "colors": {}}
        
        self.schemes[scheme_name]["colors"][color_key] = color_hex
        self.save_color_schemes()
    
    def create_scheme(self, scheme_name, base_scheme="default"):
        """ایجاد پالت جدید"""
        if scheme_name in self.schemes:
            return False, "پالت با این نام وجود دارد"
        
        self.schemes[scheme_name] = {
            "name": scheme_name,
            "colors": self.schemes[base_scheme]["colors"].copy()
        }
        self.save_color_schemes()
        return True, "پالت با موفقیت ایجاد شد"

class RateManager:
    """مدیریت نرخ و تعرفه‌ها"""
    
    def __init__(self):
        self.rates_file = "room_rates.json"
        self.default_rates = {
            "room_types": {
                "سینگل": {"base_rate": 80, "weekend_rate": 100, "capacity": 1},
                "دبل": {"base_rate": 120, "weekend_rate": 150, "capacity": 2},
                "تویین": {"base_rate": 130, "weekend_rate": 160, "capacity": 2},
                "سوئیت": {"base_rate": 200, "weekend_rate": 250, "capacity": 4},
                "دیلوکس": {"base_rate": 180, "weekend_rate": 220, "capacity": 3}
            },
            "packages": {
                "فقط اسکان": {"multiplier": 1.0},
                "اسکان + صبحانه": {"multiplier": 1.2},
                "فول برد": {"multiplier": 1.5},
                "پکیج ویژه": {"multiplier": 1.8}
            },
            "seasons": {
                "عادی": {"multiplier": 1.0},
                "فصل": {"multiplier": 1.3},
                "تعطیلات": {"multiplier": 1.5}
            }
        }
        self.load_rates()
    
    def load_rates(self):
        """بارگذاری نرخ‌ها"""
        try:
            if os.path.exists(self.rates_file):
                with open(self.rates_file, 'r', encoding='utf-8') as f:
                    self.rates = json.load(f)
            else:
                self.rates = self.default_rates
                self.save_rates()
        except Exception as e:
            print(f"خطا در بارگذاری نرخ‌ها: {e}")
            self.rates = self.default_rates
    
    def save_rates(self):
        """ذخیره نرخ‌ها"""
        try:
            with open(self.rates_file, 'w', encoding='utf-8') as f:
                json.dump(self.rates, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"خطا در ذخیره نرخ‌ها: {e}")
    
    def calculate_rate(self, room_type, package, season, nights, is_weekend=False):
        """محاسبه نرخ نهایی"""
        room_rate = self.rates["room_types"][room_type]
        package_multiplier = self.rates["packages"][package]["multiplier"]
        season_multiplier = self.rates["seasons"][season]["multiplier"]
        
        base_rate = room_rate["weekend_rate"] if is_weekend else room_rate["base_rate"]
        total = base_rate * package_multiplier * season_multiplier * nights
        
        return round(total, 2)

class UserDialog(QDialog):
    """دیالوگ مدیریت کاربر"""
    
    def __init__(self, user_manager, username=None, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.username = username
        self.is_edit = username is not None
        
        self.setWindowTitle("✏️ مدیریت کاربر" if self.is_edit else "➕ کاربر جدید")
        self.setFixedSize(500, 600)
        self.setup_ui()
        
        if self.is_edit:
            self.load_user_data()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # فرم اطلاعات کاربر
        form_group = QGroupBox("اطلاعات کاربر")
        form_layout = QFormLayout()
        
        self.username_edit = QLineEdit()
        self.username_edit.setEnabled(not self.is_edit)
        
        self.fullname_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        
        self.role_combo = QComboBox()
        self.role_combo.addItems(["admin", "reception", "housekeeping", "manager"])
        
        self.status_check = QCheckBox("کاربر فعال")
        self.status_check.setChecked(True)
        
        # بخش رمز عبور
        password_layout = QHBoxLayout()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("رمز عبور جدید")
        
        generate_btn = QPushButton("🎲 تولید رمز")
        generate_btn.clicked.connect(self.generate_password)
        generate_btn.setFixedWidth(100)
        
        show_btn = QPushButton("👁️")
        show_btn.clicked.connect(self.toggle_password_visibility)
        show_btn.setFixedWidth(40)
        
        password_layout.addWidget(self.password_edit)
        password_layout.addWidget(generate_btn)
        password_layout.addWidget(show_btn)
        
        form_layout.addRow("نام کاربری:", self.username_edit)
        form_layout.addRow("نام کامل:", self.fullname_edit)
        form_layout.addRow("ایمیل:", self.email_edit)
        form_layout.addRow("تلفن:", self.phone_edit)
        form_layout.addRow("نقش:", self.role_combo)
        form_layout.addRow("رمز عبور:", password_layout)
        form_layout.addRow("", self.status_check)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # دسترسی‌ها
        perm_group = QGroupBox("دسترسی‌های سیستم")
        perm_layout = QVBoxLayout()
        
        self.permission_list = QListWidget()
        permissions = [
            "reservation_view", "reservation_edit", "reservation_delete",
            "guest_management", "room_management", "report_view",
            "settings_management", "user_management"
        ]
        
        for perm in permissions:
            item = QListWidgetItem(perm)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.permission_list.addItem(item)
        
        perm_layout.addWidget(self.permission_list)
        perm_group.setLayout(perm_layout)
        layout.addWidget(perm_group)
        
        # دکمه‌ها
        button_layout = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_layout.accepted.connect(self.save_user)
        button_layout.rejected.connect(self.reject)
        
        layout.addWidget(button_layout)
        self.setLayout(layout)
    
    def load_user_data(self):
        """بارگذاری اطلاعات کاربر موجود"""
        user_data = self.user_manager.users.get(self.username, {})
        
        self.username_edit.setText(self.username)
        self.fullname_edit.setText(user_data.get('full_name', ''))
        self.email_edit.setText(user_data.get('email', ''))
        self.phone_edit.setText(user_data.get('phone', ''))
        self.role_combo.setCurrentText(user_data.get('role', 'reception'))
        self.status_check.setChecked(user_data.get('is_active', True))
        
        # تنظیم دسترسی‌ها
        permissions = user_data.get('permissions', [])
        for i in range(self.permission_list.count()):
            item = self.permission_list.item(i)
            if item.text() in permissions:
                item.setCheckState(Qt.CheckState.Checked)
    
    def generate_password(self):
        """تولید رمز عبور تصادفی"""
        password = self.user_manager.generate_password()
        self.password_edit.setText(password)
        QMessageBox.information(self, "رمز تولید شده", 
                               f"رمز عبور جدید: {password}\n\nلطفاً آن را ذخیره کنید.")
    
    def toggle_password_visibility(self):
        """تغییر حالت نمایش رمز عبور"""
        if self.password_edit.echoMode() == QLineEdit.EchoMode.Password:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
    
    def save_user(self):
        """ذخیره کاربر"""
        username = self.username_edit.text().strip()
        if not username:
            QMessageBox.warning(self, "خطا", "نام کاربری الزامی است")
            return
        
        # جمع‌آوری دسترسی‌ها
        permissions = []
        for i in range(self.permission_list.count()):
            item = self.permission_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                permissions.append(item.text())
        
        user_data = {
            'full_name': self.fullname_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'phone': self.phone_edit.text().strip(),
            'role': self.role_combo.currentText(),
            'is_active': self.status_check.isChecked(),
            'permissions': permissions,
            'updated_at': datetime.now().isoformat()
        }
        
        # مدیریت رمز عبور
        password = self.password_edit.text().strip()
        if password:
            user_data['password'] = self.user_manager.hash_password(password)
        
        if self.is_edit:
            success, message = self.user_manager.update_user(username, user_data)
        else:
            if not password:
                QMessageBox.warning(self, "خطا", "رمز عبور الزامی است")
                return
            success, message = self.user_manager.add_user(username, user_data)
        
        if success:
            QMessageBox.information(self, "موفق", message)
            self.accept()
        else:
            QMessageBox.warning(self, "خطا", message)

class EnhancedSettingsTab(QWidget):
    def __init__(self, reservation_manager):
        super().__init__()
        self.reservation_manager = reservation_manager
        self.user_manager = UserManager()
        self.color_manager = ColorManager()
        self.rate_manager = RateManager()
        
        self.setup_ui()
        self.load_logs_data()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_logs_data)
        self.timer.start(30000)
    
    def setup_ui(self):
        # ایجاد تب‌های اصلی
        main_layout = QVBoxLayout()
        
        tabs = QTabWidget()
        
        # تب لاگ سیستم
        logs_tab = self.create_logs_tab()
        tabs.addTab(logs_tab, "📋 لاگ سیستم")
        
        # تب مدیریت کاربران
        users_tab = self.create_users_tab()
        tabs.addTab(users_tab, "👥 مدیریت کاربران")
        
        # تب مدیریت رنگ‌ها
        colors_tab = self.create_colors_tab()
        tabs.addTab(colors_tab, "🎨 مدیریت رنگ‌ها")
        
        # تب مدیریت نرخ‌ها
        rates_tab = self.create_rates_tab()
        tabs.addTab(rates_tab, "💵 مدیریت نرخ‌ها")
        
        # تب تنظیمات سیستم
        system_tab = self.create_system_tab()
        tabs.addTab(system_tab, "⚙️ تنظیمات سیستم")
        
        main_layout.addWidget(tabs)
        self.setLayout(main_layout)
    
    def create_users_tab(self):
        """ایجاد تب مدیریت کاربران"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # نوار ابزار
        toolbar = QHBoxLayout()
        
        add_user_btn = QPushButton("➕ کاربر جدید")
        add_user_btn.clicked.connect(self.add_new_user)
        
        refresh_btn = QPushButton("🔄 بروزرسانی")
        refresh_btn.clicked.connect(self.load_users_data)
        
        toolbar.addWidget(add_user_btn)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # جدول کاربران
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(7)
        self.users_table.setHorizontalHeaderLabels([
            "نام کاربری", "نام کامل", "نقش", "ایمیل", "تلفن", "وضعیت", "عملیات"
        ])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.users_table)
        
        self.load_users_data()
        widget.setLayout(layout)
        return widget
    
    def create_colors_tab(self):
        """ایجاد تب مدیریت رنگ‌ها"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # انتخاب پالت
        scheme_layout = QHBoxLayout()
        scheme_layout.addWidget(QLabel("پالت رنگی:"))
        
        self.scheme_combo = QComboBox()
        self.scheme_combo.addItems(list(self.color_manager.schemes.keys()))
        self.scheme_combo.currentTextChanged.connect(self.load_colors_data)
        scheme_layout.addWidget(self.scheme_combo)
        
        new_scheme_btn = QPushButton("➕ پالت جدید")
        new_scheme_btn.clicked.connect(self.create_new_scheme)
        
        scheme_layout.addWidget(new_scheme_btn)
        scheme_layout.addStretch()
        
        layout.addLayout(scheme_layout)
        
        # جدول رنگ‌ها
        self.colors_table = QTableWidget()
        self.colors_table.setColumnCount(3)
        self.colors_table.setHorizontalHeaderLabels(["عنوان", "رنگ فعلی", "عملیات"])
        self.colors_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.colors_table)
        
        # پیش‌نمایش
        preview_layout = QHBoxLayout()
        preview_layout.addWidget(QLabel("پیش‌نمایش:"))
        
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(100, 30)
        self.color_preview.setStyleSheet("background-color: #3498db; border: 1px solid #ccc;")
        
        preview_layout.addWidget(self.color_preview)
        preview_layout.addStretch()
        
        layout.addLayout(preview_layout)
        
        self.load_colors_data()
        widget.setLayout(layout)
        return widget
    
    def create_rates_tab(self):
        """ایجاد تب مدیریت نرخ‌ها"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # تب‌های داخلی
        rate_tabs = QTabWidget()
        
        # نرخ اتاق‌ها
        room_rates_tab = self.create_room_rates_tab()
        rate_tabs.addTab(room_rates_tab, "🏨 نرخ اتاق‌ها")
        
        # پکیج‌ها
        packages_tab = self.create_packages_tab()
        rate_tabs.addTab(packages_tab, "📦 پکیج‌ها")
        
        # فصول
        seasons_tab = self.create_seasons_tab()
        rate_tabs.addTab(seasons_tab, "📅 فصول")
        
        layout.addWidget(rate_tabs)
        widget.setLayout(layout)
        return widget
    
    def create_room_rates_tab(self):
        """ایجاد تب نرخ اتاق‌ها"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.room_rates_table = QTableWidget()
        self.room_rates_table.setColumnCount(5)
        self.room_rates_table.setHorizontalHeaderLabels([
            "نوع اتاق", "نرخ پایه", "نرخ آخر هفته", "ظرفیت", "عملیات"
        ])
        
        layout.addWidget(self.room_rates_table)
        
        # دکمه ذخیره
        save_btn = QPushButton("💾 ذخیره تغییرات نرخ‌ها")
        save_btn.clicked.connect(self.save_room_rates)
        layout.addWidget(save_btn)
        
        self.load_room_rates()
        widget.setLayout(layout)
        return widget
    
    def create_packages_tab(self):
        """ایجاد تب پکیج‌ها"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.packages_table = QTableWidget()
        self.packages_table.setColumnCount(3)
        self.packages_table.setHorizontalHeaderLabels([
            "نام پکیج", "ضریب قیمت", "عملیات"
        ])
        
        layout.addWidget(self.packages_table)
        
        save_btn = QPushButton("💾 ذخیره تغییرات پکیج‌ها")
        save_btn.clicked.connect(self.save_packages)
        layout.addWidget(save_btn)
        
        self.load_packages()
        widget.setLayout(layout)
        return widget
    
    def create_seasons_tab(self):
        """ایجاد تب فصول"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.seasons_table = QTableWidget()
        self.seasons_table.setColumnCount(3)
        self.seasons_table.setHorizontalHeaderLabels([
            "فصل", "ضریب قیمت", "عملیات"
        ])
        
        layout.addWidget(self.seasons_table)
        
        save_btn = QPushButton("💾 ذخیره تغییرات فصول")
        save_btn.clicked.connect(self.save_seasons)
        layout.addWidget(save_btn)
        
        self.load_seasons()
        widget.setLayout(layout)
        return widget
    
    def create_system_tab(self):
        """ایجاد تب تنظیمات سیستم"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # تنظیمات عمومی
        general_group = QGroupBox("تنظیمات عمومی")
        form_layout = QFormLayout()
        
        self.check_in_time = QLineEdit("14:00")
        self.check_out_time = QLineEdit("12:00")
        self.back_to_back_enabled = QCheckBox("فعال کردن Back-to-Back")
        self.back_to_back_enabled.setChecked(True)
        
        form_layout.addRow("زمان چک-این:", self.check_in_time)
        form_layout.add