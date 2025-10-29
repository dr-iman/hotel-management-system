# rack_widget_fixed.py
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
import jdatetime
from datetime import datetime, timedelta

class FixedRoomCellWidget(QFrame):
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
    
    def paintEvent(self, event):
        """رسم سلول با پشتیبانی صحیح از Back-to-Back"""
        painter = QPainter(self)
        try:
            width = self.width()
            height = self.height()
            
            if self.reservation_data:
                self.paint_back_to_back_cell(painter, width, height)
            else:
                self.paint_empty_cell(painter, width, height)
                
        finally:
            painter.end()
    
    def paint_back_to_back_cell(self, painter, width, height):
        """رسم سلول با منطق صحیح Back-to-Back"""
        cell_type = self.reservation_data.get('cell_type', 'full')
        color = self.get_reservation_color()
        
        # منطق اصلاح شده برای تقسیم سلول
        if cell_type == 'start':
            # شروع رزرو - نیمه چپ خالی، نیمه راست پر
            painter.fillRect(width // 2, 0, width // 2, height, QColor(color))
            # خط جداکننده
            painter.setPen(QColor("#34495e"))
            painter.drawLine(width // 2, 0, width // 2, height)
            # فلش شروع
            painter.setPen(QColor("white"))
            painter.drawText(width // 2 + 5, height // 2 + 5, "→")
            
        elif cell_type == 'end':
            # پایان رزرو - نیمه چپ پر، نیمه راست خالی
            painter.fillRect(0, 0, width // 2, height, QColor(color))
            # خط جداکننده
            painter.setPen(QColor("#34495e"))
            painter.drawLine(width // 2, 0, width // 2, height)
            # فلش پایان
            painter.setPen(QColor("white"))
            painter.drawText(width // 2 - 15, height // 2 + 5, "←")
            
        elif cell_type == 'middle':
            # روزهای میانی - کل سلول پر
            painter.fillRect(0, 0, width, height, QColor(color))
            self.draw_reservation_info(painter, 0, 0, width, height)
            
        else:  # full
            # رزرو کامل - کل سلول پر
            painter.fillRect(0, 0, width, height, QColor(color))
            self.draw_reservation_info(painter, 0, 0, width, height)
        
        # Border
        painter.setPen(QColor("#2c3e50"))
        painter.drawRect(0, 0, width - 1, height - 1)