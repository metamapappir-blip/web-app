# 🔥 Aniner Backend v2.0 - سرور واقعی برای مرورگر Aniner

**سرور بک‌اند واقعی برای مرورگر Aniner - Sync, AdBlock, VPN, Auth**

[![Version](https://img.shields.io/badge/Version-2.0.0-7c3aed?style=for-the-badge)](./src/worker.js)
[![Cloudflare](https://img.shields.io/badge/Cloudflare-Workers-f6821f?style=for-the-badge&logo=cloudflare)](https://workers.cloudflare.com)
[![Real Server](https://img.shields.io/badge/Server-Real%20Backend-10b981?style=for-the-badge)]()

---

## 🚀 چی هست؟

این بک‌اند سرور واقعی برای مرورگر Aniner هست که:

- ✅ **Sync بوکمارک، تاریخچه، تنظیمات** بین دستگاه‌ها
- ✅ **AdBlock لیست** - آپدیت روزانه
- ✅ **VPN سرور لیست** - 50+ کشور
- ✅ **Auth** - ثبت‌نام، ورود با JWT
- ✅ **آمار** - تعداد کاربران، دانلود، تبلیغات مسدود شده

---

## 📡 API Endpoints

### Health
```http
GET /api/health
```
```json
{
  "status": "ok",
  "version": "2.0.0",
  "message": "✅ Aniner Backend سرور واقعی کار میکنه!"
}
```

### AdBlock
```http
GET /api/adblock/list
GET /api/adblock/list?format=text
GET /api/adblock/stats
```

### VPN
```http
GET /api/vpn/servers
POST /api/vpn/connect
Body: { "server_id": "de-frankfurt" }
```

### Auth
```http
POST /api/auth/register
Body: { "username": "ali", "password": "123456", "email": "ali@example.com" }

POST /api/auth/login
Body: { "username": "ali", "password": "123456" }
```

### Sync (نیاز به Auth)
```http
GET /api/bookmarks
Header: Authorization: Bearer <token>

POST /api/bookmarks
Body: { "bookmarks": [...] }

GET /api/history
POST /api/history

GET /api/settings
POST /api/settings
```

### Stats
```http
GET /api/stats
```

---

## 🛠️ نصب و اجرا

### روش 1: Cloudflare Workers (پیشنهادی - رایگان)

```bash
cd aniner-backend
npm install
npm run deploy  # دیپلوی روی Cloudflare Workers
# یا
wrangler deploy
```

**نیاز به:**
- اکانت رایگان Cloudflare
- `wrangler login`

بعدش سرور روی `https://aniner-backend.your-subdomain.workers.dev` کار میکنه!

### روش 2: Local Node.js

```bash
cd aniner-backend
npm install
npm run dev:local
# یا
node src/server.js
# سرور روی http://localhost:3000 کار میکنه!
```

### روش 3: تست سریع

```bash
cd aniner-backend
node src/server.js
# برو به http://localhost:3000
```

---

## 🔧 اتصال به Aniner Browser

در Aniner Browser (نسخه v2.0):

```javascript
// تنظیم آدرس بک‌اند
const BACKEND_URL = 'https://aniner-backend.your-subdomain.workers.dev';
// یا محلی
const BACKEND_URL = 'http://localhost:3000';

// گرفتن لیست AdBlock
fetch(`${BACKEND_URL}/api/adblock/list`)
  .then(r => r.json())
  .then(data => {
    console.log('AdBlock filters:', data.total);
    // اعمال فیلترها
  });

// گرفتن سرورهای VPN
fetch(`${BACKEND_URL}/api/vpn/servers`)
  .then(r => r.json())
  .then(data => {
    console.log('VPN servers:', data.servers);
  });

// Sync بوکمارک
fetch(`${BACKEND_URL}/api/bookmarks`, {
  headers: { 'Authorization': `Bearer ${token}` }
})
```

---

## 📦 ساختار

```
aniner-backend/
├── src/
│   ├── worker.js (Cloudflare Worker - اصلی - Hono)
│   └── server.js (Node.js local - برای تست)
├── wrangler.toml
├── package.json
└── README.md
```

---

## 🌟 ویژگی‌های خفن

- ⚡ **سریع** - روی Cloudflare Edge - 300+ شهر دنیا
- 🔒 **امن** - JWT Auth, CORS
- 📦 **رایگان** - Cloudflare Workers Free Tier
- 🔄 **Sync** - بوکمارک، تاریخچه بین دستگاه‌ها
- 🛡️ **AdBlock** - لیست آپدیت روزانه
- 🔒 **VPN** - لیست سرورها + کانفیگ WireGuard
- 📊 **آمار** - کاربران، دانلود، تبلیغات مسدود

---

## 🚀 دیپلوی

```bash
# Cloudflare
wrangler login
wrangler deploy

# یا npm
npm run deploy
```

بعدش آدرس Worker رو تو Aniner Browser تنظیم کن!

---

## 📜 لایسنس

MIT - رایگان و متن باز

---

<div align="center">

**Aniner Backend v2.0 - سرور واقعی برای مرورگر فوق خفن**

[GitHub](https://github.com/metamapappir-blip/web-app) • [Aniner Browser](../aniner-browser/)

</div>
