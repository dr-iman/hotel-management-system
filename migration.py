# migration.py
import os
import sys
from sqlalchemy import create_engine, text

current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, 'database', 'hotel.db')
db_url = f"sqlite:///{db_path}"

engine = create_engine(db_url)

# اضافه کردن فیلدهای جدید
with engine.connect() as conn:
    try:
        # اضافه کردن فیلد is_half_charge
        conn.execute(text("ALTER TABLE reservations ADD COLUMN is_half_charge BOOLEAN DEFAULT FALSE"))
        print("✅ فیلد is_half_charge اضافه شد")
        
        # اضافه کردن فیلدهای زمان (اختیاری)
        conn.execute(text("ALTER TABLE reservations ADD COLUMN check_in_time VARCHAR(10) DEFAULT '14:00'"))
        conn.execute(text("ALTER TABLE reservations ADD COLUMN check_out_time VARCHAR(10) DEFAULT '12:00'"))
        print("✅ فیلدهای زمان اضافه شدند")
        
        conn.commit()
        print("✅ مایگریشن با موفقیت انجام شد")
        
    except Exception as e:
        print(f"⚠️ خطا در مایگریشن: {e}")
        print("⚠️ احتمالاً فیلدها از قبل وجود دارند")