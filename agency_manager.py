from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys

class AgencyManager:
    def __init__(self):
        # استفاده از مسیر صحیح دیتابیس
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        db_path = os.path.join(project_root, 'database', 'hotel.db')
        db_url = f"sqlite:///{db_path}"
        
        print(f"🔧 مسیر دیتابیس در AgencyManager: {db_path}")
        
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
    
    def get_all_agencies(self):
        """دریافت تمام آژانس‌های فعال"""
        session = self.Session()
        try:
            agencies = session.query(Agency).filter(Agency.is_active == True).order_by(Agency.name).all()
            print(f"✅ تعداد آژانس‌های دریافت شده: {len(agencies)}")
            return agencies
        except Exception as e:
            print(f"❌ خطا در دریافت آژانس‌ها: {e}")
            return []
        finally:
            session.close()