from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QSpacerItem, QSizePolicy
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QFontDatabase
import os

class PreloaderWindow(QWidget):
    finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_animation()
        
    def setup_ui(self):
        # تنظیمات پنجره
        self.setWindowTitle("هتل آراد")
        self.setFixedSize(600, 500)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
            }
        """)
        
        # ایجاد Layout اصلی
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 60, 40, 40)  # حاشیه بالا بیشتر شده
        
        # لوگو هتل - در بالاترین قسمت
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setFixedSize(200, 200)
        
        # بارگذاری تصویر لوگو
        logo_loaded = self.load_logo_image()
        
        if not logo_loaded:
            # اگر تصویر لوگو پیدا نشد، از دایره طلایی با آیکون استفاده کن
            self.logo_label.setStyleSheet("""
                QLabel {
                    background-color: #D4AF37;
                    border-radius: 100px;
                    color: white;
                    font-size: 80px;
                    font-weight: bold;
                }
            """)
            self.logo_label.setText("🏨")
        
        # نام هتل با فونت زیبا
        self.hotel_name = QLabel("هتل آراد")
        self.hotel_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # تلاش برای استفاده از فونت B Titr
        font_loaded = False
        font_paths = [
            "C:/Windows/Fonts/B Titr.ttf",
            "C:/Windows/Fonts/b_titr.ttf",
            "/usr/share/fonts/truetype/BTitr.ttf",
            "./assets/fonts/B Titr.ttf",
            "./assets/fonts/BTitr.ttf"
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id != -1:
                    font_families = QFontDatabase.applicationFontFamilies(font_id)
                    if font_families:
                        titr_font = QFont(font_families[0], 36, QFont.Weight.Bold)
                        self.hotel_name.setFont(titr_font)
                        font_loaded = True
                        print(f"✅ فونت بارگذاری شد: {font_path}")
                        break
        
        if not font_loaded:
            # استفاده از فونت پیش‌فرض اگر B Titr پیدا نشد
            titr_font = QFont("Tahoma", 36, QFont.Weight.Bold)
            self.hotel_name.setFont(titr_font)
            print("⚠️ فونت B Titr یافت نشد. از فونت Tahoma استفاده می‌شود.")
        
        self.hotel_name.setStyleSheet("""
            QLabel {
                color: #D4AF37;
                background-color: transparent;
                padding: 10px;
            }
        """)
        
        # زیرعنوان
        self.subtitle = QLabel("سیستم مدیریت رزرواسیون")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle.setFont(QFont("Tahoma", 16, QFont.Weight.Normal))
        self.subtitle.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                background-color: transparent;
            }
        """)
        
        # اسپیسر برای فاصله بین متن و نوار پیشرفت
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        
        # نوار پیشرفت طلایی
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(400)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #f1c40f;
                border-radius: 6px;
                background-color: #fef9e7;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #D4AF37, stop:0.5 #f1c40f, stop:1 #D4AF37);
                border-radius: 5px;
            }
        """)
        
        # متن در حال بارگذاری
        self.loading_text = QLabel("در حال بارگذاری...")
        self.loading_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_text.setFont(QFont("Tahoma", 12))
        self.loading_text.setStyleSheet("""
            QLabel {
                color: #D4AF37;
                background-color: transparent;
                font-weight: bold;
            }
        """)
        
        # اضافه کردن ویجت‌ها به layout با ترتیب جدید
        layout.addWidget(self.logo_label, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.hotel_name, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.subtitle, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addItem(spacer)  # اسپیسر برای فاصله
        layout.addWidget(self.progress_bar, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.loading_text, 0, Qt.AlignmentFlag.AlignHCenter)
        
        self.setLayout(layout)
        
    def load_logo_image(self):
        """بارگذاری تصویر لوگو هتل"""
        try:
            # مسیرهای ممکن برای فایل لوگو
            possible_paths = [
                os.path.join(os.path.dirname(__file__), 'assets', 'logo.png'),
                os.path.join(os.path.dirname(__file__), 'assets', 'logo.jpg'),
                os.path.join(os.path.dirname(__file__), 'assets', 'logo.jpeg'),
                os.path.join(os.path.dirname(__file__), 'images', 'logo.png'),
                os.path.join(os.path.dirname(__file__), 'images', 'logo.jpg'),
                os.path.join(os.path.dirname(__file__), 'images', 'logo.jpeg'),
                os.path.join(os.path.dirname(__file__), 'logo.png'),
                os.path.join(os.path.dirname(__file__), 'logo.jpg'),
                os.path.join(os.path.dirname(__file__), 'logo.jpeg'),
            ]
            
            logo_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    logo_path = path
                    break
            
            if logo_path:
                pixmap = QPixmap(logo_path)
                # تغییر اندازه تصویر به اندازه مناسب با حفظ نسبت
                pixmap = pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio, 
                                     Qt.TransformationMode.SmoothTransformation)
                
                # ایجاد یک QPixmap جدید برای نمایش لوگو
                logo_pixmap = QPixmap(200, 200)
                logo_pixmap.fill(Qt.GlobalColor.transparent)
                
                painter = QPainter(logo_pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                
                # رسم تصویر در مرکز بدون border
                x = (200 - pixmap.width()) // 2
                y = (200 - pixmap.height()) // 2
                painter.drawPixmap(x, y, pixmap)
                painter.end()
                
                self.logo_label.setPixmap(logo_pixmap)
                print(f"✅ لوگو بارگذاری شد: {logo_path}")
                return True
            else:
                print("⚠️ فایل لوگو یافت نشد. از آیکون پیش‌فرض استفاده می‌شود.")
                return False
                
        except Exception as e:
            print(f"❌ خطا در بارگذاری لوگو: {e}")
            return False
    
    def setup_animation(self):
        # تایمر برای انیمیشن پیشرفت
        self.progress_value = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(60)  # به روزرسانی هر 60 میلی‌ثانیه
        
    def update_progress(self):
        self.progress_value += 1
        self.progress_bar.setValue(self.progress_value)
        
        # به روزرسانی متن بر اساس پیشرفت
        if self.progress_value < 25:
            self.loading_text.setText("در حال راه‌اندازی سیستم...")
        elif self.progress_value < 50:
            self.loading_text.setText("در حال بارگذاری ماژول‌ها...")
        elif self.progress_value < 75:
            self.loading_text.setText("در حال آماده‌سازی رابط کاربری...")
        elif self.progress_value < 90:
            self.loading_text.setText("در حال بارگذاری داده‌ها...")
        else:
            self.loading_text.setText("آماده برای ورود به سیستم!")
        
        if self.progress_value >= 100:
            self.timer.stop()
            # تاخیر کوتاه قبل از بسته شدن
            QTimer.singleShot(800, self.close_preloader)
    
    def close_preloader(self):
        self.finished.emit()
        self.close()
    
    def paintEvent(self, event):
        """رسم border طلایی دور پنجره"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # رسم border طلایی
        painter.setPen(QColor("#D4AF37"))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)
        
        # رسم سایه ملایم
        painter.setPen(QColor(212, 175, 55, 50))
        for i in range(1, 5):
            painter.drawRect(i, i, self.width() - 1 - i*2, self.height() - 1 - i*2)