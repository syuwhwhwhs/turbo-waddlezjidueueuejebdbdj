# Taha Emoji Studio

ربات تلگرام + Mini App برای شناسایی Custom Emoji ID، نمایش پیش‌نمایش خود ایموجی، افزودن متن/لوگو، پردازش و ارسال خروجی و ساخت پک اختصاصی.

## نصب مستقیم از GitHub روی Ubuntu 22.04/24.04

ابتدا مخزن را در GitHub بساز و فایل‌های همین پروژه را در ریشه مخزن قرار بده. سپس در SSH سرور:

```bash
sudo apt update && sudo apt install -y git
 git clone https://github.com/USERNAME/REPOSITORY.git taha_emoji_studio
cd taha_emoji_studio
chmod +x install.sh
./install.sh
```

به‌جای `USERNAME/REPOSITORY` آدرس واقعی مخزن خودت را قرار بده.

سپس تنظیمات را باز کن:

```bash
nano .env
```

این مقدارها را وارد کن:

```env
BOT_TOKEN=توکن_ربات_از_BotFather
BOT_USERNAME=نام_ربات_بدون_علامت_@
WEBAPP_URL=https://دامنه-واقعی-تو
ADMIN_IDS=آیدی_عددی_تلگرام_مدیر
DATABASE_PATH=data/studio.db
WORK_DIR=data/work
HOST=127.0.0.1
PORT=8000
```

`WEBAPP_URL` باید HTTPS باشد و به همین برنامه برسد. توکن را داخل GitHub قرار نده؛ فایل `.env` در `.gitignore` است.

## اجرا برای تست

ترمینال اول:

```bash
cd ~/taha_emoji_studio
.venv/bin/python server.py
```

ترمینال دوم:

```bash
cd ~/taha_emoji_studio
.venv/bin/python run.py
```

## اجرای دائمی با systemd

فایل‌های نمونه در `deploy/` هستند. در هر دو فایل مسیر `/opt/taha_emoji_studio` را با مسیر نصب خودت هماهنگ کن. سپس:

```bash
sudo cp deploy/taha-web.service.example /etc/systemd/system/taha-web.service
sudo cp deploy/taha-bot.service.example /etc/systemd/system/taha-bot.service
sudo systemctl daemon-reload
sudo systemctl enable --now taha-web taha-bot
sudo systemctl status taha-web taha-bot
```

اگر پروژه را در `/home/ubuntu/taha_emoji_studio` نصب کرده‌ای، مسیر `WorkingDirectory`، `EnvironmentFile` و `ExecStart` داخل هر دو فایل سرویس باید به همان مسیر تغییر کند. نام کاربر سرویس را هم با کاربر لینوکس خودت هماهنگ کن.

## اتصال دامنه و Mini App

برنامه وب به‌صورت پیش‌فرض روی پورت 8000 اجرا می‌شود. آن را پشت Nginx یا Caddy با گواهی SSL منتشر کن؛ دامنه HTTPS را در `WEBAPP_URL` بگذار. سپس در BotFather از تنظیمات Web App / Menu Button همان آدرس HTTPS را ثبت کن.

## نمایش فوری ایموجی در Mini App

- آیدی عددی را وارد یا Paste کن؛ پس از مکث کوتاه، جست‌وجو خودکار شروع می‌شود. دکمه «پیدا کردن ایموجی» هم فعال است.
- API ابتدا مشخصات ایموجی را از Telegram می‌گیرد و سپس فایل پیش‌نمایش را با توکن مخفی سرور دریافت می‌کند؛ توکن هرگز به مرورگر فرستاده نمی‌شود.
- WEBP به‌صورت تصویر، WEBM به‌صورت ویدیوی متحرک و TGS با rlottie به پیش‌نمایش متحرک WebP تبدیل می‌شود.
- پیش‌نمایش روی سرور cache می‌شود تا دفعات بعد سریع‌تر باز شود.

سرعت واقعی به اینترنت سرور، پاسخ Telegram و اولین بار دانلود فایل وابسته است؛ هیچ سرویس آنلاین نمی‌تواند تأخیر شبکه را صفر تضمین کند. در استفاده بعدی، cache از دانلود مجدد پیش‌نمایش جلوگیری می‌کند.

## امکانات و محدودیت‌ها

- انتخاب زبان فارسی/انگلیسی و ذخیره زبان هر کاربر.
- شناسایی ایموجی با ID یا ارسال خود ایموجی به ربات.
- نمایش پیش‌نمایش، نام/نماد و نوع فایل در Mini App.
- انتخاب لوگو از گالری (PNG/JPG/WEBP، حداکثر ۵ مگابایت) یا درج متن.
- حفظ حرکت TGS با تبدیل فریم‌ها به خروجی ویدیویی WEBM؛ WEBM ورودی نیز متحرک می‌ماند.
- صف پردازش، تاریخچه درخواست‌ها، پروفایل و آمار پایه مدیر.
- ارسال نتیجه به چت و پرسیدن اجازه برای افزودن به پک اختصاصی.

متن یا لوگوی جدید روی طرح موجود قرار می‌گیرد؛ پاک‌کردن هوشمند و بازسازی طرح زیرین (inpainting) در این نسخه نیست. TGS به WEBM تبدیل می‌شود، بنابراین خروجی متحرک است اما فرمت برداری TGS باقی نمی‌ماند. ساخت پک به پشتیبانی Telegram Bot API و محدودیت‌های فرمت/حساب وابسته است و باید با ربات واقعی آزمایش شود.

## به‌روزرسانی نسخه از GitHub

```bash
cd ~/taha_emoji_studio
git pull
.venv/bin/pip install -r requirements.txt
sudo systemctl restart taha-web taha-bot
```

پوشه `data/` و فایل `.env` را حذف نکن؛ دیتابیس و اطلاعات کاربران آنجاست.
