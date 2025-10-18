import threading
import time
from datetime import datetime
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'models'))
from models import Reservation, Room

class RealtimeManager:
    def __init__(self, reservation_manager):
        self.reservation_manager = reservation_manager
        self.last_update = datetime.now()
        self.callbacks = []
        self.running = True
        self.thread = threading.Thread(target=self._monitor_changes)
        self.thread.daemon = True
        self.thread.start()
    
    def _monitor_changes(self):
        """مانیتور تغییرات در پایگاه داده"""
        while self.running:
            try:
                session = self.reservation_manager.Session()
                latest_reservation = session.query(Reservation).order_by(
                    Reservation.created_at.desc()
                ).first()
                
                if latest_reservation and latest_reservation.created_at > self.last_update:
                    self.last_update = latest_reservation.created_at
                    self.notify_callbacks()
                
                session.close()
                time.sleep(2)  # بررسی هر 2 ثانیه
            except Exception as e:
                print(f"خطا در مانیتورینگ: {e}")
                time.sleep(5)
    
    def add_callback(self, callback):
        """اضافه کردن تابع callback برای بروزرسانی"""
        self.callbacks.append(callback)
    
    def notify_callbacks(self):
        """اطلاع دادن به تمام callbackها"""
        for callback in self.callbacks:
            try:
                callback()
            except Exception as e:
                print(f"خطا در اجرای callback: {e}")
    
    def stop(self):
        """توقف مانیتورینگ"""
        self.running = False