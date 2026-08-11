```markdown
# NetScanner v2

ابزار آموزشی اسکن پورت TCP با Python برای استفاده در سیستم شخصی و آزمایشگاه مجاز.

## قابلیت‌ها
- اسکن یک پورت یا بازه‌ای از پورت‌ها
- اسکن پورت‌های رایج با `--common`
- اجرای هم‌زمان با Thread
- تعیین Timeout
- دریافت Banner
- ذخیره خروجی در JSON

## هشدار
این ابزار فقط برای:
- سیستم شخصی
- آزمایشگاه محلی
- ماشین مجازی خودت
- هدفی که مجوز صریح دارد

استفاده شود.

## پیش‌نیاز
- Python 3.9+

## اجرا
```bash
python3 port_scanner.py --common
```

اسکن یک بازه:

```bash
python3 port_scanner.py --host 127.0.0.1 --start 1 --end 1024
```

ذخیره خروجی:

```bash
python3 port_scanner.py --common --json result.json
```

## نمونه آزمایش محلی
برای تست امن:

```bash
python3 -m http.server 8000
python3 port_scanner.py --host 127.0.0.1 --start 8000 --end 8000 --banner
```

## وابستگی‌ها
این پروژه فقط از کتابخانه‌های استاندارد Python استفاده می‌کند.

محتوای `requirements.txt`:

```text
# This project uses only Python Standard Library.
# No external packages are required.
```

## مجوز
این پروژه برای آموزش و استفاده دفاعی است.
```
