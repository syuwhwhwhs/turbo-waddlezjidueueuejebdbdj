# RoXeT BoT

نسخه جایگزین پروژه قبلی با برند RoXeT BoT و رابط موبایلی الهام‌گرفته از تصویر مرجع: پس‌زمینه یاسی، کارت‌های سفید گرد، گرادیان آبی/فیروزه‌ای و منوی شناور پایین صفحه.

## نصب روی Ubuntu

سورس را در GitHub قرار بده و روی سرور اجرا کن:

```bash
sudo su -
apt update && apt install -y git
 git clone YOUR_GITHUB_REPOSITORY_URL /opt/roxet-source
cd /opt/roxet-source
chmod +x install.sh
./install.sh
```

نصب‌کننده با منو و پیام‌های انگلیسی، توکن ربات، نام کاربری، آیدی ادمین، آدرس HTTPS مینی‌اپ و پورت را می‌پرسد. سپس تنظیمات را فقط در `/opt/roxet-bot/.env` با دسترسی محدود ذخیره می‌کند و دو سرویس دائمی systemd برای ربات و وب‌سرور می‌سازد. برنامه با کاربر عادی لینوکس اجرا می‌شود، نه root.

## مدیریت سرویس‌ها

```bash
systemctl status roxet-bot
systemctl status roxet-web
systemctl restart roxet-bot roxet-web
journalctl -u roxet-bot -f
```

## امنیت

- هرگز `.env` یا توکن را در GitHub آپلود نکن.
- `WEBAPP_URL` باید HTTPS معتبر داشته باشد تا Telegram Mini App باز شود.
- نصب‌کننده باید از داخل پوشه سورس اجرا شود.

## قابلیت‌ها

- جست‌وجو و پیش‌نمایش Custom Emoji ID
- پشتیبانی از منابع TGS، WEBM و WEBP در مسیر پردازش موجود پروژه
- انتخاب متن یا لوگو و ارسال خروجی به چت ربات
- تاریخچه درخواست‌ها، پروفایل، زبان فارسی/انگلیسی و صفحه مدیریت

توجه: سازگاری نهایی ساخت پک و پردازش فرمت‌ها به محدودیت‌های Telegram Bot API و تست روی ربات واقعی وابسته است.
