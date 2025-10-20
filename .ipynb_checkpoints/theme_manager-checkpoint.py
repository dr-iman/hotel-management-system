# theme_manager.py
import os
from PyQt6.QtCore import QSettings

class ThemeManager:
    def __init__(self):
        self.settings = QSettings("HotelArad", "Theme")
        self.current_theme = self.settings.value("theme", "light")
        
    def get_theme_path(self, theme_name):
        """دریافت مسیر فایل استایل بر اساس تم"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if theme_name == "dark":
            return os.path.join(current_dir, "ui", "styles", "style_dark.qss")
        else:
            return os.path.join(current_dir, "ui", "styles", "style.qss")
    
    def load_theme(self, app, theme_name=None):
        """بارگذاری تم"""
        if theme_name:
            self.current_theme = theme_name
            self.settings.setValue("theme", theme_name)
        
        theme_path = self.get_theme_path(self.current_theme)
        
        if os.path.exists(theme_path):
            try:
                with open(theme_path, 'r', encoding='utf-8') as f:
                    app.setStyleSheet(f.read())
                print(f"🎨 تم {self.current_theme} بارگذاری شد")
                return True
            except Exception as e:
                print(f"⚠️ خطا در بارگذاری تم: {e}")
                return False
        else:
            print(f"⚠️ فایل تم یافت نشد: {theme_path}")
            return False
    
    def toggle_theme(self, app):
        """تغییر تم"""
        if self.current_theme == "light":
            return self.load_theme(app, "dark")
        else:
            return self.load_theme(app, "light")