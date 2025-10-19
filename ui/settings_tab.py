from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QTableWidget, QTableWidgetItem, QHeaderView,
                            QComboBox, QLineEdit, QPushButton, QDateEdit,
                            QFormLayout, QGroupBox, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
import sys
import os
import jdatetime
import json
from datetime import datetime, timedelta

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
        
        # تایمر برای بروزرسانی خودکار لاگ‌ها
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_logs_data)
        self.timer.start(30000)  # هر 30 ثانیه
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # عنوان
        title_label = QLabel("⚙️ تنظیمات سیستم - لاگ تغییرات")
        title_label.setFont(QFont("Tahoma", 16, QFont.Weight.Bold))
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
        logs_label.setFont(QFont("Tahoma", 14, QFont.Weight.Bold))
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
        self.setLayout(layout)
    
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