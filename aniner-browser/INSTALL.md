# 📥 نصب Aniner Browser - راهنمای کامل

## 🔥 روش 1: نصب سریع با آیکون دسکتاپ (پیشنهادی - 10 ثانیه)

### ویندوز:

1. **دانلود کن:**
   - `Aniner-Setup.exe` (834 KB)
   - `WebView2Loader.dll` (159 KB) - باید کنار Setup باشه
   - `icon.ico` (اختیاری)

   یا همه رو یکجا:
   - `Aniner-Portable.zip` (2.1 MB) را دانلود و Extract کن

2. **نصب کن:**
   - روی `Aniner-Setup.exe` دابل کلیک کن
   - پیام "به نصب Aniner خوش آمدید" میاد - **Yes** بزن
   - صبر کن 2 ثانیه...

3. **تمام!**
   - ✅ آیکون **Aniner Browser** روی دسکتاپ ساخته شد
   - ✅ آیکون در منوی استارت ساخته شد
   - روی آیکون دسکتاپ دابل کلیک کن!

### چی شد؟

نصاب این کارها رو کرد:
- فایل‌ها رو به `C:\Program Files\Aniner\` کپی کرد
- شورتکات روی دسکتاپ ساخت: `C:\Users\YourName\Desktop\Aniner Browser.lnk`
- شورتکات در استارت منو ساخت
- WebView2 Runtime رو چک کرد

---

## 📦 روش 2: پرتابل - بدون نصب

1. `Aniner-Portable.zip` را دانلود کن
2. Extract کن تو یه پوشه (مثلاً `C:\Aniner\`)
3. روی `Aniner.exe` دابل کلیک کن
4. تمام! بدون نصب اجرا میشه

**برای آیکون دسکتاپ دستی:**

- روش A: روی `Aniner.exe` راست کلیک → Send to → Desktop (create shortcut)
- روش B: فایل `Create-Desktop-Shortcut.bat` را اجرا کن
- روش C: PowerShell:
  ```powershell
  .\Create-Desktop-Shortcut.ps1
  ```

---

## 🌐 روش 3: نسخه پیشرفته PyQt (همه قابلیت‌ها)

این نسخه همه قابلیت‌های Electron + بیشتر رو داره:

```bash
# نصب Python 3.11
# نصب PyQt
pip install PyQt5 PyQtWebEngine

# اجرا
cd aniner-browser/src
python aniner_pyqt.py
```

**ساخت EXE از PyQt:**

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=assets/icon.ico --name Aniner-Advanced src/aniner_pyqt.py

# فایل dist/Aniner-Advanced.exe ساخته شد!
```

---

## ⚡ روش 4: نسخه Electron (مثل فایرفاکس واقعی)

```bash
# نصب Node.js 22
cd aniner-browser
npm install
npm start              # اجرا
npm run build:win      # ساخت EXE - dist/Aniner-1.0.0-Portable.exe
```

---

## 🔧 پیش‌نیاز: WebView2 Runtime

Aniner برای اجرا به **Microsoft Edge WebView2 Runtime** نیاز داره.

### آیا دارم؟

- ویندوز 11: ✅ داری (پیش‌فرض)
- ویندوز 10 جدید: ✅ اکثراً دارن
- ویندوز 10 قدیمی / 8 / 7: ❌ باید نصب کنی

### چطور نصب کنم؟

1. برو به: https://developer.microsoft.com/en-us/microsoft-edge/webview2/
2. روی **Download the WebView2 Runtime** کلیک کن
3. Evergreen Bootstrapper را دانلود و نصب کن (2 MB)
4. تمام! حالا Aniner اجرا میشه

یا مستقیم:
https://go.microsoft.com/fwlink/p/?LinkId=2124703

---

## 🖥️ آیکون روی دسکتاپ نیومد؟

### روش دستی 1: PowerShell (خودکار)

```powershell
# تو پوشه Aniner این دستور رو بزن:
.\Create-Desktop-Shortcut.ps1
```

### روش دستی 2: دستی

1. روی `Aniner.exe` راست کلیک کن
2. **Send to** → **Desktop (create shortcut)**
3. روی دسکتاپ برو، روی شورتکات راست کلیک → **Properties**
4. **Change Icon** → `icon.ico` را انتخاب کن
5. OK

### روش دستی 3: Batch

```batch
Create-Desktop-Shortcut.bat
```
را اجرا کن.

---

## 🚀 اجرای Aniner

### از دسکتاپ:
روی آیکون **Aniner Browser** دابل کلیک کن

### از استارت منو:
Start → Aniner → Aniner Browser

### از CMD:
```cmd
"C:\Program Files\Aniner\Aniner.exe"
```

---

## 🔒 اتصال به VPN / V2Ray / Nova Proxy

### VPN داخلی Aniner:

1. Aniner را باز کن
2. روی دکمه 🔒 کلیک کن
3. VPN روشن شد! متصل به آلمان

### اتصال به V2Ray:

1. V2Ray را روی `socks5://127.0.0.1:1080` اجرا کن
2. در Aniner: منو (☰) → تنظیمات → پروکسی
3. `socks5://127.0.0.1:1080` را وارد کن

### Nova Proxy:

- Nova Proxy را دیپلوی کن (DEPLOY.md)
- لینک VLESS را بگیر
- تو V2Ray وارد کن
- Aniner را به V2Ray وصل کن

---

## ❓ مشکلات رایج

### Aniner باز نمیشه؟

- WebView2 Runtime نصب کن (بالا)
- WebView2Loader.dll کنار Aniner.exe باشه
- آنتی‌ویروس چک کن (False positive ممکنه)

### صفحه سفید میاد؟

- اینترنت چک کن
- WebView2 Runtime آپدیت کن

### آیکون نداره؟

- icon.ico کنار exe باشه
- Create-Desktop-Shortcut.ps1 اجرا کن

### چطور آپدیت کنم؟

- نسخه جدید را دانلود کن
- روی قبلی کپی کن
- یا Setup جدید را اجرا کن

---

## 🌟 ستاره بده!

اگه خوشت اومد:

1. برو به: https://github.com/metamapappir-blip/web-app
2. روی ⭐ Star کلیک کن
3. به دوستات معرفی کن!

**هدف: 10k ستاره!**

---

ساخته شده با ❤️ برای اینترنت آزاد
