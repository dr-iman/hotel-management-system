import jdatetime
from datetime import datetime

class JalaliDate:
    @staticmethod
    def to_jalali(dt):
        """تبدیل تاریخ میلادی به شمسی"""
        if isinstance(dt, datetime):
            return jdatetime.datetime.fromgregorian(datetime=dt)
        elif isinstance(dt, jdatetime.datetime):
            return dt
        return dt
    
    @staticmethod
    def to_gregorian(jalali_dt):
        """تبدیل تاریخ شمسی به میلادی"""
        if isinstance(jalali_dt, jdatetime.datetime):
            return jalali_dt.togregorian()
        return jalali_dt
    
    @staticmethod
    def now():
        """تاریخ و زمان شمسی فعلی"""
        return jdatetime.datetime.now()
    
    @staticmethod
    def format_date(dt, format_str="%Y/%m/%d"):
        """فرمت‌دهی تاریخ شمسی"""
        jalali_dt = JalaliDate.to_jalali(dt)
        return jalali_dt.strftime(format_str)
    
    @staticmethod
    def today():
        """امروز به شمسی"""
        return jdatetime.date.today()
    
    @staticmethod
    def from_jalali_string(date_string, format_str="%Y/%m/%d"):
        """ایجاد تاریخ شمسی از رشته"""
        return jdatetime.datetime.strptime(date_string, format_str)
    
    @staticmethod
    def add_days(jalali_date, days):
        """اضافه کردن روز به تاریخ شمسی"""
        return jalali_date + jdatetime.timedelta(days=days)