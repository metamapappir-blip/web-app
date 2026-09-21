const tabsContainer = document.getElementById('tabsContainer');
const urlInput = document.getElementById('urlInput');
const tabBar = document.getElementById('tabBar');
const suggestions = document.getElementById('suggestions');
const toastContainer = document.getElementById('toastContainer');

let tabs = [];
let activeTabId = null;
let blockedCount = 0;
let searchHistoryCache = [];

function showToast(message, type='info', duration=3000){
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  const icons = { success:'✅', error:'❌', info:'ℹ️', warning:'⚠️' };
  toast.innerHTML = `<span>${icons[type]||'ℹ️'}</span><span style="flex:1;font-size:13px">${message}</span><span style="cursor:pointer;opacity:.5" onclick="this.parentElement.remove()">✕</span>`;
  toastContainer.appendChild(toast);
  setTimeout(()=>{ toast.style.opacity='0'; toast.style.transform='translateY(10px)'; setTimeout(()=>toast.remove(),300); }, duration);
}

function renderTabs(){
  tabsContainer.innerHTML='';
  tabs.forEach(tab=>{
    const el = document.createElement('div');
    el.className = `tab ${tab.id===activeTabId?'active':''}`;
    el.dataset.id = tab.id;
    el.innerHTML = `
      ${tab.isLoading?'<div class="loading"></div>':`<div class="favicon">${tab.url?.includes('google')?'G':tab.url?.includes('youtube')?'▶':tab.url?.includes('github')?'◈':'🌐'}</div>`}
      <span class="title">${escapeHtml(tab.title||'تب جدید')}</span>
      <span class="close" title="بستن">✕</span>
    `;
    el.addEventListener('click', (e)=>{
      if(e.target.classList.contains('close')){
        window.aninerAPI.closeTab(tab.id);
      } else {
        window.aninerAPI.switchTab(tab.id);
      }
    });
    el.addEventListener('contextmenu', (e)=>{
      e.preventDefault();
      showContextMenu(e.clientX, e.clientY, tab.id);
    });
    // drag to reorder (simplified)
    el.draggable = true;
    tabsContainer.appendChild(el);
  });
}

function escapeHtml(s){ return (s||'').replace(/[&<>"']/g, m=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[m])); }

function updateAddressBar(url){
  if(!url) return;
  if(url.startsWith('data:')) {
    urlInput.value = 'aniner://home';
    document.getElementById('secureIcon').textContent='⭐';
  } else {
    urlInput.value = url;
    document.getElementById('secureIcon').textContent = url.startsWith('https')?'🔒':'⚠️';
  }
  document.getElementById('statusText').textContent = url;
}

// Navigation
document.getElementById('backBtn').onclick = ()=> window.aninerAPI.goBack();
document.getElementById('forwardBtn').onclick = ()=> window.aninerAPI.goForward();
document.getElementById('reloadBtn').onclick = ()=> {
  const btn = document.getElementById('reloadBtn');
  if(btn.textContent==='✕'){ window.aninerAPI.stop(); } else { window.aninerAPI.reload(); }
};
document.getElementById('homeBtn').onclick = ()=> window.aninerAPI.goHome();
document.getElementById('newTabBtn').onclick = ()=> window.aninerAPI.newTab();
document.getElementById('menuNewTab').onclick = ()=> { window.aninerAPI.newTab(); hideMainMenu(); };
document.getElementById('menuNewWindow').onclick = ()=> window.aninerAPI.newTab();

urlInput.addEventListener('keydown', (e)=>{
  if(e.key==='Enter'){
    const val = urlInput.value.trim();
    if(val){
      window.aninerAPI.navigate(val);
      suggestions.classList.remove('show');
      urlInput.blur();
    }
  }
  if(e.key==='Escape'){
    suggestions.classList.remove('show');
    const active = tabs.find(t=>t.id===activeTabId);
    if(active) updateAddressBar(active.url);
  }
});

urlInput.addEventListener('input', async ()=>{
  const q = urlInput.value.trim();
  if(!q){ suggestions.classList.remove('show'); return; }
  if(q.length<2){ suggestions.classList.remove('show'); return; }
  
  // Local history suggestions
  let items = [];
  if(q.length>1){
    try {
      const hist = await window.aninerAPI.searchHistory(q);
      items = hist.slice(0,5).map(h=>({ type:'history', title:h.title, url:h.url, icon:'🕘' }));
    } catch {}
  }
  // Search suggestions
  items.push({ type:'search', title:`جستجو برای "${q}" در گوگل`, url:`https://www.google.com/search?q=${encodeURIComponent(q)}`, icon:'🔍' });
  if(!q.includes(' ') && q.includes('.')){
    items.unshift({ type:'url', title: q.startsWith('http')?q:`https://${q}`, url: q.startsWith('http')?q:`https://${q}`, icon:'🌐' });
  }
  
  suggestions.innerHTML = items.map(i=>`
    <div class="sugg-item" data-url="${escapeHtml(i.url)}">
      <div class="icon">${i.icon}</div>
      <div class="info"><div class="title">${escapeHtml(i.title)}</div><div class="url">${escapeHtml(i.url)}</div></div>
    </div>
  `).join('');
  suggestions.querySelectorAll('.sugg-item').forEach(el=>{
    el.onclick = ()=>{
      window.aninerAPI.navigate(el.dataset.url);
      suggestions.classList.remove('show');
    };
  });
  suggestions.classList.add('show');
});

urlInput.addEventListener('focus', ()=>{ urlInput.select(); });
document.addEventListener('click', (e)=>{
  if(!e.target.closest('.address-bar-wrapper')) suggestions.classList.remove('show');
  if(!e.target.closest('#mainMenu') && !e.target.closest('#menuBtn')) hideMainMenu();
  if(!e.target.closest('.context-menu')) document.getElementById('contextMenu').classList.remove('show');
});

// Feature toggles
document.getElementById('adblockToggle').onclick = async ()=>{
  const enabled = await window.aninerAPI.toggleAdBlock();
  document.getElementById('adblockToggle').classList.toggle('active', enabled);
  document.getElementById('menuAdblock').querySelector('.check').textContent = enabled?'✓':'';
  showToast(enabled?'🛡️ مسدودکننده تبلیغات روشن شد':'🛡️ مسدودکننده خاموش شد', enabled?'success':'warning');
  document.getElementById('adblockStatus').textContent = `🛡️ تبلیغات مسدود شد: ${blockedCount}`;
};
document.getElementById('vpnToggle').onclick = async ()=>{
  const btn = document.getElementById('vpnToggle');
  btn.disabled=true;
  btn.innerHTML='<span class="ico">⏳</span>';
  const enabled = await window.aninerAPI.toggleVPN();
  btn.disabled=false;
  btn.classList.toggle('active', enabled);
  btn.innerHTML='<span class="ico">🔒</span>';
  document.getElementById('vpnStatus').textContent = enabled?'🔒 VPN روشن - متصل به آلمان':'VPN خاموش';
  document.getElementById('menuVPN').querySelector('.check').textContent = enabled?'✓':'';
  showToast(enabled?'🔒 VPN متصل شد - IP شما مخفی شد':'🔒 VPN قطع شد','info');
};
document.getElementById('darkToggle').onclick = async ()=>{
  const enabled = await window.aninerAPI.toggleDarkMode();
  document.getElementById('darkToggle').classList.toggle('active', enabled);
  showToast(enabled?'🌙 حالت تاریک هوشمند فعال شد - همه سایت‌ها تاریک شدند':'🌙 حالت تاریک خاموش شد','info');
};

// Action buttons
document.getElementById('screenshotBtn').onclick = async ()=>{
  showToast('📸 در حال گرفتن اسکرین‌شات...','info');
  const path = await window.aninerAPI.takeScreenshot('full');
  if(path) showToast(`✅ اسکرین‌شات ذخیره شد: ${path}`,'success',5000);
};
document.getElementById('readerBtn').onclick = ()=> window.aninerAPI.readerMode();
document.getElementById('pipBtn').onclick = ()=> window.aninerAPI.togglePiP();
document.getElementById('translateBtn').onclick = ()=>{
  const lang = prompt('ترجمه به چه زبانی؟ (fa, en, de, fr, ar...)', 'fa');
  if(lang) window.aninerAPI.translatePage(lang);
};
document.getElementById('bookmarkBtn').onclick = async ()=>{
  const active = tabs.find(t=>t.id===activeTabId);
  if(!active) return;
  await window.aninerAPI.addBookmark({ title: active.title, url: active.url });
  document.getElementById('bookmarkBtn').textContent='★';
  showToast('⭐ به بوکمارک‌ها اضافه شد','success');
};
document.getElementById('qrBtn').onclick = async ()=>{
  const active = tabs.find(t=>t.id===activeTabId);
  if(!active) return;
  const qrUrl = await window.aninerAPI.generateQR(active.url);
  openSidebar('QR Code', `<div class="qr-view"><img src="${qrUrl}"><p>${escapeHtml(active.url)}</p><button class="welcome-btn" style="margin-top:16px;padding:10px 20px;font-size:13px" onclick="navigator.clipboard.writeText('${active.url}'); window.showToast('لینک کپی شد','success')">کپی لینک</button></div>`);
};
document.getElementById('copyLinkBtn').onclick = ()=>{
  navigator.clipboard.writeText(urlInput.value);
  showToast('🔗 لینک کپی شد','success');
};
document.getElementById('downloadBtn').onclick = ()=> openDownloads();
document.getElementById('historyBtn').onclick = ()=> openHistory();
document.getElementById('bookmarkListBtn').onclick = ()=> openBookmarks();

// Sidebar
function openSidebar(title, html){
  document.getElementById('sidebarTitle').textContent=title;
  document.getElementById('sidebarContent').innerHTML=html;
  document.getElementById('sidebar').classList.add('open');
}
document.getElementById('closeSidebar').onclick = ()=> document.getElementById('sidebar').classList.remove('open');

async function openBookmarks(){
  const list = await window.aninerAPI.getBookmarks();
  if(list.length===0){ openSidebar('بوکمارک‌ها','<p style="opacity:.6;text-align:center;padding:40px">هنوز بوکمارکی نداری<br>⭐ روی ستاره کلیک کن تا اضافه بشه</p>'); return; }
  const html = list.map(b=>`<div class="bookmark-item" data-url="${escapeHtml(b.url)}"><div class="t">${escapeHtml(b.title)}</div><div class="u">${escapeHtml(b.url)}</div></div>`).join('');
  openSidebar('بوکمارک‌ها', html);
  document.querySelectorAll('.bookmark-item').forEach(el=> el.onclick = ()=> window.aninerAPI.navigate(el.dataset.url));
}
async function openHistory(){
  const list = await window.aninerAPI.getHistory();
  if(list.length===0){ openSidebar('تاریخچه','<p style="opacity:.6;text-align:center;padding:40px">تاریخچه خالیه</p>'); return; }
  const html = `<div style="margin-bottom:12px"><input id="histSearch" placeholder="جستجو در تاریخچه..." style="width:100%;padding:10px 14px;border-radius:10px;border:1px solid var(--border);background:var(--bg3);color:#fff;outline:none"></div>` + list.map(h=>{
    const d = new Date(h.time);
    return `<div class="history-item" data-url="${escapeHtml(h.url)}"><div class="t">${escapeHtml(h.title)}</div><div class="u">${escapeHtml(h.url)}</div><div style="font-size:10px;opacity:.4;margin-top:4px">${d.toLocaleString('fa-IR')}</div></div>`;
  }).join('');
  openSidebar('تاریخچه', html);
  document.getElementById('histSearch')?.addEventListener('input', async (e)=>{
    const q = e.target.value;
    const res = await window.aninerAPI.searchHistory(q);
    const container = document.getElementById('sidebarContent');
    const items = res.map(h=>`<div class="history-item" data-url="${escapeHtml(h.url)}"><div class="t">${escapeHtml(h.title)}</div><div class="u">${escapeHtml(h.url)}</div></div>`).join('');
    // keep search input
    const existing = container.querySelector('#histSearch')?.value || '';
    container.innerHTML = `<div style="margin-bottom:12px"><input id="histSearch" value="${escapeHtml(existing)}" placeholder="جستجو در تاریخچه..." style="width:100%;padding:10px 14px;border-radius:10px;border:1px solid var(--border);background:var(--bg3);color:#fff;outline:none"></div>` + items;
    container.querySelectorAll('.history-item').forEach(el=> el.onclick = ()=> window.aninerAPI.navigate(el.dataset.url));
  });
  document.querySelectorAll('.history-item').forEach(el=> el.onclick = ()=> window.aninerAPI.navigate(el.dataset.url));
}
async function openDownloads(){
  openSidebar('دانلودها', '<p style="opacity:.6;text-align:center;padding:40px">دانلودها در پوشه Downloads ذخیره میشن<br>⬇️</p>');
}

// Main menu
function hideMainMenu(){ document.getElementById('mainMenu').classList.remove('show'); }
document.getElementById('menuBtn').onclick = (e)=>{
  e.stopPropagation();
  document.getElementById('mainMenu').classList.toggle('show');
};
document.getElementById('menuScreenshot').onclick = ()=>{ hideMainMenu(); document.getElementById('screenshotBtn').click(); };
document.getElementById('menuQR').onclick = ()=>{ hideMainMenu(); document.getElementById('qrBtn').click(); };
document.getElementById('menuReader').onclick = ()=>{ hideMainMenu(); window.aninerAPI.readerMode(); };
document.getElementById('menuPiP').onclick = ()=>{ hideMainMenu(); window.aninerAPI.togglePiP(); };
document.getElementById('menuTranslate').onclick = ()=>{ hideMainMenu(); document.getElementById('translateBtn').click(); };
document.getElementById('menuAdblock').onclick = ()=>{ hideMainMenu(); document.getElementById('adblockToggle').click(); };
document.getElementById('menuVPN').onclick = ()=>{ hideMainMenu(); document.getElementById('vpnToggle').click(); };
document.getElementById('menuClear').onclick = async ()=>{
  hideMainMenu();
  if(confirm('همه کش، کوکی و تاریخچه پاک بشه؟')){
    await window.aninerAPI.clearData('all');
    showToast('🧹 همه داده‌ها پاک شد','success');
  }
};
document.getElementById('menuDownloads').onclick = ()=>{ hideMainMenu(); openDownloads(); };
document.getElementById('menuHistory').onclick = ()=>{ hideMainMenu(); openHistory(); };
document.getElementById('menuBookmarks').onclick = ()=>{ hideMainMenu(); openBookmarks(); };
document.getElementById('menuSettings').onclick = ()=>{ hideMainMenu(); openSettings(); };
document.getElementById('menuAbout').onclick = ()=>{
  hideMainMenu();
  alert('Aniner Browser v1.0.0\n\n🚀 سریع‌ترین مرورگر ایرانی\n🛡️ مسدودکننده تبلیغات هوشمند\n🔒 VPN رایگان نامحدود\n🌙 حالت تاریک هوشمند\n📸 اسکرین‌شات حرفه‌ای\n🎥 دانلود ویدیو + PiP\n📖 حالت مطالعه\n🌐 ترجمه 100+ زبان\n🧩 پشتیبانی از افزونه‌های کروم\n\nساخته شده با ❤️ برای اینترنت آزاد\nمتن باز - رایگان - بدون جاسوسی');
};
document.getElementById('menuStar').onclick = ()=>{
  hideMainMenu();
  window.aninerAPI.navigate('https://github.com/metamapappir-blip/web-app');
  showToast('⭐ مرسی که ستاره میدی! دمت گرم','success');
};
document.getElementById('menuExtensions').onclick = ()=>{
  hideMainMenu();
  showToast('🧩 پشتیبانی از افزونه‌های کروم به زودی - در حال توسعه','info');
};
document.getElementById('menuPassword').onclick = ()=>{
  hideMainMenu();
  openSidebar('مدیریت رمزها', '<p style="padding:20px;opacity:.7;line-height:1.8">🔑 مدیریت رمز عبور امن<br><br>• همه رمزها با AES-256 رمزنگاری میشن<br>• فقط روی دستگاه شما ذخیره میشن<br>• هیچ سروری نداریم<br><br>به زودی...</p>');
};

function openSettings(){
  openSidebar('تنظیمات Aniner', `
    <div style="display:flex;flex-direction:column;gap:16px">
      <div style="background:var(--bg3);padding:16px;border-radius:12px;border:1px solid var(--border)">
        <h4 style="margin-bottom:12px">🔍 موتور جستجو</h4>
        <select id="searchEngine" style="width:100%;padding:10px;border-radius:8px;background:var(--bg2);color:#fff;border:1px solid var(--border)">
          <option value="google">Google</option>
          <option value="duckduckgo">DuckDuckGo (حریم خصوصی)</option>
          <option value="bing">Bing</option>
          <option value="brave">Brave Search</option>
        </select>
      </div>
      <div style="background:var(--bg3);padding:16px;border-radius:12px;border:1px solid var(--border)">
        <h4 style="margin-bottom:12px">🎨 تم</h4>
        <div style="display:flex;gap:8px">
          <button class="welcome-btn" style="flex:1;padding:10px" onclick="document.body.className='dark'">تاریک</button>
          <button class="welcome-btn" style="flex:1;padding:10px;background:#fff;color:#111" onclick="document.body.className=''">روشن</button>
        </div>
      </div>
      <div style="background:var(--bg3);padding:16px;border-radius:12px;border:1px solid var(--border)">
        <h4 style="margin-bottom:12px">🔒 پروکسی / VPN دستی</h4>
        <input id="proxyUrl" placeholder="socks5://127.0.0.1:1080 یا http://..." style="width:100%;padding:10px;border-radius:8px;background:var(--bg2);color:#fff;border:1px solid var(--border);direction:ltr">
        <div style="display:flex;gap:8px;margin-top:10px">
          <button class="welcome-btn" style="flex:1;padding:10px" onclick="setCustomProxy()">اعمال</button>
          <button class="welcome-btn" style="flex:1;padding:10px;background:var(--bg2)" onclick="clearProxy()">غیرفعال</button>
        </div>
        <p style="font-size:11px;opacity:.5;margin-top:8px">برای اتصال به Nova Proxy یا V2Ray از این قسمت استفاده کن</p>
      </div>
      <div style="background:linear-gradient(135deg,#7c3aed22,#ec489922);padding:16px;border-radius:12px;border:1px solid #7c3aed33">
        <h4>⭐ از Aniner حمایت کن</h4>
        <p style="font-size:12px;opacity:.8;margin:8px 0">اگه خوشت اومده ستاره بده، دوستات رو دعوت کن</p>
        <button class="welcome-btn" style="width:100%;padding:10px" onclick="window.aninerAPI.navigate('https://github.com/metamapappir-blip/web-app')">رفتن به GitHub</button>
      </div>
    </div>
  `);
}
window.setCustomProxy = async ()=>{
  const url = document.getElementById('proxyUrl').value.trim();
  if(!url) return;
  await window.aninerAPI.setProxy({ enabled:true, url });
  showToast('🔒 پروکسی اعمال شد','success');
};
window.clearProxy = async ()=>{
  await window.aninerAPI.setProxy({ enabled:false });
  showToast('پروکسی غیرفعال شد','info');
};

// Context menu
function showContextMenu(x,y,tabId){
  const menu = document.getElementById('contextMenu');
  menu.style.left=x+'px';
  menu.style.top=y+'px';
  menu.classList.add('show');
  menu.dataset.tabId=tabId;
}
document.getElementById('contextMenu').addEventListener('click', (e)=>{
  const action = e.target.dataset.action;
  const tabId = e.target.closest('.context-menu').dataset.tabId;
  if(!action) return;
  if(action==='new-tab') window.aninerAPI.newTab();
  if(action==='duplicate') window.aninerAPI.duplicateTab(tabId);
  if(action==='close') window.aninerAPI.closeTab(tabId);
  if(action==='reload') window.aninerAPI.reload();
  document.getElementById('contextMenu').classList.remove('show');
});

// IPC listeners
window.aninerAPI.onTabsChanged((newTabs)=>{
  tabs=newTabs;
  renderTabs();
});
window.aninerAPI.onTabUpdate((data)=>{
  if(data.activeId){ activeTabId=data.activeId; renderTabs(); }
  if(data.url){ updateAddressBar(data.url); const t = tabs.find(x=>x.id===activeTabId); if(t){ t.url=data.url; } }
});
window.aninerAPI.onLoadingState((data)=>{
  const tab = tabs.find(t=>t.id===data.id);
  if(tab){
    tab.isLoading=data.isLoading;
    if(data.url) tab.url=data.url;
    if(data.title) tab.title=data.title;
    renderTabs();
    if(data.id===activeTabId){
      updateAddressBar(data.url||tab.url);
      const reloadBtn = document.getElementById('reloadBtn');
      reloadBtn.textContent = data.isLoading?'✕':'↻';
      document.getElementById('statusText').textContent = data.isLoading?'در حال بارگذاری...':(data.url||'آماده');
      if(!data.isLoading) document.getElementById('welcomeOverlay').style.display='none';
    }
  }
});
window.aninerAPI.onNotification((data)=>{
  if(data.type==='download-start') showToast(`⬇️ دانلود شروع شد: ${data.fileName}`,'info');
  if(data.type==='download-done') showToast(`✅ دانلود تمام شد: ${data.fileName}`,'success',5000);
  if(data.type==='adblock') blockedCount++;
});
window.aninerAPI.onDownloadProgress((data)=>{
  document.getElementById('statusText').textContent = `⬇️ ${data.fileName} - ${Math.round(data.progress*100)}%`;
});

// Keyboard shortcuts
document.addEventListener('keydown', (e)=>{
  if((e.ctrlKey||e.metaKey) && e.key==='t'){ e.preventDefault(); window.aninerAPI.newTab(); }
  if((e.ctrlKey||e.metaKey) && e.key==='w'){ e.preventDefault(); if(activeTabId) window.aninerAPI.closeTab(activeTabId); }
  if((e.ctrlKey||e.metaKey) && e.key==='l'){ e.preventDefault(); urlInput.focus(); urlInput.select(); }
  if((e.ctrlKey||e.metaKey) && e.key==='r'){ e.preventDefault(); window.aninerAPI.reload(); }
  if((e.ctrlKey||e.metaKey) && e.shiftKey && e.key==='S'){ e.preventDefault(); document.getElementById('screenshotBtn').click(); }
  if(e.key==='F5'){ e.preventDefault(); window.aninerAPI.reload(); }
  if((e.ctrlKey||e.metaKey) && e.key==='h'){ e.preventDefault(); openHistory(); }
  if((e.ctrlKey||e.metaKey) && e.key==='j'){ e.preventDefault(); openDownloads(); }
  if(e.key==='Escape'){ document.getElementById('sidebar').classList.remove('open'); hideMainMenu(); suggestions.classList.remove('show'); }
});

// Init
(async()=>{
  try {
    tabs = await window.aninerAPI.getTabs();
    renderTabs();
  } catch {}
})();
window.showToast = showToast;
