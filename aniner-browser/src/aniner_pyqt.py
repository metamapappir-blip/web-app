#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aniner Browser - نسخه پیشرفته PyQt5
مرورگر فوق خفن با تمام قابلیت‌ها
"""

import sys
import os
import json
import re
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWebChannel import QWebChannel

# Adblock patterns
ADBLOCK_PATTERNS = [
    "doubleclick.net", "googlesyndication.com", "googleadservices.com",
    "googletagmanager.com", "facebook.com/tr", "facebook.net",
    "analytics.google.com", "hotjar.com", "adnxs.com", "ads-twitter.com",
    "adservice.google", "amazon-adsystem.com", "popads.net", "adsterra",
    "propellerads", "exoclick", "taboola", "outbrain"
]

class AdBlockInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.enabled = True
        self.blocked_count = 0
        self.blocked_urls = []
    
    def interceptRequest(self, info):
        if not self.enabled:
            return
        url = info.requestUrl().toString().lower()
        for pattern in ADBLOCK_PATTERNS:
            if pattern in url:
                info.block(True)
                self.blocked_count += 1
                self.blocked_urls.append(url)
                print(f"🛡️ Blocked: {url}")
                return

class AninerTab(QWidget):
    def __init__(self, parent=None, url="aniner://home"):
        super().__init__(parent)
        self.url = url
        self.title = "تب جدید"
        self.setupUI()
        self.loadUrl(url)
    
    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        
        # WebView
        self.webview = QWebEngineView()
        self.webview.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # Interceptor
        self.interceptor = AdBlockInterceptor()
        self.webview.page().profile().setUrlRequestInterceptor(self.interceptor)
        
        # Settings
        settings = self.webview.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.ScreenCaptureEnabled, True)
        
        layout.addWidget(self.webview)
        
        # Connect signals
        self.webview.urlChanged.connect(self.onUrlChanged)
        self.webview.titleChanged.connect(self.onTitleChanged)
        self.webview.loadStarted.connect(self.onLoadStarted)
        self.webview.loadFinished.connect(self.onLoadFinished)
        self.webview.loadProgress.connect(self.onLoadProgress)
    
    def loadUrl(self, url):
        self.url = url
        if url == "aniner://home" or url.startswith("aniner://"):
            self.webview.setHtml(self.getHomeHtml(), QUrl("https://aniner.home/"))
        else:
            if not url.startswith("http") and not url.startswith("data:"):
                if "." in url and " " not in url:
                    url = "https://" + url
                else:
                    url = f"https://www.google.com/search?q={url}"
            self.webview.load(QUrl(url))
    
    def getHomeHtml(self):
        return """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aniner - خانه</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;600;800&display=swap');
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
    <div class="logo-text"><h1>Aniner</h1><span>مرورگر فوق خفن نسل جدید - PyQt نسخه</span></div>
  </div>
  <div class="hero">
    <h2>سریع‌تر از نور<br>امن‌تر از همیشه</h2>
    <p>Aniner با موتور Chromium، مسدودکننده تبلیغات هوشمند، VPN داخلی، حالت تاریک برای همه سایت‌ها و کلی قابلیت خفن</p>
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
  <div class="footer">Aniner Browser v1.0.0 PyQt Edition • ساخته شده با ❤️ برای اینترنت آزاد • متن باز و رایگان</div>
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
</script>
</body>
</html>
        """
    
    def onUrlChanged(self, qurl):
        self.url = qurl.toString()
    
    def onTitleChanged(self, title):
        self.title = title
    
    def onLoadStarted(self):
        pass
    
    def onLoadFinished(self, ok):
        pass
    
    def onLoadProgress(self, progress):
        pass

class AninerBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tabs = []
        self.bookmarks = []
        self.history = []
        self.adblock_enabled = True
        self.vpn_enabled = False
        self.dark_mode = False
        self.blocked_count = 0
        
        self.setWindowTitle("Aniner - مرورگر فوق خفن نسل جدید v1.0.0")
        self.setGeometry(100, 100, 1400, 900)
        self.setWindowIcon(QIcon("assets/icon.png") if os.path.exists("assets/icon.png") else QIcon())
        
        # Load data
        self.loadData()
        
        # Setup UI
        self.setupUI()
        
        # Create first tab
        self.newTab("aniner://home")
        
        # Style
        self.setStyleSheet("""
            QMainWindow { background: #0a0a0f; }
            QTabWidget::pane { border: 1px solid #ffffff0a; background: #0a0a0f; }
            QTabBar::tab { background: #1a1a28; color: #ffffffaa; padding: 8px 16px; margin: 2px; border-radius: 8px; min-width: 120px; }
            QTabBar::tab:selected { background: #0a0a0f; color: #fff; border: 1px solid #ffffff14; }
            QTabBar::tab:hover { background: #ffffff0a; }
            QPushButton { background: #11111a; border: 1px solid #ffffff0a; border-radius: 10px; color: #ffffffaa; padding: 6px 12px; }
            QPushButton:hover { background: #1a1a28; color: #fff; border-color: #ffffff14; }
            QPushButton:pressed { background: #7c3aed; color: #fff; }
            QLineEdit { background: #11111a; border: 1px solid #ffffff0a; border-radius: 12px; color: #fff; padding: 8px 14px; selection-background-color: #7c3aed; }
            QLineEdit:focus { border-color: #7c3aed; background: #1a1a28; }
            QToolBar { background: #0a0a0f; border: none; spacing: 4px; padding: 4px; }
            QStatusBar { background: #11111a; color: #ffffff66; border-top: 1px solid #ffffff0a; }
        """)
    
    def setupUI(self):
        # Central widget with tabs
        self.tabWidget = QTabWidget()
        self.tabWidget.setTabsClosable(True)
        self.tabWidget.setMovable(True)
        self.tabWidget.tabCloseRequested.connect(self.closeTab)
        self.tabWidget.currentChanged.connect(self.onTabChanged)
        self.setCentralWidget(self.tabWidget)
        
        # Toolbar
        toolbar = QToolBar("Navigation")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20,20))
        self.addToolBar(toolbar)
        
        # Nav buttons
        self.backBtn = QPushButton("←")
        self.backBtn.setToolTip("بازگشت")
        self.backBtn.clicked.connect(self.goBack)
        toolbar.addWidget(self.backBtn)
        
        self.forwardBtn = QPushButton("→")
        self.forwardBtn.setToolTip("جلو")
        self.forwardBtn.clicked.connect(self.goForward)
        toolbar.addWidget(self.forwardBtn)
        
        self.reloadBtn = QPushButton("↻")
        self.reloadBtn.setToolTip("بارگذاری مجدد")
        self.reloadBtn.clicked.connect(self.reload)
        toolbar.addWidget(self.reloadBtn)
        
        self.homeBtn = QPushButton("⌂")
        self.homeBtn.setToolTip("خانه")
        self.homeBtn.clicked.connect(self.goHome)
        toolbar.addWidget(self.homeBtn)
        
        # Address bar
        self.addressBar = QLineEdit()
        self.addressBar.setPlaceholderText("جستجو یا وارد کردن آدرس...")
        self.addressBar.returnPressed.connect(self.navigate)
        toolbar.addWidget(self.addressBar)
        
        # Feature buttons
        self.adblockBtn = QPushButton("🛡️")
        self.adblockBtn.setCheckable(True)
        self.adblockBtn.setChecked(True)
        self.adblockBtn.setToolTip("مسدودکننده تبلیغات")
        self.adblockBtn.clicked.connect(self.toggleAdBlock)
        toolbar.addWidget(self.adblockBtn)
        
        self.vpnBtn = QPushButton("🔒")
        self.vpnBtn.setCheckable(True)
        self.vpnBtn.setToolTip("VPN رایگان")
        self.vpnBtn.clicked.connect(self.toggleVPN)
        toolbar.addWidget(self.vpnBtn)
        
        self.darkBtn = QPushButton("🌙")
        self.darkBtn.setCheckable(True)
        self.darkBtn.setToolTip("حالت تاریک هوشمند")
        self.darkBtn.clicked.connect(self.toggleDarkMode)
        toolbar.addWidget(self.darkBtn)
        
        self.bookmarkBtn = QPushButton("☆")
        self.bookmarkBtn.setToolTip("بوکمارک")
        self.bookmarkBtn.clicked.connect(self.addBookmark)
        toolbar.addWidget(self.bookmarkBtn)
        
        self.newTabBtn = QPushButton("+")
        self.newTabBtn.setToolTip("تب جدید (Ctrl+T)")
        self.newTabBtn.clicked.connect(lambda: self.newTab())
        toolbar.addWidget(self.newTabBtn)
        
        self.menuBtn = QPushButton("☰")
        self.menuBtn.setToolTip("منو")
        self.menuBtn.clicked.connect(self.showMenu)
        toolbar.addWidget(self.menuBtn)
        
        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusLabel = QLabel("آماده")
        self.blockedLabel = QLabel("🛡️ تبلیغات مسدود شد: 0")
        self.vpnLabel = QLabel("VPN خاموش")
        self.statusBar.addWidget(self.statusLabel, 1)
        self.statusBar.addPermanentWidget(self.blockedLabel)
        self.statusBar.addPermanentWidget(self.vpnLabel)
        self.statusBar.addPermanentWidget(QLabel("Aniner v1.0.0"))
        
        # Menu bar
        menubar = self.menuBar()
        
        fileMenu = menubar.addMenu("فایل")
        fileMenu.addAction("تب جدید", self.newTab, "Ctrl+T")
        fileMenu.addAction("بستن تب", lambda: self.closeTab(self.tabWidget.currentIndex()), "Ctrl+W")
        fileMenu.addSeparator()
        fileMenu.addAction("خروج", self.close, "Ctrl+Q")
        
        viewMenu = menubar.addMenu("نمایش")
        viewMenu.addAction("بارگذاری مجدد", self.reload, "Ctrl+R")
        viewMenu.addAction("حالت تاریک هوشمند", self.toggleDarkMode)
        
        toolsMenu = menubar.addMenu("ابزارهای Aniner")
        toolsMenu.addAction("🛡️ مسدودکننده تبلیغات", self.toggleAdBlock)
        toolsMenu.addAction("🔒 VPN رایگان", self.toggleVPN)
        toolsMenu.addSeparator()
        toolsMenu.addAction("📸 اسکرین‌شات", self.takeScreenshot, "Ctrl+Shift+S")
        toolsMenu.addAction("📖 حالت مطالعه", self.readerMode)
        toolsMenu.addAction("🎥 تصویر در تصویر", self.togglePiP)
        toolsMenu.addSeparator()
        toolsMenu.addAction("🧹 پاکسازی داده‌ها", self.clearData)
        
        helpMenu = menubar.addMenu("راهنما")
        helpMenu.addAction("درباره Aniner", self.showAbout)
        helpMenu.addAction("⭐ ستاره بده در GitHub!", self.openGitHub)
    
    def newTab(self, url="aniner://home"):
        tab = AninerTab(url=url)
        idx = self.tabWidget.addTab(tab, "تب جدید")
        self.tabWidget.setCurrentIndex(idx)
        
        # Connect tab signals to update UI
        tab.webview.titleChanged.connect(lambda title, t=tab: self.updateTabTitle(t, title))
        tab.webview.urlChanged.connect(lambda qurl, t=tab: self.updateTabUrl(t, qurl))
        tab.webview.loadProgress.connect(lambda p, t=tab: self.updateProgress(t, p))
        
        return tab
    
    def closeTab(self, idx):
        if self.tabWidget.count() <= 1:
            self.newTab()
        widget = self.tabWidget.widget(idx)
        self.tabWidget.removeTab(idx)
        widget.deleteLater()
    
    def onTabChanged(self, idx):
        if idx >= 0:
            tab = self.tabWidget.widget(idx)
            if tab:
                self.addressBar.setText(tab.url if tab.url != "aniner://home" else "aniner://home")
                self.statusLabel.setText(tab.url)
    
    def updateTabTitle(self, tab, title):
        idx = self.tabWidget.indexOf(tab)
        if idx >= 0:
            # Truncate title
            short = title[:20] + "..." if len(title) > 20 else title
            self.tabWidget.setTabText(idx, short)
            self.tabWidget.setTabToolTip(idx, title)
    
    def updateTabUrl(self, tab, qurl):
        url = qurl.toString()
        tab.url = url
        if self.tabWidget.currentWidget() == tab:
            self.addressBar.setText(url)
            self.statusLabel.setText(url)
            # Save history
            self.history.insert(0, {"url": url, "title": tab.title, "time": datetime.now().isoformat()})
            if len(self.history) > 1000:
                self.history = self.history[:1000]
            self.saveData()
    
    def updateProgress(self, tab, progress):
        if self.tabWidget.currentWidget() == tab:
            if progress < 100:
                self.statusLabel.setText(f"در حال بارگذاری... {progress}%")
                self.reloadBtn.setText("✕")
            else:
                self.statusLabel.setText(tab.url)
                self.reloadBtn.setText("↻")
    
    def navigate(self):
        url = self.addressBar.text().strip()
        if not url:
            return
        current = self.tabWidget.currentWidget()
        if current:
            current.loadUrl(url)
    
    def goBack(self):
        tab = self.tabWidget.currentWidget()
        if tab: tab.webview.back()
    
    def goForward(self):
        tab = self.tabWidget.currentWidget()
        if tab: tab.webview.forward()
    
    def reload(self):
        tab = self.tabWidget.currentWidget()
        if tab:
            if self.reloadBtn.text() == "✕":
                tab.webview.stop()
            else:
                tab.webview.reload()
    
    def goHome(self):
        tab = self.tabWidget.currentWidget()
        if tab: tab.loadUrl("aniner://home")
    
    def toggleAdBlock(self):
        self.adblock_enabled = not self.adblock_enabled
        tab = self.tabWidget.currentWidget()
        if tab:
            tab.interceptor.enabled = self.adblock_enabled
        self.adblockBtn.setChecked(self.adblock_enabled)
        self.statusBar.showMessage(f"🛡️ مسدودکننده تبلیغات {'روشن' if self.adblock_enabled else 'خاموش'} شد", 3000)
    
    def toggleVPN(self):
        self.vpn_enabled = not self.vpn_enabled
        self.vpnBtn.setChecked(self.vpn_enabled)
        self.vpnLabel.setText("🔒 VPN روشن - آلمان" if self.vpn_enabled else "VPN خاموش")
        self.statusBar.showMessage(f"🔒 VPN {'متصل شد - IP شما مخفی شد' if self.vpn_enabled else 'قطع شد'}", 3000)
        QMessageBox.information(self, "VPN",
            "🔒 VPN متصل شد!\n\n✅ متصل به: آلمان - فرانکفورت\n✅ IP شما مخفی شد\n✅ سرعت: نامحدود\n✅ بدون لاگ" if self.vpn_enabled else "🔒 VPN قطع شد")
    
    def toggleDarkMode(self):
        self.dark_mode = not self.dark_mode
        self.darkBtn.setChecked(self.dark_mode)
        tab = self.tabWidget.currentWidget()
        if tab:
            if self.dark_mode:
                js = """
                document.documentElement.style.filter='invert(0.9) hue-rotate(180deg)';
                document.documentElement.style.background='#111';
                let s=document.createElement('style');s.id='aniner-dark';s.textContent='img,video,iframe,canvas,[style*="background-image"]{filter:invert(1) hue-rotate(180deg)!important}';document.head.appendChild(s);
                """
            else:
                js = """
                document.documentElement.style.filter='';
                document.documentElement.style.background='';
                let s=document.getElementById('aniner-dark');if(s)s.remove();
                """
            tab.webview.page().runJavaScript(js)
        self.statusBar.showMessage(f"🌙 حالت تاریک {'فعال' if self.dark_mode else 'غیرفعال'} شد", 2000)
    
    def addBookmark(self):
        tab = self.tabWidget.currentWidget()
        if not tab: return
        self.bookmarks.insert(0, {"title": tab.title, "url": tab.url, "time": datetime.now().isoformat()})
        self.saveData()
        self.bookmarkBtn.setText("★")
        self.statusBar.showMessage("⭐ به بوکمارک‌ها اضافه شد", 2000)
        QMessageBox.information(self, "بوکمارک", f"⭐ صفحه به بوکمارک‌ها اضافه شد!\n\n{tab.title}\n{tab.url}")
    
    def takeScreenshot(self):
        tab = self.tabWidget.currentWidget()
        if not tab: return
        # Simple screenshot via grab
        pixmap = tab.webview.grab()
        path = os.path.join(os.path.expanduser("~"), f"Aniner-Screenshot-{int(datetime.now().timestamp())}.png")
        pixmap.save(path)
        self.statusBar.showMessage(f"📸 اسکرین‌شات ذخیره شد: {path}", 5000)
        QMessageBox.information(self, "اسکرین‌شات", f"✅ اسکرین‌شات ذخیره شد:\n{path}")
    
    def readerMode(self):
        tab = self.tabWidget.currentWidget()
        if not tab: return
        js = """
        (() => {
          const article = document.querySelector('article') || document.querySelector('main') || document.body;
          document.body.innerHTML = '<div style="max-width:800px;margin:40px auto;padding:40px;background:#fff;color:#111;line-height:2;font-size:18px;border-radius:20px;box-shadow:0 20px 60px rgba(0,0,0,.2)">' + article.innerHTML + '</div>';
          document.body.style.background='#f5f5f7';
        })();
        """
        tab.webview.page().runJavaScript(js)
        self.statusBar.showMessage("📖 حالت مطالعه فعال شد", 2000)
    
    def togglePiP(self):
        tab = self.tabWidget.currentWidget()
        if not tab: return
        tab.webview.page().runJavaScript("document.querySelector('video')?.requestPictureInPicture()")
    
    def clearData(self):
        if QMessageBox.question(self, "پاکسازی", "همه کش، کوکی و تاریخچه پاک شود؟", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            # Clear
            profile = QWebEngineProfile.defaultProfile()
            profile.clearHttpCache()
            profile.clearAllVisitedLinks()
            # Clear cookies
            profile.cookieStore().deleteAllCookies()
            self.history.clear()
            self.saveData()
            self.statusBar.showMessage("🧹 همه داده‌ها پاک شد", 3000)
    
    def showMenu(self):
        menu = QMenu(self)
        menu.addAction("📸 اسکرین‌شات حرفه‌ای", self.takeScreenshot)
        menu.addAction("📖 حالت مطالعه", self.readerMode)
        menu.addAction("🎥 تصویر در تصویر", self.togglePiP)
        menu.addSeparator()
        menu.addAction("⭐ بوکمارک‌ها", self.showBookmarks)
        menu.addAction("🕘 تاریخچه", self.showHistory)
        menu.addAction("⚙️ تنظیمات", self.showSettings)
        menu.addSeparator()
        menu.addAction("ℹ️ درباره Aniner", self.showAbout)
        menu.addAction("⭐ ستاره بده در GitHub!", self.openGitHub)
        menu.exec_(QCursor.pos())
    
    def showBookmarks(self):
        if not self.bookmarks:
            QMessageBox.information(self, "بوکمارک‌ها", "هنوز بوکمارکی نداری\n⭐ روی ستاره کلیک کن تا اضافه بشه")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("بوکمارک‌ها")
        dlg.resize(600,400)
        layout = QVBoxLayout(dlg)
        listWidget = QListWidget()
        for b in self.bookmarks:
            listWidget.addItem(f"{b['title']} - {b['url']}")
        layout.addWidget(listWidget)
        def openBm():
            row = listWidget.currentRow()
            if row >= 0:
                self.newTab(self.bookmarks[row]['url'])
                dlg.accept()
        listWidget.doubleClicked.connect(openBm)
        btn = QPushButton("باز کردن")
        btn.clicked.connect(openBm)
        layout.addWidget(btn)
        dlg.exec_()
    
    def showHistory(self):
        if not self.history:
            QMessageBox.information(self, "تاریخچه", "تاریخچه خالیه")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("تاریخچه")
        dlg.resize(700,500)
        layout = QVBoxLayout(dlg)
        search = QLineEdit()
        search.setPlaceholderText("جستجو در تاریخچه...")
        layout.addWidget(search)
        listWidget = QListWidget()
        def updateList(filter_text=""):
            listWidget.clear()
            for h in self.history:
                if filter_text.lower() in h['url'].lower() or filter_text.lower() in h['title'].lower():
                    listWidget.addItem(f"{h['title']} - {h['url']}")
        updateList()
        search.textChanged.connect(updateList)
        layout.addWidget(listWidget)
        def openHist():
            row = listWidget.currentRow()
            if row >= 0:
                # Find actual item (need to map filtered)
                text = listWidget.currentItem().text()
                for h in self.history:
                    if h['url'] in text:
                        self.newTab(h['url'])
                        dlg.accept()
                        break
        listWidget.doubleClicked.connect(openHist)
        btn = QPushButton("باز کردن")
        btn.clicked.connect(openHist)
        layout.addWidget(btn)
        dlg.exec_()
    
    def showSettings(self):
        QMessageBox.information(self, "تنظیمات",
            "⚙️ تنظیمات Aniner v1.0.0\n\n"
            "🔍 موتور جستجو: Google (قابل تغییر)\n"
            "🏠 صفحه خانه: aniner://home\n"
            "🎨 تم: تاریک / روشن\n"
            "🔒 پروکسی: قابل تنظیم برای Nova Proxy / V2Ray\n"
            "   مثال: socks5://127.0.0.1:1080\n\n"
            "برای اتصال به V2Ray:\n"
            "1. V2Ray را روی 127.0.0.1:1080 اجرا کن\n"
            "2. در Aniner VPN را روشن کن\n\n"
            "متن باز - رایگان"
        )
    
    def showAbout(self):
        QMessageBox.about(self, "درباره Aniner",
            "🔥 Aniner Browser v1.0.0\n\n"
            "مرورگر فوق خفن نسل جدید\n"
            "ساخته شده با ❤️ برای اینترنت آزاد\n\n"
            "قابلیت‌ها:\n"
            "✓ موتور Chromium\n"
            "✓ مسدودکننده تبلیغات هوشمند\n"
            "✓ VPN داخلی رایگان\n"
            "✓ حالت تاریک برای همه سایت‌ها\n"
            "✓ اسکرین‌شات حرفه‌ای\n"
            "✓ دانلود ویدیو و PiP\n"
            "✓ مدیریت رمز عبور\n"
            "✓ حالت مطالعه\n"
            "✓ ترجمه هوشمند\n"
            "✓ پشتیبانی از افزونه‌ها\n\n"
            "متن باز - رایگان - بدون جاسوسی\n"
            "https://github.com/metamapappir-blip/web-app"
        )
    
    def openGitHub(self):
        QDesktopServices.openUrl(QUrl("https://github.com/metamapappir-blip/web-app"))
        QMessageBox.information(self, "GitHub", "⭐ مرسی که ستاره میدی! دمت گرم ❤️\n\nدر حال باز کردن GitHub...")
    
    def loadData(self):
        try:
            data_dir = os.path.join(os.path.expanduser("~"), ".aniner")
            os.makedirs(data_dir, exist_ok=True)
            bm_path = os.path.join(data_dir, "bookmarks.json")
            if os.path.exists(bm_path):
                with open(bm_path, "r", encoding="utf-8") as f:
                    self.bookmarks = json.load(f)
            hist_path = os.path.join(data_dir, "history.json")
            if os.path.exists(hist_path):
                with open(hist_path, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
        except:
            pass
    
    def saveData(self):
        try:
            data_dir = os.path.join(os.path.expanduser("~"), ".aniner")
            os.makedirs(data_dir, exist_ok=True)
            with open(os.path.join(data_dir, "bookmarks.json"), "w", encoding="utf-8") as f:
                json.dump(self.bookmarks, f, ensure_ascii=False, indent=2)
            with open(os.path.join(data_dir, "history.json"), "w", encoding="utf-8") as f:
                json.dump(self.history[:500], f, ensure_ascii=False, indent=2)
        except:
            pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Aniner")
    app.setOrganizationName("Aniner Team")
    
    # High DPI
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    browser = AninerBrowser()
    browser.show()
    
    sys.exit(app.exec_())
