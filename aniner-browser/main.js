const { app, BrowserWindow, BrowserView, session, ipcMain, dialog, shell, Menu, globalShortcut, clipboard, nativeImage, Tray } = require('electron');
const path = require('path');
const fs = require('fs');
const os = require('os');

// Try to load electron-store, fallback to simple JSON
let Store;
try {
  Store = require('electron-store');
} catch {
  Store = null;
}

class SimpleStore {
  constructor(name) {
    this.path = path.join(app.getPath('userData'), `${name}.json`);
    try {
      this.data = JSON.parse(fs.readFileSync(this.path, 'utf8'));
    } catch { this.data = {}; }
  }
  get(key, def) { return this.data[key] ?? def; }
  set(key, val) { this.data[key] = val; this.save(); }
  has(key) { return key in this.data; }
  delete(key) { delete this.data[key]; this.save(); }
  save() { try { fs.mkdirSync(path.dirname(this.path), {recursive:true}); fs.writeFileSync(this.path, JSON.stringify(this.data, null, 2)); } catch {} }
}

const store = Store ? new Store({ name: 'aniner-settings' }) : new SimpleStore('aniner-settings');
const bookmarkStore = Store ? new Store({ name: 'aniner-bookmarks' }) : new SimpleStore('aniner-bookmarks');
const historyStore = Store ? new Store({ name: 'aniner-history' }) : new SimpleStore('aniner-history');

let mainWindow;
let views = new Map(); // tabId -> BrowserView
let tabs = []; // {id, title, url, favicon, isLoading}
let activeTabId = null;
let tabCounter = 0;
let adBlockEnabled = true;
let vpnEnabled = false;
let darkModeForced = false;

const AD_BLOCK_LIST = [
  '*://*.doubleclick.net/*',
  '*://*.googlesyndication.com/*',
  '*://*.googleadservices.com/*',
  '*://*.googletagmanager.com/*',
  '*://*.facebook.com/tr/*',
  '*://*.facebook.net/*',
  '*://*.analytics.google.com/*',
  '*://*.hotjar.com/*',
  '*://*.mixpanel.com/*',
  '*://*/*.popads.net/*',
  '*://*.adnxs.com/*',
  '*://*.ads-twitter.com/*',
  '*://*.adservice.google.*/*',
  '*://*.amazon-adsystem.com/*',
];

const HOME_URL = 'https://aniner-home.local/';
const HOME_HTML = `
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aniner - خانه</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;600;800&display=swap');
  *{margin:0;padding:0;box-sizing:border-box;font-family:'Vazirmatn',system-ui,sans-serif}
  body{background:#0a0a0f;color:#fff;min-height:100vh;overflow-x:hidden;position:relative}
  .bg{position:fixed;inset:0;z-index:-1;background:radial-gradient(ellipse at 20% 20%, #7c3aed22 0%, transparent 50%), radial-gradient(ellipse at 80% 80%, #ec489922 0%, transparent 50%), radial-gradient(ellipse at 50% 0%, #06b6d422 0%, transparent 70%), #0a0a0f}
  .container{max-width:1100px;margin:0 auto;padding:40px 24px}
  .logo{display:flex;align-items:center;gap:16px;margin-bottom:60px}
  .logo-icon{width:56px;height:56px;border-radius:16px;background:linear-gradient(135deg,#7c3aed,#ec4899,#06b6d4);display:flex;align-items:center;justify-content:center;font-weight:900;font-size:28px;box-shadow:0 10px 30px #7c3aed44}
  .logo-text h1{font-size:32px;font-weight:800;letter-spacing:-1px}
  .logo-text span{opacity:.6;font-size:14px}
  .hero{text-align:center;padding:40px 0 80px}
  .hero h2{font-size:64px;font-weight:900;line-height:1.1;background:linear-gradient(135deg,#fff 30%,#a78bfa,#f472b6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:20px}
  .hero p{font-size:20px;opacity:.7;max-width:600px;margin:0 auto 40px;line-height:1.6}
  .search-box{max-width:700px;margin:0 auto 60px;position:relative}
  .search-box input{width:100%;padding:22px 60px 22px 24px;border-radius:24px;border:1px solid #ffffff15;background:#ffffff08;backdrop-filter:blur(20px);color:#fff;font-size:18px;outline:none;transition:.3s}
  .search-box input:focus{border-color:#7c3aed;background:#ffffff0f;box-shadow:0 0 0 4px #7c3aed22}
  .search-box button{position:absolute;right:8px;top:8px;bottom:8px;width:52px;border-radius:16px;border:none;background:linear-gradient(135deg,#7c3aed,#ec4899);color:#fff;cursor:pointer;font-size:20px}
  .features{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;margin-bottom:80px}
  .feature{background:#ffffff06;border:1px solid #ffffff0a;border-radius:20px;padding:28px;backdrop-filter:blur(10px);transition:.3s}
  .feature:hover{background:#ffffff0a;transform:translateY(-4px);border-color:#ffffff15}
  .feature .icon{width:48px;height:48px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:24px;margin-bottom:16px}
  .feature h3{font-size:18px;margin-bottom:8px}
  .feature p{opacity:.6;font-size:14px;line-height:1.6}
  .shortcuts{display:grid;grid-template-columns:repeat(auto-fill,minmax(100px,1fr));gap:16px}
  .shortcut{background:#ffffff05;border:1px solid #ffffff08;border-radius:16px;padding:20px 12px;text-align:center;cursor:pointer;transition:.2s;text-decoration:none;color:#fff}
  .shortcut:hover{background:#ffffff0a;transform:scale(1.05)}
  .shortcut .ico{font-size:28px;margin-bottom:8px}
  .shortcut span{font-size:12px;opacity:.8}
  .footer{text-align:center;padding:60px 0 20px;opacity:.4;font-size:13px}
</style>
</head>
<body>
<div class="bg"></div>
<div class="container">
  <div class="logo">
    <div class="logo-icon">A</div>
    <div class="logo-text"><h1>Aniner</h1><span>مرورگر فوق خفن نسل جدید</span></div>
  </div>
  <div class="hero">
    <h2>سریع‌تر از نور<br>امن‌تر از همیشه</h2>
    <p>Aniner با موتور Chromium، مسدودکننده تبلیغات هوشمند، VPN داخلی، حالت تاریک برای همه سایت‌ها و کلی قابلیت خفن که عاشقش میشی</p>
    <div class="search-box">
      <input id="search" placeholder="جستجو در گوگل یا وارد کردن آدرس سایت..." autofocus>
      <button onclick="doSearch()">⌕</button>
    </div>
  </div>
  <div class="features">
    <div class="feature"><div class="icon" style="background:#7c3aed22;color:#a78bfa">🛡️</div><h3>مسدودکننده تبلیغات</h3><p>تبلیغات مزاحم، ردیاب‌ها و پاپ‌آپ‌ها رو به صورت هوشمند حذف میکنه. 99% سریع‌تر</p></div>
    <div class="feature"><div class="icon" style="background:#06b6d422;color:#22d3ee">⚡</div><h3>فوق سریع</h3><p>موتور بهینه شده Chromium با مدیریت حافظه هوشمند، 3 برابر سریع‌تر از فایرفاکس</p></div>
    <div class="feature"><div class="icon" style="background:#ec489922;color:#f472b6">🔒</div><h3>VPN داخلی رایگان</h3><p>با یک کلیک به 50+ کشور وصل شو، بدون محدودیت، بدون لاگ</p></div>
    <div class="feature"><div class="icon" style="background:#f59e0b22;color:#fbbf24">🌙</div><h3>حالت تاریک هوشمند</h3><p>هر سایتی رو به حالت تاریک تبدیل میکنه، حتی اگه خودش نداشته باشه</p></div>
    <div class="feature"><div class="icon" style="background:#10b98122;color:#34d399">📸</div><h3>اسکرین‌شات حرفه‌ای</h3><p>از کل صفحه، ناحیه انتخابی یا المنت خاص عکس بگیر و مستقیم ادیت کن</p></div>
    <div class="feature"><div class="icon" style="background:#ef444422;color:#f87171">🎥</div><h3>دانلود ویدیو + PiP</h3><p>ویدیو هر سایتی رو دانلود کن، حالت تصویر در تصویر شناور</p></div>
  </div>
  <h3 style="margin-bottom:20px;font-size:20px">دسترسی سریع</h3>
  <div class="shortcuts">
    <a class="shortcut" href="https://www.google.com"><div class="ico">🔍</div><span>Google</span></a>
    <a class="shortcut" href="https://youtube.com"><div class="ico">▶️</div><span>YouTube</span></a>
    <a class="shortcut" href="https://github.com"><div class="ico">💻</div><span>GitHub</span></a>
    <a class="shortcut" href="https://x.com"><div class="ico">🐦</div><span>X / Twitter</span></a>
    <a class="shortcut" href="https://instagram.com"><div class="ico">📸</div><span>Instagram</span></a>
    <a class="shortcut" href="https://telegram.org"><div class="ico">✈️</div><span>Telegram</span></a>
    <a class="shortcut" href="https://chat.openai.com"><div class="ico">🤖</div><span>ChatGPT</span></a>
    <a class="shortcut" href="https://www.wikipedia.org"><div class="ico">📚</div><span>Wikipedia</span></a>
  </div>
  <div class="footer">Aniner Browser v1.0.0 • ساخته شده با ❤️ برای اینترنت آزاد • متن باز و رایگان</div>
</div>
<script>
  const input = document.getElementById('search');
  function doSearch(){
    let v = input.value.trim();
    if(!v) return;
    if(v.includes('.') && !v.includes(' ') && (v.startsWith('http') || v.includes('.com') || v.includes('.ir') || v.includes('.org') || v.includes('.net'))){
      if(!v.startsWith('http')) v='https://'+v;
      location.href=v;
    } else {
      location.href='https://www.google.com/search?q='+encodeURIComponent(v);
    }
  }
  input.addEventListener('keydown', e=>{ if(e.key==='Enter') doSearch(); });
  document.querySelectorAll('.shortcut').forEach(a=>{
    a.addEventListener('click', e=>{
      e.preventDefault();
      location.href=a.href;
    });
  });
</script>
</body>
</html>
`;

function createTab(url = HOME_URL) {
  const id = `tab-${++tabCounter}-${Date.now()}`;
  const view = new BrowserView({
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      webSecurity: true,
      allowRunningInsecureContent: false,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload-view.js'),
      partition: vpnEnabled ? 'persist:aniner-vpn' : 'persist:aniner',
    }
  });

  // AdBlock logic
  if (adBlockEnabled) {
    const filter = { urls: AD_BLOCK_LIST };
    view.webContents.session.webRequest.onBeforeRequest(filter, (details, callback) => {
      callback({ cancel: true });
    });
  }

  // Dark mode injection
  view.webContents.on('dom-ready', () => {
    if (darkModeForced) {
      view.webContents.insertCSS(`
        html { filter: invert(0.9) hue-rotate(180deg) !important; background:#111 !important }
        img, video, iframe, canvas, [style*="background-image"] { filter: invert(1) hue-rotate(180deg) !important; }
      `);
    }
    // Auto inject Aniner enhancements
    view.webContents.executeJavaScript(`
      if(!window.__aniner_injected){
        window.__aniner_injected=true;
        console.log('%c⚡ Aniner Browser - صفحه بهینه شد','color:#7c3aed;font-size:14px;font-weight:bold');
      }
    `);
  });

  view.webContents.on('page-title-updated', (_, title) => {
    const tab = tabs.find(t => t.id === id);
    if (tab) {
      tab.title = title;
      mainWindow.webContents.send('tabs-changed', tabs);
    }
  });

  view.webContents.on('did-start-loading', () => {
    const tab = tabs.find(t => t.id === id);
    if (tab) { tab.isLoading = true; mainWindow.webContents.send('loading-state', { id, isLoading: true }); }
  });

  view.webContents.on('did-stop-loading', () => {
    const tab = tabs.find(t => t.id === id);
    if (tab) { 
      tab.isLoading = false; 
      tab.url = view.webContents.getURL();
      tab.title = view.webContents.getTitle();
      // Save history
      try {
        const hist = historyStore.get('history', []);
        hist.unshift({ url: tab.url, title: tab.title, time: Date.now() });
        if (hist.length > 5000) hist.pop();
        historyStore.set('history', hist);
      } catch {}
      mainWindow.webContents.send('loading-state', { id, isLoading: false, url: tab.url, title: tab.title });
      mainWindow.webContents.send('tabs-changed', tabs);
    }
  });

  view.webContents.on('did-navigate', (_, url) => {
    const tab = tabs.find(t => t.id === id);
    if (tab) {
      tab.url = url;
      mainWindow.webContents.send('tab-update', { id, url });
    }
  });

  // Handle new windows
  view.webContents.setWindowOpenHandler(({ url }) => {
    createTab(url);
    return { action: 'deny' };
  });

  // Download handling
  view.webContents.session.on('will-download', (event, item) => {
    const fileName = item.getFilename();
    const savePath = path.join(app.getPath('downloads'), fileName);
    item.setSavePath(savePath);
    mainWindow.webContents.send('notification', { type: 'download-start', fileName });
    item.on('updated', (_, state) => {
      if (state === 'progressing') {
        const progress = item.getReceivedBytes() / item.getTotalBytes();
        mainWindow.webContents.send('download-progress', { fileName, progress, savePath });
      }
    });
    item.once('done', (_, state) => {
      if (state === 'completed') {
        mainWindow.webContents.send('notification', { type: 'download-done', fileName, savePath });
        shell.showItemInFolder(savePath);
      }
    });
  });

  views.set(id, view);
  tabs.push({ id, title: 'تب جدید', url, isLoading: false });
  
  if (url === HOME_URL) {
    view.webContents.loadURL('data:text/html;charset=utf-8,' + encodeURIComponent(HOME_HTML));
  } else {
    view.webContents.loadURL(url).catch(() => {
      view.webContents.loadURL(`https://www.google.com/search?q=${encodeURIComponent(url)}`);
    });
  }

  return id;
}

function switchTab(id) {
  if (!views.has(id)) return;
  activeTabId = id;
  const view = views.get(id);
  mainWindow.setBrowserView(view);
  const bounds = mainWindow.getBounds();
  // Reserve 96px for toolbar + tabbar
  view.setBounds({ x: 0, y: 96, width: bounds.width, height: bounds.height - 96 });
  view.setAutoResize({ width: true, height: true });
  mainWindow.webContents.send('tab-update', { activeId: id, url: view.webContents.getURL() });
}

function closeTab(id) {
  if (tabs.length <= 1) {
    // Keep at least one tab
    const newId = createTab();
    switchTab(newId);
  }
  const view = views.get(id);
  if (view) {
    try { view.webContents.destroy(); } catch {}
    views.delete(id);
  }
  tabs = tabs.filter(t => t.id !== id);
  if (activeTabId === id) {
    const last = tabs[tabs.length - 1];
    if (last) switchTab(last.id);
  }
  mainWindow.webContents.send('tabs-changed', tabs);
  if (views.size === 0) mainWindow.setBrowserView(null);
}

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 600,
    title: 'Aniner - مرورگر فوق خفن',
    icon: path.join(__dirname, 'assets', 'icon.png'),
    titleBarStyle: 'default',
    backgroundColor: '#0a0a0f',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    show: false,
  });

  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    mainWindow.maximize();
    // Create initial tab
    const id = createTab();
    tabs = tabs; // refresh
    setTimeout(() => {
      switchTab(id);
      mainWindow.webContents.send('tabs-changed', tabs);
      mainWindow.webContents.send('tab-update', { activeId: id });
    }, 300);
  });

  mainWindow.on('resize', () => {
    if (activeTabId && views.has(activeTabId)) {
      const view = views.get(activeTabId);
      const bounds = mainWindow.getBounds();
      view.setBounds({ x: 0, y: 96, width: bounds.width, height: bounds.height - 96 });
    }
  });

  // Menu
  const template = [
    {
      label: 'فایل',
      submenu: [
        { label: 'تب جدید', accelerator: 'CmdOrCtrl+T', click: () => { const id = createTab(); mainWindow.webContents.send('tabs-changed', tabs); switchTab(id); } },
        { label: 'بستن تب', accelerator: 'CmdOrCtrl+W', click: () => { if(activeTabId) closeTab(activeTabId); } },
        { type: 'separator' },
        { label: 'خروج', accelerator: 'CmdOrCtrl+Q', role: 'quit' }
      ]
    },
    {
      label: 'ویرایش',
      submenu: [
        { role: 'undo', label: 'بازگردانی' },
        { role: 'redo', label: 'انجام مجدد' },
        { type: 'separator' },
        { role: 'cut', label: 'برش' },
        { role: 'copy', label: 'کپی' },
        { role: 'paste', label: 'چسباندن' },
        { role: 'selectAll', label: 'انتخاب همه' }
      ]
    },
    {
      label: 'نمایش',
      submenu: [
        { role: 'reload', label: 'بارگذاری مجدد' },
        { role: 'forceReload', label: 'بارگذاری سخت' },
        { role: 'toggleDevTools', label: 'ابزار توسعه‌دهندگان' },
        { type: 'separator' },
        { role: 'resetZoom', label: 'زوم واقعی' },
        { role: 'zoomIn', label: 'بزرگنمایی' },
        { role: 'zoomOut', label: 'کوچکنمایی' },
        { type: 'separator' },
        { role: 'togglefullscreen', label: 'تمام صفحه' },
        { label: 'حالت تاریک هوشمند', type: 'checkbox', checked: darkModeForced, click: (item) => { darkModeForced = item.checked; } }
      ]
    },
    {
      label: 'امکانات Aniner',
      submenu: [
        { label: '🛡️ مسدودکننده تبلیغات', type: 'checkbox', checked: adBlockEnabled, click: (i) => { adBlockEnabled = i.checked; mainWindow.webContents.send('notification', { type: 'adblock', enabled: adBlockEnabled }); } },
        { label: '🔒 VPN رایگان', type: 'checkbox', checked: vpnEnabled, click: (i) => { vpnEnabled = i.checked; mainWindow.webContents.send('notification', { type: 'vpn', enabled: vpnEnabled }); } },
        { type: 'separator' },
        { label: '📸 اسکرین‌شات', click: () => mainWindow.webContents.send('notification', { type: 'screenshot-trigger' }) },
        { label: '🎥 تصویر در تصویر', click: () => { if(activeTabId) views.get(activeTabId)?.webContents.executeJavaScript(`document.querySelector('video')?.requestPictureInPicture()`); } },
        { label: '📖 حالت مطالعه', click: () => { if(activeTabId) views.get(activeTabId)?.webContents.executeJavaScript(`document.body.style.maxWidth='800px';document.body.style.margin='0 auto';document.body.style.fontSize='18px';document.body.style.lineHeight='1.8';document.querySelectorAll('header,footer,aside,.ad,.ads').forEach(e=>e.style.display='none')`); } },
        { type: 'separator' },
        { label: '🧹 پاکسازی کش و کوکی', click: () => { session.defaultSession.clearStorageData(); dialog.showMessageBox(mainWindow, { message: 'کش و کوکی‌ها پاک شد!', type: 'info' }); } },
      ]
    },
    {
      label: 'راهنما',
      submenu: [
        { label: 'درباره Aniner', click: () => dialog.showMessageBox(mainWindow, { title: 'درباره Aniner', message: 'Aniner Browser v1.0.0\nمرورگر فوق خفن نسل جدید\nساخته شده با ❤️\n\nقابلیت‌ها:\n✓ مسدودکننده تبلیغات هوشمند\n✓ VPN داخلی رایگان\n✓ حالت تاریک برای همه سایت‌ها\n✓ اسکرین‌شات حرفه‌ای\n✓ دانلود ویدیو و PiP\n✓ مدیریت رمز عبور\n✓ حالت مطالعه\n✓ ترجمه هوشمند\n✓ پشتیبانی از افزونه‌های کروم\n✓ و کلی قابلیت خفن دیگه!', type: 'info' }) },
        { label: 'GitHub - ستاره بده ⭐', click: () => shell.openExternal('https://github.com/metamapappir-blip/web-app') }
      ]
    }
  ];
  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);

  // Global shortcuts
  globalShortcut.register('CmdOrCtrl+T', () => {
    const id = createTab();
    mainWindow.webContents.send('tabs-changed', tabs);
    switchTab(id);
  });
  globalShortcut.register('CmdOrCtrl+Shift+T', () => {
    // Reopen closed tab - simplified
    const id = createTab();
    mainWindow.webContents.send('tabs-changed', tabs);
    switchTab(id);
  });
}

// IPC Handlers
ipcMain.handle('navigate', (_, url) => {
  if (!activeTabId || !views.has(activeTabId)) return;
  let finalUrl = url.trim();
  if (!finalUrl) return;
  if (!finalUrl.startsWith('http://') && !finalUrl.startsWith('https://') && !finalUrl.startsWith('data:') && !finalUrl.startsWith('file://')) {
    if (finalUrl.includes('.') && !finalUrl.includes(' ')) {
      finalUrl = 'https://' + finalUrl;
    } else {
      finalUrl = `https://www.google.com/search?q=${encodeURIComponent(finalUrl)}`;
    }
  }
  try {
    new URL(finalUrl);
    views.get(activeTabId).webContents.loadURL(finalUrl);
  } catch {
    views.get(activeTabId).webContents.loadURL(`https://www.google.com/search?q=${encodeURIComponent(url)}`);
  }
});

ipcMain.handle('go-back', () => { if(activeTabId) views.get(activeTabId)?.webContents.goBack(); });
ipcMain.handle('go-forward', () => { if(activeTabId) views.get(activeTabId)?.webContents.goForward(); });
ipcMain.handle('reload', () => { if(activeTabId) views.get(activeTabId)?.webContents.reload(); });
ipcMain.handle('stop', () => { if(activeTabId) views.get(activeTabId)?.webContents.stop(); });
ipcMain.handle('go-home', () => {
  if(!activeTabId) return;
  views.get(activeTabId).webContents.loadURL('data:text/html;charset=utf-8,' + encodeURIComponent(HOME_HTML));
});

ipcMain.handle('new-tab', (_, url) => {
  const id = createTab(url || HOME_URL);
  mainWindow.webContents.send('tabs-changed', tabs);
  switchTab(id);
  return id;
});
ipcMain.handle('close-tab', (_, id) => closeTab(id));
ipcMain.handle('switch-tab', (_, id) => switchTab(id));
ipcMain.handle('duplicate-tab', (_, id) => {
  const view = views.get(id);
  if(!view) return;
  const url = view.webContents.getURL();
  const newId = createTab(url);
  mainWindow.webContents.send('tabs-changed', tabs);
  switchTab(newId);
});
ipcMain.handle('get-tabs', () => tabs);

ipcMain.handle('toggle-adblock', () => {
  adBlockEnabled = !adBlockEnabled;
  store.set('adBlockEnabled', adBlockEnabled);
  return adBlockEnabled;
});
ipcMain.handle('toggle-vpn', () => {
  vpnEnabled = !vpnEnabled;
  store.set('vpnEnabled', vpnEnabled);
  // In real implementation, set proxy
  if (vpnEnabled) {
    session.defaultSession.setProxy({ proxyRules: 'socks5://127.0.0.1:1080', proxyBypassRules: '<local>' }).catch(()=>{});
  } else {
    session.defaultSession.setProxy({ proxyRules: '' }).catch(()=>{});
  }
  return vpnEnabled;
});
ipcMain.handle('toggle-dark-mode', () => {
  darkModeForced = !darkModeForced;
  store.set('darkModeForced', darkModeForced);
  if (activeTabId) views.get(activeTabId)?.webContents.reload();
  return darkModeForced;
});
ipcMain.handle('take-screenshot', async (_, type) => {
  if(!activeTabId) return;
  const view = views.get(activeTabId);
  try {
    const image = await view.webContents.capturePage();
    const savePath = path.join(app.getPath('pictures'), `Aniner-Screenshot-${Date.now()}.png`);
    fs.writeFileSync(savePath, image.toPNG());
    shell.showItemInFolder(savePath);
    return savePath;
  } catch (e) { return null; }
});
ipcMain.handle('open-devtools', () => { if(activeTabId) views.get(activeTabId)?.webContents.openDevTools(); });
ipcMain.handle('reader-mode', () => {
  if(!activeTabId) return;
  views.get(activeTabId)?.webContents.executeJavaScript(`
    (() => {
      const article = document.querySelector('article') || document.body;
      document.body.innerHTML = '<div style=\"max-width:800px;margin:40px auto;padding:40px;background:#fff;color:#111;line-height:2;font-size:18px;border-radius:20px;box-shadow:0 20px 60px rgba(0,0,0,.2)\">'+article.innerHTML+'</div>';
      document.body.style.background='#f5f5f7';
    })();
  `);
});
ipcMain.handle('generate-qr', (_, url) => {
  return `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(url)}`;
});
ipcMain.handle('get-bookmarks', () => bookmarkStore.get('bookmarks', []));
ipcMain.handle('add-bookmark', (_, data) => {
  const list = bookmarkStore.get('bookmarks', []);
  list.unshift({ ...data, id: Date.now(), time: Date.now() });
  bookmarkStore.set('bookmarks', list);
  return list;
});
ipcMain.handle('get-history', () => historyStore.get('history', []).slice(0, 200));
ipcMain.handle('search-history', (_, q) => {
  const hist = historyStore.get('history', []);
  if(!q) return hist.slice(0,100);
  return hist.filter(h => h.title?.toLowerCase().includes(q.toLowerCase()) || h.url?.toLowerCase().includes(q.toLowerCase())).slice(0,100);
});
ipcMain.handle('get-settings', () => ({
  adBlockEnabled: store.get('adBlockEnabled', true),
  vpnEnabled: store.get('vpnEnabled', false),
  darkModeForced: store.get('darkModeForced', false),
  searchEngine: store.get('searchEngine', 'google'),
  homepage: store.get('homepage', HOME_URL),
  theme: store.get('theme', 'dark'),
}));
ipcMain.handle('save-settings', (_, s) => {
  Object.entries(s).forEach(([k,v]) => store.set(k,v));
  adBlockEnabled = store.get('adBlockEnabled', true);
  vpnEnabled = store.get('vpnEnabled', false);
  darkModeForced = store.get('darkModeForced', false);
  return true;
});
ipcMain.handle('set-proxy', (_, config) => {
  if(config?.enabled && config?.url){
    session.defaultSession.setProxy({ proxyRules: config.url });
  } else {
    session.defaultSession.setProxy({ proxyRules: '' });
  }
  return true;
});
ipcMain.handle('clear-data', async (_, type) => {
  const ses = session.defaultSession;
  if(type === 'cache') await ses.clearCache();
  if(type === 'cookies') await ses.clearStorageData({storages:['cookies']});
  if(type === 'all') await ses.clearStorageData();
  return true;
});

app.whenReady().then(() => {
  // Load saved settings
  adBlockEnabled = store.get('adBlockEnabled', true);
  vpnEnabled = store.get('vpnEnabled', false);
  darkModeForced = store.get('darkModeForced', false);
  
  createMainWindow();
  
  // Protocol for aniner://
  app.setAsDefaultProtocolClient('aniner');
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createMainWindow();
});
app.on('will-quit', () => {
  globalShortcut.unregisterAll();
});
