from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os
import sys
import json

current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(current_dir)

from models.models import Base, Room, Guest, Reservation, SystemLog, Agency

class ReservationManager:
    def __init__(self):
        db_path = os.path.join(current_dir, 'database', 'hotel.db')
        db_url = f"sqlite:///{db_path}"
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.create_tables()
        self.init_sample_agencies()
    
    def init_sample_agencies(self):
        """ایجاد آژانس‌های نمونه در صورت عدم وجود"""
        session = self.Session()
        try:
            existing_agencies = session.query(Agency).count()
            if existing_agencies == 0:
                sample_agencies = [
                    {"name": "آژانس مسافرتی ایران", "contact_person": "علیرضا محمدی"},
                    {"name": "آژانس آسمان آبی", "contact_person": "فاطمه کریمی"},
                    {"name": "آژانس سفرهای خارجی", "contact_person": "محمد حسینی"},
                    {"name": "آژانس گردشگری پارس", "contact_person": "زهرا احمدی"}
                ]
                
                for agency_data in sample_agencies:
                    agency = Agency(**agency_data)
                    session.add(agency)
                
                session.commit()
                print("✅ آژانس‌های نمونه ایجاد شدند")
        except Exception as e:
            print(f"⚠️ خطا در ایجاد آژانس‌های نمونه: {e}")
        finally:
            session.close()

    def get_all_agencies(self):
        """دریافت تمام آژانس‌ها"""
        session = self.Session()
        try:
            agencies = session.query(Agency).filter(Agency.is_active == True).order_by(Agency.name).all()
            return agencies
        except Exception as e:
            print(f"خطا در دریافت آژانس‌ها: {e}")
            return []
        finally:
            session.close()

    def create_reservation(self, reservation_data, guest_data, changed_by="سیستم"):
        """ایجاد رزرو جدید"""
        session = self.Session()
        try:
            print(f"🔍 شروع ایجاد رزرو برای مهمان: {guest_data['first_name']} {guest_data['last_name']}")
            
            # ایجاد مهمان جدید
            guest = Guest(
                first_name=guest_data['first_name'],
                last_name=guest_data['last_name'],
                id_number=guest_data.get('id_number'),
                nationality=guest_data.get('nationality', 'ایرانی')
            )
            session.add(guest)
            session.commit()
            print(f"✅ مهمان ایجاد شد با ID: {guest.id}")
            
            # ایجاد رزرو
            reservation = Reservation(
                room_id=reservation_data['room_id'],
                guest_id=guest.id,
                check_in=reservation_data['check_in'],
                check_out=reservation_data['check_out'],
                status=reservation_data.get('status', 'confirmed'),
                adults=reservation_data.get('adults', 1),
                children=reservation_data.get('children', 0),
                total_amount=reservation_data.get('total_amount', 0),
                paid_amount=reservation_data.get('paid_amount', 0),
                package_type=reservation_data.get('package_type', 'فقط اسکان'),
                guest_type=reservation_data.get('guest_type', 'حضوری'),
                agency_id=reservation_data.get('agency_id'),
                settlement_type=reservation_data.get('settlement_type', 'تسویه با هتل'),
                tracking_code=reservation_data.get('tracking_code'),
                receipt_file=reservation_data.get('receipt_file'),
                receipt_filename=reservation_data.get('receipt_filename')
            )
            
            session.add(reservation)
            session.commit()
            print(f"✅ رزرو ایجاد شد با ID: {reservation.id}")
            
            # ثبت لاگ
            new_data = {
                'room_id': reservation.room_id,
                'guest_id': reservation.guest_id,
                'check_in': reservation.check_in.isoformat(),
                'check_out': reservation.check_out.isoformat(),
                'status': reservation.status,
                'adults': reservation.adults,
                'children': reservation.children,
                'total_amount': reservation.total_amount,
                'paid_amount': reservation.paid_amount,
                'package_type': reservation.package_type,
                'guest_type': reservation.guest_type,
                'agency_id': reservation.agency_id,
                'settlement_type': reservation.settlement_type,
                'tracking_code': reservation.tracking_code
            }
            
            self.log_system_action(
                action="create",
                table_name="reservations",
                record_id=reservation.id,
                old_data=None,
                new_data=new_data,
                changed_by=changed_by,
                description="ثبت رزرو جدید"
            )
            
            return True, "رزرو با موفقیت ثبت شد", reservation.id
            
        except Exception as e:
            print(f"❌ خطا در ثبت رزرو: {e}")
            session.rollback()
            import traceback
            traceback.print_exc()
            return False, f"خطا در ثبت رزرو: {str(e)}", None
        finally:
            session.close()
            
    def create_tables(self):
        """ایجاد تمام جداول در دیتابیس"""
        try:
            # این خط تمام جدول‌های تعریف شده در Base رو ایجاد می‌کنه
            Base.metadata.create_all(self.engine)
            print("✅ تمام جداول با موفقیت ایجاد شدند")
            
            # تست ایجاد جدول system_logs
            session = self.Session()
            log_count = session.query(SystemLog).count()
            print(f"📊 تعداد لاگ‌های موجود در دیتابیس: {log_count}")
            session.close()
            
        except Exception as e:
            print(f"❌ خطا در ایجاد جداول: {e}")
            import traceback
            traceback.print_exc()
    
    def log_system_action(self, action, table_name, record_id, old_data=None, new_data=None, changed_by="سیستم", description=""):
        """ثبت action در سیستم لاگ"""
        session = self.Session()
        try:
            # تبدیل داده‌ها به JSON برای ذخیره در دیتابیس
            old_data_json = json.dumps(old_data, ensure_ascii=False) if old_data else None
            new_data_json = json.dumps(new_data, ensure_ascii=False) if new_data else None
            
            log = SystemLog(
                action=action,
                table_name=table_name,
                record_id=record_id,
                old_data=old_data_json,
                new_data=new_data_json,
                changed_by=changed_by,
                description=description
            )
            session.add(log)
            session.commit()
            print(f"✅ لاگ ثبت شد: {action} روی {table_name}.{record_id} توسط {changed_by}")
            return True
        except Exception as e:
            print(f"❌ خطا در ثبت لاگ: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_all_logs(self):
        """دریافت تمام لاگ‌ها (برای تست)"""
        session = self.Session()
        try:
            logs = session.query(SystemLog).order_by(SystemLog.changed_at.desc()).all()
            print(f"📊 تعداد لاگ‌های موجود: {len(logs)}")
            
            # تبدیل JSON به دیکشنری
            for log in logs:
                if log.old_data:
                    try:
                        log.old_data = json.loads(log.old_data)
                    except:
                        pass
                if log.new_data:
                    try:
                        log.new_data = json.loads(log.new_data)
                    except:
                        pass
                        
            return logs
        except Exception as e:
            print(f"❌ خطا در دریافت لاگ‌ها: {e}")
            return []
        finally:
            session.close()
    
    def get_system_logs(self, action_filter=None, table_filter=None, user_filter=None, 
                       date_from=None, date_to=None, limit=1000):
        """دریافت لاگ‌های سیستم با فیلترهای مختلف"""
        session = self.Session()
        try:
            query = session.query(SystemLog)
            
            # اعمال فیلترها
            if action_filter and action_filter != "همه":
                query = query.filter(SystemLog.action == action_filter)
            
            if table_filter and table_filter != "همه":
                query = query.filter(SystemLog.table_name == table_filter)
            
            if user_filter:
                query = query.filter(SystemLog.changed_by.ilike(f"%{user_filter}%"))
            
            if date_from:
                query = query.filter(SystemLog.changed_at >= date_from)
            
            if date_to:
                # اضافه کردن یک روز به تاریخ تا برای شامل شدن آن روز
                date_to_end = date_to + timedelta(days=1)
                query = query.filter(SystemLog.changed_at < date_to_end)
            
            logs = query.order_by(SystemLog.changed_at.desc()).limit(limit).all()
            
            # تبدیل JSON به دیکشنری
            for log in logs:
                if log.old_data:
                    try:
                        log.old_data = json.loads(log.old_data)
                    except:
                        log.old_data = None
                if log.new_data:
                    try:
                        log.new_data = json.loads(log.new_data)
                    except:
                        log.new_data = None
            
            return logs
            
        except Exception as e:
            print(f"❌ خطا در دریافت لاگ‌ها با فیلتر: {e}")
            return []
        finally:
            session.close()
    
    def get_reservation_by_id(self, reservation_id):
        """دریافت رزرو بر اساس ID"""
        session = self.Session()
        try:
            reservation = session.query(Reservation).filter(Reservation.id == reservation_id).first()
            return reservation
        except Exception as e:
            print(f"خطا در دریافت رزرو: {e}")
            return None
        finally:
            session.close()
    
    def update_reservation(self, reservation_id, update_data, changed_by="سیستم"):
        """بروزرسانی رزرو و ثبت لاگ"""
        session = self.Session()
        try:
            reservation = session.query(Reservation).filter(Reservation.id == reservation_id).first()
            if not reservation:
                return False, "رزرو یافت نشد"
            
            # ذخیره داده‌های قبلی برای لاگ
            old_data = {
                'room_id': reservation.room_id,
                'guest_id': reservation.guest_id,
                'check_in': reservation.check_in.isoformat() if reservation.check_in else None,
                'check_out': reservation.check_out.isoformat() if reservation.check_out else None,
                'status': reservation.status,
                'adults': reservation.adults,
                'children': reservation.children,
                'total_amount': reservation.total_amount,
                'package_type': reservation.package_type,
                'guest_type': getattr(reservation, 'guest_type', 'حضوری')
            }
            
            # اعمال تغییرات
            for key, value in update_data.items():
                if hasattr(reservation, key):
                    setattr(reservation, key, value)
            
            session.commit()
            
            # ذخیره داده‌های جدید برای لاگ
            new_data = {
                'room_id': reservation.room_id,
                'guest_id': reservation.guest_id,
                'check_in': reservation.check_in.isoformat() if reservation.check_in else None,
                'check_out': reservation.check_out.isoformat() if reservation.check_out else None,
                'status': reservation.status,
                'adults': reservation.adults,
                'children': reservation.children,
                'total_amount': reservation.total_amount,
                'package_type': reservation.package_type,
                'guest_type': getattr(reservation, 'guest_type', 'حضوری')
            }
            
            # ثبت لاگ
            log_success = self.log_system_action(
                action="update",
                table_name="reservations",
                record_id=reservation_id,
                old_data=old_data,
                new_data=new_data,
                changed_by=changed_by,
                description="ویرایش رزرو"
            )
            
            if not log_success:
                print("⚠️ رزرو بروزرسانی شد اما ثبت لاگ با مشکل مواجه شد")
            
            return True, "رزرو با موفقیت بروزرسانی شد"
            
        except Exception as e:
            session.rollback()
            print(f"خطا در بروزرسانی رزرو: {e}")
            return False, f"خطا در بروزرسانی: {str(e)}"
        finally:
            session.close()

    def create_reservation(self, reservation_data, guest_data, changed_by="سیستم"):
        """ایجاد رزرو جدید و ثبت لاگ - نسخه نهایی"""
        session = self.Session()
        try:
            print(f"🔍 شروع ایجاد رزرو برای مهمان: {guest_data['first_name']} {guest_data['last_name']}")
            print(f"📅 تاریخ ورود: {reservation_data['check_in']}")
            print(f"📅 تاریخ خروج: {reservation_data['check_out']}")
            print(f"🏨 اتاق: {reservation_data['room_id']}")
            
            # ایجاد مهمان جدید
            guest = Guest(
                first_name=guest_data['first_name'],
                last_name=guest_data['last_name'],
                nationality=guest_data.get('nationality', 'ایرانی')
            )
            session.add(guest)
            session.commit()  # کامیت فوری برای گرفتن ID
            print(f"✅ مهمان ایجاد شد با ID: {guest.id}")
            
            # ایجاد رزرو
            reservation = Reservation(
                room_id=reservation_data['room_id'],
                guest_id=guest.id,
                check_in=reservation_data['check_in'],
                check_out=reservation_data['check_out'],
                status=reservation_data.get('status', 'confirmed'),
                adults=reservation_data.get('adults', 1),
                children=reservation_data.get('children', 0),
                total_amount=reservation_data.get('total_amount', 0),
                paid_amount=reservation_data.get('paid_amount', 0),
                package_type=reservation_data.get('package_type', 'فقط اسکان'),
                guest_type=reservation_data.get('guest_type', 'حضوری')
            )
            
            session.add(reservation)
            session.commit()  # کامیت نهایی
            print(f"✅ رزرو ایجاد شد با ID: {reservation.id}")
            
            # ثبت لاگ
            new_data = {
                'room_id': reservation.room_id,
                'guest_id': reservation.guest_id,
                'check_in': reservation.check_in.isoformat(),
                'check_out': reservation.check_out.isoformat(),
                'status': reservation.status,
                'adults': reservation.adults,
                'children': reservation.children,
                'total_amount': reservation.total_amount,
                'package_type': reservation.package_type,
                'guest_type': reservation.guest_type
            }
            
            log_success = self.log_system_action(
                action="create",
                table_name="reservations",
                record_id=reservation.id,
                old_data=None,
                new_data=new_data,
                changed_by=changed_by,
                description="ثبت رزرو جدید"
            )
            
            if log_success:
                print(f"✅ لاگ رزرو {reservation.id} ثبت شد")
            else:
                print(f"⚠️ رزرو ذخیره شد اما ثبت لاگ با مشکل مواجه شد")
            
            return True, "رزرو با موفقیت ثبت شد", reservation.id
            
        except Exception as e:
            print(f"❌ خطا در ثبت رزرو: {e}")
            session.rollback()
            import traceback
            traceback.print_exc()
            return False, f"خطا در ثبت رزرو: {str(e)}", None
        finally:
            session.close()
            print("🔒 session بسته شد")
        
    def get_suggested_rooms(self, check_in, check_out, capacity):
        """دریافت اتاق‌های پیشنهادی با ظرفیت مناسب"""
        session = self.Session()
        try:
            suitable_rooms = session.query(Room).filter(
                Room.is_active == True,
                Room.capacity >= capacity
            ).all()
            
            available_rooms = []
            for room in suitable_rooms:
                if self.is_room_available(room.id, check_in, check_out):
                    available_rooms.append(room)
            
            return available_rooms
            
        except Exception as e:
            print(f"خطا در دریافت اتاق‌های پیشنهادی: {e}")
            return []
        finally:
            session.close()
    
    def get_room_conflicts(self, room_id, check_in, check_out):
        """دریافت رزروهای متضاد برای یک اتاق"""
        session = self.Session()
        try:
            conflicts = session.query(Reservation, Guest).join(
                Guest, and_(Reservation.guest_id == Guest.id)
            ).filter(
                Reservation.room_id == room_id,
                Reservation.status.in_(['confirmed', 'checked_in']),
                or_(
                    and_(Reservation.check_in < check_out, Reservation.check_out > check_in)
                )
            ).all()
            
            conflict_info = []
            for reservation, guest in conflicts:
                conflict_info.append({
                    'guest_name': f"{guest.first_name} {guest.last_name}",
                    'check_in': reservation.check_in,
                    'check_out': reservation.check_out,
                    'status': reservation.status
                })
            
            return conflict_info
            
        except Exception as e:
            print(f"خطا در دریافت تضادها: {e}")
            return []
        finally:
            session.close()
    
    def get_reservation_for_date(self, room_id, date):
        """دریافت رزرو برای یک اتاق در تاریخ مشخص"""
        session = self.Session()
        try:
            from sqlalchemy import and_
            
            reservation = session.query(Reservation, Guest).join(
                Guest, 
                and_(Reservation.guest_id == Guest.id)
            ).filter(
                Reservation.room_id == room_id,
                Reservation.check_in <= date,
                Reservation.check_out > date,
                Reservation.status.in_(['confirmed', 'checked_in'])
            ).first()
            
            return reservation
        except Exception as e:
            print(f"خطا در دریافت رزرو: {e}")
            return None
        finally:
            session.close()
    
    def search_reservations(self, search_text):
        """جستجو بر اساس نام مهمان یا شماره اتاق"""
        session = self.Session()
        
        try:
            from sqlalchemy import and_
            
            # جستجو در مهمانان
            guest_results = session.query(Reservation, Guest).join(
                Guest, and_(Reservation.guest_id == Guest.id)
            ).filter(
                or_(
                    Guest.first_name.ilike(f"%{search_text}%"),
                    Guest.last_name.ilike(f"%{search_text}%")
                )
            ).all()
            
            # جستجو در اتاق‌ها
            room_results = session.query(Reservation, Room).join(
                Room, and_(Reservation.room_id == Room.id)
            ).filter(
                Room.room_number.ilike(f"%{search_text}%")
            ).all()
            
            # ترکیب نتایج
            all_results = list(set([r[0] for r in guest_results] + [r[0] for r in room_results]))
            return all_results
            
        except Exception as e:
            print(f"خطا در جستجو: {e}")
            return []
        finally:
            session.close()

    def get_room_availability_with_back_to_back(self, room_id, check_in, check_out):
        """بررسی موجود بودن اتاق با پشتیبانی کامل از Back-to-Back"""
        session = self.Session()
        
        try:
            # تبدیل به datetime اگر string است
            if isinstance(check_in, str):
                check_in = datetime.fromisoformat(check_in)
            if isinstance(check_out, str):
                check_out = datetime.fromisoformat(check_out)
            
            print(f"🔍 بررسی اتاق {room_id}")
            print(f"   ورود اصلی: {check_in} (نوع: {type(check_in)})")
            print(f"   خروج اصلی: {check_out} (نوع: {type(check_out)})")
            
            # تنظیم زمان‌های استاندارد هتل - روش صحیح و ساده
            if hasattr(check_in, 'hour'):  # اگر datetime است
                check_in_time = datetime(check_in.year, check_in.month, check_in.day, 14, 0, 0)
            else:  # اگر date است
                check_in_time = datetime(check_in.year, check_in.month, check_in.day, 14, 0, 0)
                
            if hasattr(check_out, 'hour'):  # اگر datetime است
                check_out_time = datetime(check_out.year, check_out.month, check_out.day, 12, 0, 0)
            else:  # اگر date است
                check_out_time = datetime(check_out.year, check_out.month, check_out.day, 12, 0, 0)
            
            print(f"   ورود تنظیم شده: {check_in_time}")
            print(f"   خروج تنظیم شده: {check_out_time}")
            
            # پیدا کردن رزروهای متضاد
            from sqlalchemy import and_, or_
            
            conflicting_reservations = session.query(Reservation).filter(
                Reservation.room_id == room_id,
                Reservation.status.in_(['confirmed', 'checked_in']),
                or_(
                    # تداخل عادی
                    and_(
                        Reservation.check_in < check_out_time,
                        Reservation.check_out > check_in_time
                    )
                )
            ).all()
            
            print(f"📊 تعداد رزروهای متضاد: {len(conflicting_reservations)}")
            
            # اگر رزرو متضاد وجود ندارد، اتاق آزاد است
            if not conflicting_reservations:
                return True, []
            
            # بررسی امکان Back-to-Back
            back_to_back_possible = True
            conflicts_info = []
            
            for reservation in conflicting_reservations:
                print(f"  🔍 بررسی رزرو {reservation.id}: {reservation.check_in} تا {reservation.check_out}")
                
                # اگر رزرو موجود دقیقاً در زمان check-out تمام شود و رزرو جدید شروع شود
                if (reservation.check_out == check_in_time and 
                    reservation.status == 'checked_in'):
                    # Back-to-Back ممکن است
                    conflicts_info.append({
                        'type': 'back_to_back_possible',
                        'reservation_id': reservation.id,
                        'check_out': reservation.check_out,
                        'new_check_in': check_in_time,
                        'message': 'امکان Back-to-Back وجود دارد'
                    })
                    print(f"  ✅ Back-to-Back ممکن است با رزرو {reservation.id}")
                else:
                    # تداخل واقعی وجود دارد
                    back_to_back_possible = False
                    conflicts_info.append({
                        'type': 'conflict',
                        'reservation_id': reservation.id,
                        'check_in': reservation.check_in,
                        'check_out': reservation.check_out,
                        'message': f'تداخل با رزرو {reservation.id}'
                    })
                    print(f"  ❌ تداخل با رزرو {reservation.id}")
            
            print(f"🎯 نتیجه: Back-to-Back ممکن است = {back_to_back_possible}")
            return back_to_back_possible, conflicts_info
            
        except Exception as e:
            print(f"❌ خطا در بررسی اتاق: {e}")
            import traceback
            traceback.print_exc()
            return False, [{'type': 'error', 'message': str(e)}]
        finally:
            session.close()
    
    def is_room_available(self, room_id, check_in, check_out):
        """بررسی موجود بودن اتاق در بازه زمانی مشخص با پشتیبانی از Back-to-Back"""
        try:
            # استفاده از تابع جدید برای بررسی دقیق‌تر
            is_available, conflicts = self.get_room_availability_with_back_to_back(room_id, check_in, check_out)
            
            # اگر Back-to-Back ممکن است، اتاق را available در نظر بگیر
            if is_available:
                return True
                
            # اگر تداخل واقعی وجود دارد
            for conflict in conflicts:
                if conflict['type'] == 'conflict':
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ خطا در بررسی موجودی اتاق: {e}")
            return False

    def create_reservation_with_back_to_back_check(self, reservation_data, guest_data, changed_by="سیستم"):
        """ایجاد رزرو جدید با بررسی دقیق Back-to-Back"""
        try:
            room_id = reservation_data['room_id']
            check_in = reservation_data['check_in']
            check_out = reservation_data['check_out']
            
            print(f"🎯 شروع ایجاد رزرو با بررسی Back-to-Back")
            print(f"🏨 اتاق: {room_id}")
            print(f"📅 ورود: {check_in}")
            print(f"📅 خروج: {check_out}")
            
            # بررسی دقیق موجودی اتاق
            is_available, conflicts = self.get_room_availability_with_back_to_back(room_id, check_in, check_out)
            
            if not is_available:
                conflict_messages = []
                for conflict in conflicts:
                    if conflict['type'] == 'conflict':
                        conflict_messages.append(conflict['message'])
                
                if conflict_messages:
                    return False, "اتاق در تاریخ انتخاب شده قابل رزرو نیست. تداخل با رزروهای موجود.", None
                else:
                    return False, "اتاق در تاریخ انتخاب شده قابل رزرو نیست.", None
            
            # اگر اتاق available است، رزرو را ایجاد کن
            return self.create_reservation(reservation_data, guest_data, changed_by)
            
        except Exception as e:
            print(f"❌ خطا در ایجاد رزرو با بررسی Back-to-Back: {e}")
            return False, f"خطا در ایجاد رزرو: {str(e)}", None


    def get_room_back_to_back_status(self, room_id, date):
        """دریافت وضعیت Back-to-Back برای یک اتاق در تاریخ مشخص"""
        session = self.Session()
        try:
            from sqlalchemy import and_, or_
            
            target_date = date.replace(hour=14, minute=0, second=0, microsecond=0)
            
            # رزروی که در این تاریخ تمام می‌شود
            ending_reservation = session.query(Reservation, Guest).join(
                Guest, and_(Reservation.guest_id == Guest.id)
            ).filter(
                Reservation.room_id == room_id,
                Reservation.check_out == target_date,
                Reservation.status.in_(['confirmed', 'checked_in'])
            ).first()
            
            # رزروی که در این تاریخ شروع می‌شود
            starting_reservation = session.query(Reservation, Guest).join(
                Guest, and_(Reservation.guest_id == Guest.id)
            ).filter(
                Reservation.room_id == room_id,
                Reservation.check_in == target_date,
                Reservation.status.in_(['confirmed', 'checked_in'])
            ).first()
            
            result = {
                'has_ending': ending_reservation is not None,
                'has_starting': starting_reservation is not None,
                'is_back_to_back': ending_reservation is not None and starting_reservation is not None
            }
            
            if ending_reservation:
                res, guest = ending_reservation
                result['ending_guest'] = f"{guest.first_name} {guest.last_name}"
                result['ending_reservation_id'] = res.id
                
            if starting_reservation:
                res, guest = starting_reservation
                result['starting_guest'] = f"{guest.first_name} {guest.last_name}"
                result['starting_reservation_id'] = res.id
                
            return result
            
        except Exception as e:
            print(f"❌ خطا در دریافت وضعیت Back-to-Back: {e}")
            return {'has_ending': False, 'has_starting': False, 'is_back_to_back': False}
        finally:
            session.close()

    
    def get_room_status(self, room_id, date):
        """دریافت وضعیت اتاق در تاریخ مشخص"""
        session = self.Session()
        
        try:
            reservation = session.query(Reservation).filter(
                Reservation.room_id == room_id,
                Reservation.check_in <= date,
                Reservation.check_out > date,
                Reservation.status.in_(['confirmed', 'checked_in'])
            ).first()
            
            return reservation.status if reservation else 'vacant'
        finally:
            session.close()
    
    def get_daily_occupancy(self, date):
        """دریافت آمار اشغال روزانه"""
        session = self.Session()
        
        try:
            total_rooms = session.query(Room).filter(Room.is_active == True).count()
            occupied_rooms = session.query(Reservation).filter(
                Reservation.check_in <= date,
                Reservation.check_out > date,
                Reservation.status.in_(['confirmed', 'checked_in'])
            ).count()
            
            return {
                'total_rooms': total_rooms,
                'occupied_rooms': occupied_rooms,
                'occupancy_rate': (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0
            }
        finally:
            session.close()
    
    def get_todays_arrivals(self):
        """دریافت تعداد ورودی‌های امروز"""
        session = self.Session()
        today = datetime.now().date()
        
        try:
            arrivals = session.query(Reservation).filter(
                Reservation.check_in <= today,
                Reservation.check_out > today,
                Reservation.status == 'confirmed'
            ).count()
            
            return arrivals
        finally:
            session.close()
    
    def get_todays_departures(self):
        """دریافت تعداد خروجی‌های امروز"""
        session = self.Session()
        today = datetime.now().date()
        
        try:
            departures = session.query(Reservation).filter(
                Reservation.check_out == today,
                Reservation.status == 'checked_in'
            ).count()
            
            return departures
        finally:
            session.close()

    def get_active_users(self):
        """دریافت لیست کاربران فعال از لاگ‌ها"""
        session = self.Session()
        try:
            users = session.query(SystemLog.changed_by).distinct().all()
            return [user[0] for user in users]
        except Exception as e:
            print(f"خطا در دریافت کاربران فعال: {e}")
            return []
        finally:
            session.close()

    def clear_old_logs(self, days=90):
        """پاک کردن لاگ‌های قدیمی"""
        session = self.Session()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = session.query(SystemLog).filter(
                SystemLog.changed_at < cutoff_date
            ).delete()
            session.commit()
            print(f"✅ {deleted_count} لاگ قدیمی پاک شد")
            return deleted_count
        except Exception as e:
            session.rollback()
            print(f"❌ خطا در پاک کردن لاگ‌های قدیمی: {e}")
            return 0
        finally:
            session.close()