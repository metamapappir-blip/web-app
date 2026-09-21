const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('aninerAPI', {
  // Navigation
  navigate: (url) => ipcRenderer.invoke('navigate', url),
  goBack: () => ipcRenderer.invoke('go-back'),
  goForward: () => ipcRenderer.invoke('go-forward'),
  reload: () => ipcRenderer.invoke('reload'),
  stop: () => ipcRenderer.invoke('stop'),
  goHome: () => ipcRenderer.invoke('go-home'),

  // Tabs
  newTab: (url) => ipcRenderer.invoke('new-tab', url),
  closeTab: (id) => ipcRenderer.invoke('close-tab', id),
  switchTab: (id) => ipcRenderer.invoke('switch-tab', id),
  duplicateTab: (id) => ipcRenderer.invoke('duplicate-tab', id),
  getTabs: () => ipcRenderer.invoke('get-tabs'),

  // Features
  toggleAdBlock: () => ipcRenderer.invoke('toggle-adblock'),
  toggleVPN: () => ipcRenderer.invoke('toggle-vpn'),
  toggleDarkMode: () => ipcRenderer.invoke('toggle-dark-mode'),
  takeScreenshot: (type) => ipcRenderer.invoke('take-screenshot', type),
  openDevTools: () => ipcRenderer.invoke('open-devtools'),
  togglePiP: () => ipcRenderer.invoke('toggle-pip'),
  readerMode: () => ipcRenderer.invoke('reader-mode'),
  translatePage: (lang) => ipcRenderer.invoke('translate-page', lang),
  generateQR: (url) => ipcRenderer.invoke('generate-qr', url),
  clearData: (type) => ipcRenderer.invoke('clear-data', type),
  openDownloads: () => ipcRenderer.invoke('open-downloads'),
  openHistory: () => ipcRenderer.invoke('open-history'),
  openBookmarks: () => ipcRenderer.invoke('open-bookmarks'),
  addBookmark: (data) => ipcRenderer.invoke('add-bookmark', data),
  openSettings: () => ipcRenderer.invoke('open-settings'),
  setProxy: (config) => ipcRenderer.invoke('set-proxy', config),
  getSettings: () => ipcRenderer.invoke('get-settings'),
  saveSettings: (settings) => ipcRenderer.invoke('save-settings', settings),
  getBookmarks: () => ipcRenderer.invoke('get-bookmarks'),
  getHistory: () => ipcRenderer.invoke('get-history'),
  getDownloads: () => ipcRenderer.invoke('get-downloads'),
  searchHistory: (query) => ipcRenderer.invoke('search-history', query),
  
  // Events from main
  onTabUpdate: (callback) => ipcRenderer.on('tab-update', (_, data) => callback(data)),
  onTabsChanged: (callback) => ipcRenderer.on('tabs-changed', (_, data) => callback(data)),
  onLoadingState: (callback) => ipcRenderer.on('loading-state', (_, data) => callback(data)),
  onDownloadProgress: (callback) => ipcRenderer.on('download-progress', (_, data) => callback(data)),
  onSettingChanged: (callback) => ipcRenderer.on('setting-changed', (_, data) => callback(data)),
  onNotification: (callback) => ipcRenderer.on('notification', (_, data) => callback(data)),
});
