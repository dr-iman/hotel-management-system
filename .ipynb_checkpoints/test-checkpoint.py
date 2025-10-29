# remove_pyqt_completely.py
import subprocess
import sys
import os
import platform

def run_command(command, description=""):
    """اجرای یک دستور و مدیریت خروجی"""
    print(f"\n🎯 {description}...")
    print(f"   $ {command}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            check=True
        )
        if result.stdout.strip():
            print(f"   ✅ خروجی: {result.stdout.strip()}")
        else:
            print(f"   ✅ اجرا شد")
        return True
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else e.stdout.strip()
        if "not installed" in error_msg.lower() or "not found" in error_msg.lower():
            print(f"   ℹ️  از قبل حذف شده")
        else:
            print(f"   ⚠️  خطا: {error_msg}")
        return False

def get_pyqt_packages():
    """لیست تمام پکیج‌های مرتبط با PyQt"""
    return [
        # PyQt6
        "PyQt6", "PyQt6-sip", "PyQt6_Qwt", "PyQt6_Qt6", "PyQt6_3D", 
        "PyQt6_WebEngine", "PyQt6_WebEngineWidgets", "PyQt6_Network",
        "PyQt6_NetworkAuth", "PyQt6_Nfc", "PyQt6_Bluetooth", "PyQt6_SerialPort",
        
        # PyQt5
        "PyQt5", "PyQt5-sip", "PyQt5-Qt5", "PyQt5-stubs", "PyQt5-Qwt",
        "PyQt5_WebEngine", "PyQt5_WebEngineWidgets", "PyQt5_Network",
        "PyQt5_NetworkAuth", "PyQt5_Nfc", "PyQt5_Bluetooth", "PyQt5_SerialPort",
        
        # PySide
        "PySide2", "PySide6", "PySide2-stubs", "PySide6-stubs",
        
        # SIP و وابستگی‌ها
        "sip", "PyQt6_sip", "PyQt5_sip",
        
        # پکیج‌های قدیمی
        "PyQt4", "PyQt4-Phonon", "PyQt4-Qt4",
        
        # پکیج‌های مرتبط دیگر
        "qtpy", "qtconsole", "qtawesome", "qt-material",
        "pyqtgraph", "pyqtdatavisualization", "pyqtchart"
    ]

def uninstall_with_pip3():
    """حذف با pip3"""
    print("=" * 50)
    print("🗑️  حذف با pip3")
    print("=" * 50)
    
    packages = get_pyqt_packages()
    success_count = 0
    
    for package in packages:
        command = f"pip3 uninstall -y {package}"
        if run_command(command, f"حذف {package} با pip3"):
            success_count += 1
    
    print(f"\n📊 با pip3: {success_count}/{len(packages)} پکیج پردازش شد")

def uninstall_with_python3_pip():
    """حذف با python3 -m pip"""
    print("\n" + "=" * 50)
    print("🗑️  حذف با python3 -m pip")
    print("=" * 50)
    
    packages = get_pyqt_packages()
    success_count = 0
    
    for package in packages:
        command = f"python3 -m pip uninstall -y {package}"
        if run_command(command, f"حذف {package} با python3 -m pip"):
            success_count += 1
    
    print(f"\n📊 با python3 -m pip: {success_count}/{len(packages)} پکیج پردازش شد")

def uninstall_with_pip():
    """حذف با pip (پیش‌فرض)"""
    print("\n" + "=" * 50)
    print("🗑️  حذف با pip")
    print("=" * 50)
    
    packages = get_pyqt_packages()
    success_count = 0
    
    for package in packages:
        command = f"pip uninstall -y {package}"
        if run_command(command, f"حذف {package} با pip"):
            success_count += 1
    
    print(f"\n📊 با pip: {success_count}/{len(packages)} پکیج پردازش شد")

def clean_pip_cache():
    """پاکسازی cache pip"""
    print("\n" + "=" * 50)
    print("🧹 پاکسازی cache")
    print("=" * 50)
    
    commands = [
        "pip3 cache purge",
        "python3 -m pip cache purge",
        "pip cache purge"
    ]
    
    for cmd in commands:
        run_command(cmd, "پاکسازی cache")

def verify_uninstallation():
    """بررسی حذف کامل"""
    print("\n" + "=" * 50)
    print("🔍 بررسی حذف کامل")
    print("=" * 50)
    
    test_packages = ["PyQt6", "PyQt5", "PySide6", "PySide2"]
    
    for package in test_packages:
        try:
            __import__(package)
            print(f"   ❌ {package}: هنوز نصب شده!")
        except ImportError:
            print(f"   ✅ {package}: حذف شده")

def list_remaining_qt_packages():
    """لیست پکیج‌های Qt باقی مانده"""
    print("\n" + "=" * 50)
    print("📋 بررسی پکیج‌های باقی مانده")
    print("=" * 50)
    
    commands = [
        "pip3 list | grep -i qt",
        "python3 -m pip list | grep -i qt",
        "pip list | grep -i qt"
    ]
    
    for cmd in commands:
        print(f"\n🎯 اجرای: {cmd}")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.stdout.strip():
                print("   📦 پکیج‌های باقی مانده:")
                for line in result.stdout.strip().split('\n'):
                    print(f"      {line}")
            else:
                print("   ✅ هیچ پکیج Qt-related یافت نشد")
        except Exception as e:
            print(f"   ⚠️ خطا: {e}")

def manual_cleanup_suggestions():
    """پیشنهادات پاکسازی دستی"""
    print("\n" + "=" * 50)
    print("💡 پیشنهادات پاکسازی دستی")
    print("=" * 50)
    
    system = platform.system()
    
    if system == "Windows":
        suggestions = [
            "مسیرهای احتمالی برای پاکسازی دستی:",
            "1. C:\\Users\\[Username]\\AppData\\Local\\Programs\\Python\\Python*\\Lib\\site-packages\\PyQt*",
            "2. C:\\Python*\\Lib\\site-packages\\PyQt*",
            "3. C:\\Program Files\\Python*\\Lib\\site-packages\\PyQt*",
            "",
            "دستورات مفید:",
            "- dir C:\\Python* /s | findstr /i pyqt",
            "- del /s /q C:\\Python*\\Lib\\site-packages\\PyQt*"
        ]
    elif system == "Linux":
        suggestions = [
            "مسیرهای احتمالی برای پاکسازی دستی:",
            "1. /usr/local/lib/python*/dist-packages/PyQt*",
            "2. /usr/lib/python*/dist-packages/PyQt*",
            "3. ~/.local/lib/python*/site-packages/PyQt*",
            "",
            "دستورات مفید:",
            "- find /usr -name '*PyQt*' -type d 2>/dev/null",
            "- rm -rf ~/.local/lib/python*/site-packages/PyQt*"
        ]
    else:  # macOS
        suggestions = [
            "مسیرهای احتمالی برای پاکسازی دستی:",
            "1. /Library/Frameworks/Python.framework/Versions/*/lib/python*/site-packages/PyQt*",
            "2. /usr/local/lib/python*/site-packages/PyQt*",
            "3. ~/Library/Python/*/lib/python/site-packages/PyQt*",
            "",
            "دستورات مفید:",
            "- find /usr -name '*PyQt*' -type d 2>/dev/null",
            "- rm -rf ~/Library/Python/*/lib/python/site-packages/PyQt*"
        ]
    
    for suggestion in suggestions:
        print(f"   {suggestion}")

def main():
    """تابع اصلی"""
    print("=" * 60)
    print("🗑️  حذف کامل PyQt از سیستم")
    print("=" * 60)
    
    # نمایش اطلاعات سیستم
    print(f"💻 سیستم عامل: {platform.system()} {platform.release()}")
    print(f"🐍 پایتون: {sys.version}")
    
    # تایید کاربر
    print("\n⚠️  هشدار: این عملیات تمام پکیج‌های PyQt را حذف می‌کند!")
    response = input("آیا مطمئن هستید؟ (y/بله): ").strip().lower()
    
    if response not in ['y', 'yes', 'بله', 'ن']:
        print("❌ عملیات لغو شد")
        return
    
    # حذف با روش‌های مختلف
    uninstall_with_pip3()
    uninstall_with_python3_pip()
    uninstall_with_pip()
    
    # پاکسازی cache
    clean_pip_cache()
    
    # بررسی نتایج
    verify_uninstallation()
    list_remaining_qt_packages()
    
    # پیشنهادات
    manual_cleanup_suggestions()
    
    print("\n" + "=" * 60)
    print("🎉 عملیات حذف کامل شد!")
    print("💡 در صورت نیاز از پیشنهادات پاکسازی دستی استفاده کنید")
    print("=" * 60)

if __name__ == "__main__":
    main()