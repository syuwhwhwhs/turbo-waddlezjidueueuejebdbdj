D={
'fa':{
'welcome':'به Taha Emoji Studio خوش آمدی ✨','choose':'زبانت را انتخاب کن / Choose your language',
'open':'🚀 ورود به مینی‌اپ','saved':'زبان فارسی ذخیره شد.','need':'آدرس HTTPS مینی‌اپ تنظیم نشده است.',
'help':'برای شروع، ایموجی پرمیوم را در مینی‌اپ با آیدی آن جست‌وجو کن. سپس متن یا لوگو را انتخاب کن.',
'waiting':'درخواستت ثبت شد. برای جایگزینی لوگو، لینک مستقیم تصویر را وارد کن؛ برای تغییر نوشته، متن جدید را بفرست.',
'yes':'✅ بله، به پک اضافه کن','no':'❌ نه، فقط فایل را بفرست','askpack':'ایموجی آماده شد! می‌خواهی به پک اختصاصی‌ات اضافه کنم؟',
'added':'به پک اضافه شد:','failed':'ساخت این فرمت در حال حاضر پشتیبانی نمی‌شود یا پردازش ناموفق بود.',
'admin':'پنل مدیریت','stats':'کاربران: {users}\nدرخواست‌ها: {jobs}','cancel':'لغو'
},
'en':{
'welcome':'Welcome to Taha Emoji Studio ✨','choose':'Choose your language',
'open':'🚀 Open Mini App','saved':'English saved.','need':'Mini App HTTPS URL is not configured.',
'help':'Open the Mini App, look up a Premium Emoji by ID, then choose text or logo replacement.',
'waiting':'Your request is saved. For a logo, provide a direct image URL; for text replacement, send the new text.',
'yes':'✅ Yes, add to my pack','no':'❌ No, just send the file','askpack':'Your emoji is ready! Would you like me to add it to your pack?',
'added':'Added to your pack:','failed':'This format is not supported by the current renderer or processing failed.',
'admin':'Admin panel','stats':'Users: {users}\nJobs: {jobs}','cancel':'Cancel'
}}
def t(lang,key,**kwargs):
    value=D.get(lang,D['fa']).get(key,key)
    return value.format(**kwargs)
