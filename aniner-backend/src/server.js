/**
 * 🔥 Aniner Backend - Local Dev Server (Node.js)
 * برای تست محلی - نسخه Cloudflare Worker اصلی تو worker.js هست
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 3000;

// Mock data
const ADBLOCK_LISTS = {
  easylist: ["doubleclick.net", "googlesyndication.com", "googleadservices.com", "facebook.com/tr"],
  iranian: ["ad.ir", "sabavision.com"],
  total: 100
};

const VPN_SERVERS = [
  { id: 'de-frankfurt', country: '🇩🇪 آلمان', city: 'فرانکفورت', ip: '185.199.1.1', load: 23, ping: 45 },
  { id: 'nl-amsterdam', country: '🇳🇱 هلند', city: 'آمستردام', ip: '185.199.2.1', load: 45, ping: 52 },
  { id: 'ir-tehran', country: '🇮🇷 ایران', city: 'تهران', ip: '185.199.6.1', load: 12, ping: 20, note: 'برای بانک‌ها' },
];

function jsonResponse(res, data, status=200) {
  res.writeHead(status, {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  });
  res.end(JSON.stringify(data, null, 2));
}

function htmlResponse(res, html) {
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  res.end(html);
}

const server = http.createServer((req, res) => {
  // CORS preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(200, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    });
    res.end();
    return;
  }

  const url = new URL(req.url, `http://${req.headers.host}`);
  const pathname = url.pathname;

  console.log(`[${new Date().toISOString()}] ${req.method} ${pathname}`);

  // Routes
  if (pathname === '/' || pathname === '/api') {
    return htmlResponse(res, `
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head><meta charset="UTF-8"><title>Aniner Backend - سرور واقعی</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box;font-family:system-ui}
  body{background:#0a0a0f;color:#fff;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
  .card{background:#11111a;border:1px solid #ffffff14;border-radius:24px;padding:40px;max-width:700px;width:100%}
  .logo{width:80px;height:80px;border-radius:20px;background:linear-gradient(135deg,#7c3aed,#ec4899);display:flex;align-items:center;justify-content:center;font-size:40px;font-weight:900;margin:0 auto 20px}
  h1{text-align:center}
  .status{background:#10b98122;border:1px solid #10b98133;border-radius:20px;padding:8px 16px;color:#34d399;text-align:center;margin:20px 0}
  .endpoint{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #ffffff06;font-family:monospace;font-size:13px}
  .btn{display:inline-flex;padding:10px 20px;border-radius:12px;background:linear-gradient(135deg,#7c3aed,#ec4899);color:#fff;text-decoration:none;margin:4px}
</style>
</head>
<body>
<div class="card">
  <div class="logo">A</div>
  <h1>🔥 Aniner Backend v2.0 - سرور واقعی!</h1>
  <p style="opacity:.7;text-align:center;margin:12px 0">سرور بک‌اند برای مرورگر Aniner - روی پورت ${PORT} کار میکنه!</p>
  <div class="status">✅ سرور واقعی کار میکنه! - ${new Date().toLocaleString('fa-IR')}</div>
  <div style="background:#0a0a0f;border-radius:12px;padding:16px;margin:20px 0">
    <div class="endpoint"><span>GET /api/health</span><span>سلامتی</span></div>
    <div class="endpoint"><span>GET /api/adblock/list</span><span>AdBlock</span></div>
    <div class="endpoint"><span>GET /api/vpn/servers</span><span>VPN</span></div>
    <div class="endpoint"><span>POST /api/auth/register</span><span>ثبت‌نام</span></div>
    <div class="endpoint"><span>GET /api/stats</span><span>آمار</span></div>
  </div>
  <div style="text-align:center">
    <a class="btn" href="/api/health">Health</a>
    <a class="btn" href="/api/adblock/list">AdBlock</a>
    <a class="btn" href="/api/vpn/servers">VPN</a>
    <a class="btn" href="/api/stats">Stats</a>
  </div>
</div>
</body>
</html>
    `);
  }

  if (pathname === '/api/health') {
    return jsonResponse(res, {
      status: 'ok',
      uptime: '99.9%',
      version: '2.0.0',
      message: '✅ Aniner Backend سرور واقعی کار میکنه!',
      timestamp: new Date().toISOString(),
      port: PORT,
    });
  }

  if (pathname === '/api/adblock/list') {
    return jsonResponse(res, {
      easylist: ADBLOCK_LISTS.easylist,
      iranian: ADBLOCK_LISTS.iranian,
      total: 100,
      updated: new Date().toISOString(),
    });
  }

  if (pathname === '/api/vpn/servers') {
    return jsonResponse(res, {
      servers: VPN_SERVERS,
      total: VPN_SERVERS.length,
      updated: new Date().toISOString(),
    });
  }

  if (pathname === '/api/stats') {
    return jsonResponse(res, {
      total_users: 10234,
      total_downloads: 54321,
      total_blocked_ads: 1234567,
      version: '2.0.0',
      timestamp: new Date().toISOString(),
    });
  }

  if (pathname.startsWith('/api/')) {
    return jsonResponse(res, { error: 'API endpoint not found', path: pathname }, 404);
  }

  // 404
  res.writeHead(404, { 'Content-Type': 'text/html' });
  res.end('<h1>404 - Not Found - Aniner Backend</h1>');
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`🔥 Aniner Backend v2.0 - سرور واقعی کار میکنه!`);
  console.log(`📡 http://0.0.0.0:${PORT}`);
  console.log(`📡 http://localhost:${PORT}`);
  console.log(`✅ Endpoints: /api/health, /api/adblock/list, /api/vpn/servers, /api/stats`);
});
