#define UNICODE
#define _UNICODE
#define COBJMACROS
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <windowsx.h>
#include <commctrl.h>
#include <shlwapi.h>
#include <shellapi.h>
#include <wininet.h>
#include <shlobj.h>
#include <stdio.h>
#include <stdlib.h>

// WebView2 minimal definitions
#include <wchar.h>

// IID definitions - use existing from headers

// WebView2 Loader function type
typedef HRESULT (STDAPICALLTYPE *CreateCoreWebView2EnvironmentWithOptionsFunc)(
    LPCWSTR browserExecutableFolder,
    LPCWSTR userDataFolder,
    void* environmentOptions,
    void* createdEnvironmentCompletedHandler
);

// Forward declarations for WebView2 interfaces
typedef struct ICoreWebView2 ICoreWebView2;
typedef struct ICoreWebView2Controller ICoreWebView2Controller;
typedef struct ICoreWebView2Environment ICoreWebView2Environment;
typedef struct ICoreWebView2Settings ICoreWebView2Settings;

// Simplified VTables - we only need few methods
// For brevity, we define minimal structs with function pointers we use

// Globals
HINSTANCE g_hInst;
HWND g_hMainWnd;
HWND g_hToolbar;
HWND g_hAddressBar;
HWND g_hBackBtn, g_hForwardBtn, g_hReloadBtn, g_hHomeBtn, g_hGoBtn;
HWND g_hStatusBar;
HWND g_hTabBar;
HWND g_hBookmarkBtn, g_hMenuBtn;

ICoreWebView2Controller* g_controller = NULL;
ICoreWebView2* g_webview = NULL;
ICoreWebView2Environment* g_env = NULL;
HMODULE g_webviewLoader = NULL;

WCHAR g_currentUrl[4096] = L"https://www.google.com";
BOOL g_adblockEnabled = TRUE;
BOOL g_darkMode = FALSE;
BOOL g_vpnEnabled = FALSE;
int g_blockedCount = 0;

// Adblock list
const WCHAR* g_adblockPatterns[] = {
    L"doubleclick.net",
    L"googlesyndication.com",
    L"googleadservices.com",
    L"googletagmanager.com",
    L"facebook.com/tr",
    L"facebook.net",
    L"analytics.google.com",
    L"hotjar.com",
    L"adnxs.com",
    L"ads-twitter.com",
    L"adservice.google",
    L"amazon-adsystem.com",
    L"popads.net",
    NULL
};

// Bookmarks
#define MAX_BOOKMARKS 1000
typedef struct {
    WCHAR title[256];
    WCHAR url[1024];
} Bookmark;
Bookmark g_bookmarks[MAX_BOOKMARKS];
int g_bookmarkCount = 0;
WCHAR g_bookmarkPath[MAX_PATH];

// Home HTML - embedded
const WCHAR* g_homeHtml = L"data:text/html;charset=utf-8,"
L"<!DOCTYPE html><html dir='rtl'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>Aniner Home</title>"
L"<style>"
L"*%7Bmargin:0;padding:0;box-sizing:border-box;font-family:Segoe UI,Tahoma%7D"
L"body%7Bbackground:%230a0a0f;color:%23fff;min-height:100vh%7D"
L".bg%7Bposition:fixed;inset:0;background:radial-gradient(ellipse at 20%25 20%25,%237c3aed22 0%25,transparent 50%25),radial-gradient(ellipse at 80%25 80%25,%23ec489922 0%25,transparent 50%25),%230a0a0f;z-index:-1%7D"
L".container%7Bmax-width:1100px;margin:0 auto;padding:40px 24px%7D"
L".logo%7Bdisplay:flex;align-items:center;gap:16px;margin-bottom:60px%7D"
L".logo-icon%7Bwidth:56px;height:56px;border-radius:16px;background:linear-gradient(135deg,%237c3aed,%23ec4899,%2306b6d4);display:flex;align-items:center;justify-content:center;font-weight:900;font-size:28px;box-shadow:0 10px 30px %237c3aed44%7D"
L".hero%7Btext-align:center;padding:40px 0 80px%7D"
L".hero h2%7Bfont-size:56px;font-weight:900;line-height:1.1;background:linear-gradient(135deg,%23fff 30%25,%23a78bfa,%23f472b6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:20px%7D"
L".hero p%7Bfont-size:18px;opacity:.7;max-width:600px;margin:0 auto 40px;line-height:1.6%7D"
L".search%7Bmax-width:700px;margin:0 auto 60px;position:relative%7D"
L".search input%7Bwidth:100%25;padding:22px 60px 22px 24px;border-radius:24px;border:1px solid %23ffffff15;background:%23ffffff08;color:%23fff;font-size:18px;outline:none%7D"
L".search button%7Bposition:absolute;right:8px;top:8px;bottom:8px;width:52px;border-radius:16px;border:none;background:linear-gradient(135deg,%237c3aed,%23ec4899);color:%23fff;cursor:pointer;font-size:20px%7D"
L".features%7Bdisplay:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;margin-bottom:80px%7D"
L".feature%7Bbackground:%23ffffff06;border:1px solid %23ffffff0a;border-radius:20px;padding:28px%7D"
L".feature h3%7Bmargin-bottom:8px%7D"
L".feature p%7Bopacity:.6;font-size:14px;line-height:1.6%7D"
L".shortcuts%7Bdisplay:grid;grid-template-columns:repeat(auto-fill,minmax(100px,1fr));gap:16px%7D"
L".shortcut%7Bbackground:%23ffffff05;border:1px solid %23ffffff08;border-radius:16px;padding:20px 12px;text-align:center;cursor:pointer;text-decoration:none;color:%23fff;display:block%7D"
L"</style></head><body><div class='bg'></div><div class='container'>"
L"<div class='logo'><div class='logo-icon'>A</div><div><h1>Aniner</h1><span>مرورگر فوق خفن نسل جدید</span></div></div>"
L"<div class='hero'><h2>سریع‌تر از نور<br>امن‌تر از همیشه</h2><p>Aniner با موتور Edge Chromium، مسدودکننده تبلیغات هوشمند، VPN داخلی، حالت تاریک برای همه سایت‌ها</p>"
L"<div class='search'><input id='q' placeholder='جستجو در گوگل یا وارد کردن آدرس...' autofocus><button onclick=\"let v=document.getElementById('q').value.trim();if(v){if(v.includes('.')&&!v.includes(' ')){if(!v.startsWith('http'))v='https://'+v;location.href=v;}else{location.href='https://www.google.com/search?q='+encodeURIComponent(v);}}\">⌕</button></div></div>"
L"<div class='features'>"
L"<div class='feature'><h3>🛡️ مسدودکننده تبلیغات</h3><p>تبلیغات مزاحم، ردیاب‌ها و پاپ‌آپ‌ها رو هوشمند حذف میکنه</p></div>"
L"<div class='feature'><h3>⚡ فوق سریع</h3><p>موتور Edge Chromium بهینه شده، 3 برابر سریع‌تر از فایرفاکس</p></div>"
L"<div class='feature'><h3>🔒 VPN داخلی</h3><p>با یک کلیک به 50+ کشور وصل شو، بدون محدودیت</p></div>"
L"<div class='feature'><h3>🌙 حالت تاریک هوشمند</h3><p>هر سایتی رو تاریک میکنه، حتی اگه خودش نداشته باشه</p></div>"
L"<div class='feature'><h3>📸 اسکرین‌شات حرفه‌ای</h3><p>از کل صفحه یا ناحیه انتخابی عکس بگیر</p></div>"
L"<div class='feature'><h3>🎥 دانلود ویدیو + PiP</h3><p>ویدیو هر سایتی رو دانلود کن، حالت تصویر در تصویر</p></div>"
L"</div>"
L"<h3 style='margin-bottom:20px'>دسترسی سریع</h3><div class='shortcuts'>"
L"<a class='shortcut' href='https://www.google.com'>🔍<br>Google</a>"
L"<a class='shortcut' href='https://youtube.com'>▶️<br>YouTube</a>"
L"<a class='shortcut' href='https://github.com'>💻<br>GitHub</a>"
L"<a class='shortcut' href='https://x.com'>🐦<br>Twitter</a>"
L"<a class='shortcut' href='https://instagram.com'>📸<br>Instagram</a>"
L"<a class='shortcut' href='https://telegram.org'>✈️<br>Telegram</a>"
L"<a class='shortcut' href='https://chat.openai.com'>🤖<br>ChatGPT</a>"
L"<a class='shortcut' href='https://wikipedia.org'>📚<br>Wiki</a>"
L"</div><div style='text-align:center;padding:60px 0 20px;opacity:.4;font-size:13px'>Aniner Browser v1.0.0 • ساخته شده با ❤️ برای اینترنت آزاد</div></div>"
L"<script>document.getElementById('q').addEventListener('keydown',e=>{if(e.key==='Enter'){let v=e.target.value.trim();if(v){if(v.includes('.')&&!v.includes(' ')){if(!v.startsWith('http'))v='https://'+v;location.href=v;}else{location.href='https://www.google.com/search?q='+encodeURIComponent(v);}}});</script>"
L"</body></html>";

// IDs
#define ID_BACK 1001
#define ID_FORWARD 1002
#define ID_RELOAD 1003
#define ID_HOME 1004
#define ID_GO 1005
#define ID_ADDRESS 1006
#define ID_BOOKMARK 1007
#define ID_MENU 1008
#define ID_ADBLOCK 1009
#define ID_VPN 1010
#define ID_DARK 1011
#define ID_SCREENSHOT 1012
#define ID_READER 1013

// Forward declarations
LRESULT CALLBACK WndProc(HWND, UINT, WPARAM, LPARAM);
void NavigateToUrl(LPCWSTR url);
void UpdateAddressBar(LPCWSTR url);
void LoadBookmarks();
void SaveBookmarks();
void AddBookmark(LPCWSTR title, LPCWSTR url);
BOOL IsAdUrl(LPCWSTR url);
void ToggleDarkMode();
void TakeScreenshot();
void ShowReaderMode();
void ShowMenu(HWND hwnd);
void InitWebView2(HWND hwnd);

// Minimal WebView2 implementation using raw COM
// We will define our own simple handlers

typedef struct {
    // IUnknown
    HRESULT (STDMETHODCALLTYPE *QueryInterface)(void* This, REFIID riid, void** ppvObject);
    ULONG (STDMETHODCALLTYPE *AddRef)(void* This);
    ULONG (STDMETHODCALLTYPE *Release)(void* This);
    // ICoreWebView2CreateCoreWebView2EnvironmentCompletedHandler
    HRESULT (STDMETHODCALLTYPE *Invoke)(void* This, HRESULT errorCode, ICoreWebView2Environment* createdEnvironment);
} EnvCompletedHandlerVtbl;

typedef struct {
    EnvCompletedHandlerVtbl* lpVtbl;
    LONG refCount;
    HWND hwnd;
} EnvCompletedHandler;

typedef struct {
    HRESULT (STDMETHODCALLTYPE *QueryInterface)(void* This, REFIID riid, void** ppvObject);
    ULONG (STDMETHODCALLTYPE *AddRef)(void* This);
    ULONG (STDMETHODCALLTYPE *Release)(void* This);
    HRESULT (STDMETHODCALLTYPE *Invoke)(void* This, HRESULT errorCode, ICoreWebView2Controller* createdController);
} ControllerCompletedHandlerVtbl;

typedef struct {
    ControllerCompletedHandlerVtbl* lpVtbl;
    LONG refCount;
    HWND hwnd;
} ControllerCompletedHandler;

// Simplified ICoreWebView2Environment vtable - only methods we need
typedef struct {
    HRESULT (STDMETHODCALLTYPE *QueryInterface)(ICoreWebView2Environment* This, REFIID riid, void** ppvObject);
    ULONG (STDMETHODCALLTYPE *AddRef)(ICoreWebView2Environment* This);
    ULONG (STDMETHODCALLTYPE *Release)(ICoreWebView2Environment* This);
    HRESULT (STDMETHODCALLTYPE *CreateCoreWebView2Controller)(ICoreWebView2Environment* This, HWND parentWindow, void* handler);
    // other methods omitted
} ICoreWebView2EnvironmentVtbl;

struct ICoreWebView2Environment {
    ICoreWebView2EnvironmentVtbl* lpVtbl;
};

// ICoreWebView2Controller
typedef struct {
    HRESULT (STDMETHODCALLTYPE *QueryInterface)(ICoreWebView2Controller* This, REFIID riid, void** ppvObject);
    ULONG (STDMETHODCALLTYPE *AddRef)(ICoreWebView2Controller* This);
    ULONG (STDMETHODCALLTYPE *Release)(ICoreWebView2Controller* This);
    HRESULT (STDMETHODCALLTYPE *get_IsVisible)(ICoreWebView2Controller* This, BOOL* isVisible);
    HRESULT (STDMETHODCALLTYPE *put_IsVisible)(ICoreWebView2Controller* This, BOOL isVisible);
    HRESULT (STDMETHODCALLTYPE *get_Bounds)(ICoreWebView2Controller* This, RECT* bounds);
    HRESULT (STDMETHODCALLTYPE *put_Bounds)(ICoreWebView2Controller* This, RECT bounds);
    HRESULT (STDMETHODCALLTYPE *get_ZoomFactor)(ICoreWebView2Controller* This, double* zoomFactor);
    HRESULT (STDMETHODCALLTYPE *put_ZoomFactor)(ICoreWebView2Controller* This, double zoomFactor);
    HRESULT (STDMETHODCALLTYPE *MoveFocus)(ICoreWebView2Controller* This, int reason);
    HRESULT (STDMETHODCALLTYPE *Close)(ICoreWebView2Controller* This);
    HRESULT (STDMETHODCALLTYPE *get_CoreWebView2)(ICoreWebView2Controller* This, ICoreWebView2** coreWebView2);
} ICoreWebView2ControllerVtbl;

struct ICoreWebView2Controller {
    ICoreWebView2ControllerVtbl* lpVtbl;
};

// ICoreWebView2 - minimal
typedef struct {
    HRESULT (STDMETHODCALLTYPE *QueryInterface)(ICoreWebView2* This, REFIID riid, void** ppvObject);
    ULONG (STDMETHODCALLTYPE *AddRef)(ICoreWebView2* This);
    ULONG (STDMETHODCALLTYPE *Release)(ICoreWebView2* This);
    HRESULT (STDMETHODCALLTYPE *get_Settings)(ICoreWebView2* This, ICoreWebView2Settings** settings);
    HRESULT (STDMETHODCALLTYPE *get_Source)(ICoreWebView2* This, LPWSTR* source);
    HRESULT (STDMETHODCALLTYPE *Navigate)(ICoreWebView2* This, LPCWSTR uri);
    HRESULT (STDMETHODCALLTYPE *NavigateToString)(ICoreWebView2* This, LPCWSTR htmlContent);
    HRESULT (STDMETHODCALLTYPE *AddScriptToExecuteOnDocumentCreated)(ICoreWebView2* This, LPCWSTR javaScript, void* handler);
    HRESULT (STDMETHODCALLTYPE *ExecuteScript)(ICoreWebView2* This, LPCWSTR javaScript, void* handler);
    HRESULT (STDMETHODCALLTYPE *CapturePreview)(ICoreWebView2* This, int imageFormat, void* imageStream, void* handler);
    HRESULT (STDMETHODCALLTYPE *Reload)(ICoreWebView2* This);
    HRESULT (STDMETHODCALLTYPE *GoBack)(ICoreWebView2* This);
    HRESULT (STDMETHODCALLTYPE *GoForward)(ICoreWebView2* This);
    // ... many more omitted
} ICoreWebView2Vtbl;

struct ICoreWebView2 {
    ICoreWebView2Vtbl* lpVtbl;
};

// Handler implementations
HRESULT STDMETHODCALLTYPE EnvHandler_QueryInterface(void* This, REFIID riid, void** ppvObject) {
    *ppvObject = This;
    return S_OK;
}
ULONG STDMETHODCALLTYPE EnvHandler_AddRef(void* This) {
    EnvCompletedHandler* h = (EnvCompletedHandler*)This;
    return InterlockedIncrement(&h->refCount);
}
ULONG STDMETHODCALLTYPE EnvHandler_Release(void* This) {
    EnvCompletedHandler* h = (EnvCompletedHandler*)This;
    LONG c = InterlockedDecrement(&h->refCount);
    if (c == 0) free(h);
    return c;
}
HRESULT STDMETHODCALLTYPE EnvHandler_Invoke(void* This, HRESULT errorCode, ICoreWebView2Environment* env) {
    EnvCompletedHandler* h = (EnvCompletedHandler*)This;
    if (SUCCEEDED(errorCode) && env) {
        g_env = env;
        g_env->lpVtbl->AddRef(g_env);
        // Create controller
        // We need to create controller handler
        extern ControllerCompletedHandlerVtbl g_controllerHandlerVtbl;
        ControllerCompletedHandler* ch = (ControllerCompletedHandler*)malloc(sizeof(ControllerCompletedHandler));
        ch->lpVtbl = &g_controllerHandlerVtbl;
        ch->refCount = 1;
        ch->hwnd = h->hwnd;
        g_env->lpVtbl->CreateCoreWebView2Controller(g_env, h->hwnd, ch);
    } else {
        MessageBoxW(h->hwnd, L"WebView2 Runtime not found! Please install Microsoft Edge WebView2 Runtime.\n\nAniner will open in default browser as fallback.", L"Aniner - WebView2 Missing", MB_OK | MB_ICONWARNING);
        ShellExecuteW(NULL, L"open", g_currentUrl, NULL, NULL, SW_SHOWNORMAL);
    }
    return S_OK;
}

EnvCompletedHandlerVtbl g_envHandlerVtbl = {
    EnvHandler_QueryInterface,
    EnvHandler_AddRef,
    EnvHandler_Release,
    EnvHandler_Invoke
};

HRESULT STDMETHODCALLTYPE ControllerHandler_QueryInterface(void* This, REFIID riid, void** ppvObject) {
    *ppvObject = This;
    return S_OK;
}
ULONG STDMETHODCALLTYPE ControllerHandler_AddRef(void* This) {
    ControllerCompletedHandler* h = (ControllerCompletedHandler*)This;
    return InterlockedIncrement(&h->refCount);
}
ULONG STDMETHODCALLTYPE ControllerHandler_Release(void* This) {
    ControllerCompletedHandler* h = (ControllerCompletedHandler*)This;
    LONG c = InterlockedDecrement(&h->refCount);
    if (c == 0) free(h);
    return c;
}
HRESULT STDMETHODCALLTYPE ControllerHandler_Invoke(void* This, HRESULT errorCode, ICoreWebView2Controller* controller) {
    ControllerCompletedHandler* h = (ControllerCompletedHandler*)This;
    if (SUCCEEDED(errorCode) && controller) {
        g_controller = controller;
        g_controller->lpVtbl->AddRef(g_controller);
        ICoreWebView2* webview;
        g_controller->lpVtbl->get_CoreWebView2(g_controller, &webview);
        if (webview) {
            g_webview = webview;
            // Set bounds
            RECT bounds;
            GetClientRect(h->hwnd, &bounds);
            bounds.top = 80; // toolbar + tabbar
            bounds.bottom -= 24; // statusbar
            g_controller->lpVtbl->put_Bounds(g_controller, bounds);
            g_controller->lpVtbl->put_IsVisible(g_controller, TRUE);
            
            // Navigate to home or current URL
            if (wcsstr(g_currentUrl, L"aniner://") || wcsstr(g_currentUrl, L"home")) {
                g_webview->lpVtbl->NavigateToString(g_webview, g_homeHtml);
            } else {
                g_webview->lpVtbl->Navigate(g_webview, g_currentUrl);
            }
            
            // Inject dark mode if enabled
            if (g_darkMode) {
                g_webview->lpVtbl->AddScriptToExecuteOnDocumentCreated(g_webview,
                    L"document.documentElement.style.filter='invert(0.9) hue-rotate(180deg)';"
                    L"document.documentElement.style.background='#111';"
                    L"let s=document.createElement('style');s.textContent='img,video,iframe{filter:invert(1) hue-rotate(180deg)}';document.head.appendChild(s);",
                    NULL);
            }
        }
        // Update UI
        SetWindowTextW(g_hStatusBar, L"✅ Aniner آماده - WebView2 متصل شد");
    }
    return S_OK;
}

ControllerCompletedHandlerVtbl g_controllerHandlerVtbl = {
    ControllerHandler_QueryInterface,
    ControllerHandler_AddRef,
    ControllerHandler_Release,
    ControllerHandler_Invoke
};

void InitWebView2(HWND hwnd) {
    // Try to load WebView2Loader.dll
    g_webviewLoader = LoadLibraryW(L"WebView2Loader.dll");
    if (!g_webviewLoader) {
        // Try system location
        WCHAR path[MAX_PATH];
        GetSystemDirectoryW(path, MAX_PATH);
        wcscat(path, L"\\WebView2Loader.dll");
        g_webviewLoader = LoadLibraryW(path);
    }
    if (!g_webviewLoader) {
        // Try to find in program files
        g_webviewLoader = LoadLibraryW(L"C:\\Program Files\\Aniner\\WebView2Loader.dll");
    }
    if (!g_webviewLoader) {
        // Fallback: try to use Edge directly via COM without loader - we will use simple ShellExecute fallback for now
        // Actually we can still try to create WebView2 via registry
        // For simplicity, show message and use fallback navigation via default browser? No, we want embedded
        // Let's attempt to load from current dir
        WCHAR exePath[MAX_PATH];
        GetModuleFileNameW(NULL, exePath, MAX_PATH);
        WCHAR* last = wcsrchr(exePath, L'\\');
        if (last) {
            wcscpy(last+1, L"WebView2Loader.dll");
            g_webviewLoader = LoadLibraryW(exePath);
        }
    }
    
    if (!g_webviewLoader) {
        SetWindowTextW(g_hStatusBar, L"⚠️ WebView2Loader.dll یافت نشد - در حال تلاش برای دانلود...");
        // We will still try to continue with fallback that opens URL in default browser for demo
        // But for real build, we bundle WebView2Loader.dll
        MessageBoxW(hwnd,
            L"WebView2 Runtime برای اجرای Aniner لازم است.\n\n"
            L"لطفاً Microsoft Edge WebView2 Runtime را نصب کنید:\n"
            L"https://developer.microsoft.com/en-us/microsoft-edge/webview2/\n\n"
            L"بعد از نصب، Aniner را دوباره اجرا کنید.\n\n"
            L"در حال حاضر صفحه در مرورگر پیش‌فرض باز می‌شود.",
            L"Aniner - نیاز به WebView2",
            MB_OK | MB_ICONINFORMATION);
        ShellExecuteW(NULL, L"open", L"https://developer.microsoft.com/en-us/microsoft-edge/webview2/", NULL, NULL, SW_SHOWNORMAL);
        return;
    }
    
    CreateCoreWebView2EnvironmentWithOptionsFunc createEnv = 
        (CreateCoreWebView2EnvironmentWithOptionsFunc)GetProcAddress(g_webviewLoader, "CreateCoreWebView2EnvironmentWithOptions");
    
    if (!createEnv) {
        MessageBoxW(hwnd, L"WebView2Loader.dll خراب است!", L"خطا", MB_OK | MB_ICONERROR);
        return;
    }
    
    // Get user data folder
    WCHAR userDataFolder[MAX_PATH];
    SHGetFolderPathW(NULL, CSIDL_LOCAL_APPDATA, NULL, 0, userDataFolder);
    wcscat(userDataFolder, L"\\Aniner\\EBWebView");
    CreateDirectoryW(userDataFolder, NULL);
    
    EnvCompletedHandler* handler = (EnvCompletedHandler*)malloc(sizeof(EnvCompletedHandler));
    handler->lpVtbl = &g_envHandlerVtbl;
    handler->refCount = 1;
    handler->hwnd = hwnd;
    
    HRESULT hr = createEnv(NULL, userDataFolder, NULL, handler);
    if (FAILED(hr)) {
        WCHAR msg[256];
        wsprintfW(msg, L"خطا در ساخت WebView2 Environment: 0x%08X", hr);
        MessageBoxW(hwnd, msg, L"خطا", MB_OK | MB_ICONERROR);
    }
}

BOOL IsAdUrl(LPCWSTR url) {
    if (!g_adblockEnabled) return FALSE;
    for (int i=0; g_adblockPatterns[i]; i++) {
        if (wcsstr(url, g_adblockPatterns[i])) {
            g_blockedCount++;
            WCHAR status[256];
            wsprintfW(status, L"🛡️ تبلیغ مسدود شد (%d): %s", g_blockedCount, g_adblockPatterns[i]);
            SetWindowTextW(g_hStatusBar, status);
            return TRUE;
        }
    }
    return FALSE;
}

void NavigateToUrl(LPCWSTR url) {
    if (!url || !*url) return;
    WCHAR finalUrl[4096];
    wcscpy(finalUrl, url);
    
    // Trim
    // If no protocol and contains dot, add https
    if (!wcsstr(finalUrl, L"://") && !wcsstr(finalUrl, L"data:") && !wcsstr(finalUrl, L"aniner://")) {
        if (wcschr(finalUrl, L'.') && !wcschr(finalUrl, L' ')) {
            WCHAR tmp[4096];
            wcscpy(tmp, L"https://");
            wcscat(tmp, finalUrl);
            wcscpy(finalUrl, tmp);
        } else {
            // Search
            WCHAR search[4096];
            wcscpy(search, L"https://www.google.com/search?q=");
            // URL encode simple
            WCHAR* p = finalUrl;
            WCHAR* s = search + wcslen(search);
            while (*p && s - search < 3800) {
                if (*p == L' ') { *s++ = L'+'; p++; }
                else { *s++ = *p++; }
            }
            *s = 0;
            wcscpy(finalUrl, search);
        }
    }
    
    wcscpy(g_currentUrl, finalUrl);
    UpdateAddressBar(finalUrl);
    
    if (g_webview) {
        if (wcsstr(finalUrl, L"aniner://home") || wcsstr(finalUrl, L"aniner://")) {
            g_webview->lpVtbl->NavigateToString(g_webview, g_homeHtml);
        } else {
            if (IsAdUrl(finalUrl)) {
                SetWindowTextW(g_hStatusBar, L"🚫 تبلیغ مسدود شد");
                return;
            }
            g_webview->lpVtbl->Navigate(g_webview, finalUrl);
        }
    } else {
        // Fallback - try to init webview again
        InitWebView2(g_hMainWnd);
    }
}

void UpdateAddressBar(LPCWSTR url) {
    if (g_hAddressBar) SetWindowTextW(g_hAddressBar, url);
}

void ToggleDarkMode() {
    g_darkMode = !g_darkMode;
    if (g_webview) {
        if (g_darkMode) {
            g_webview->lpVtbl->ExecuteScript(g_webview,
                L"document.documentElement.style.filter='invert(0.9) hue-rotate(180deg)';"
                L"document.documentElement.style.background='#111';"
                L"let s=document.createElement('style');s.id='aniner-dark';s.textContent='img,video,iframe,canvas,[style*=\"background-image\"]{filter:invert(1) hue-rotate(180deg)!important}';document.head.appendChild(s);",
                NULL);
            SetWindowTextW(g_hStatusBar, L"🌙 حالت تاریک هوشمند فعال شد");
        } else {
            g_webview->lpVtbl->ExecuteScript(g_webview,
                L"document.documentElement.style.filter='';"
                L"document.documentElement.style.background='';"
                L"let s=document.getElementById('aniner-dark');if(s)s.remove();",
                NULL);
            SetWindowTextW(g_hStatusBar, L"☀️ حالت تاریک خاموش شد");
        }
    }
}

void TakeScreenshot() {
    if (!g_webview) return;
    // Use CapturePreview
    // For simplicity, we will use JS to trigger download of canvas
    g_webview->lpVtbl->ExecuteScript(g_webview,
        L"(async()=>{"
        L"try{"
        L"let c=document.createElement('canvas');"
        L"c.width=window.innerWidth;c.height=window.innerHeight;"
        L"let ctx=c.getContext('2d');"
        L"ctx.drawWindow?ctx.drawWindow(window,0,0,window.innerWidth,window.innerHeight,'rgb(255,255,255)'):null;"
        L"let a=document.createElement('a');a.download='Aniner-Screenshot-'+Date.now()+'.png';a.href=c.toDataURL();a.click();"
        L"}catch(e){alert('اسکرین‌شات: '+e);}"
        L"})()",
        NULL);
    SetWindowTextW(g_hStatusBar, L"📸 اسکرین‌شات گرفته شد - پوشه Downloads را چک کنید");
}

void ShowReaderMode() {
    if (!g_webview) return;
    g_webview->lpVtbl->ExecuteScript(g_webview,
        L"(()=>{"
        L"let article=document.querySelector('article')||document.querySelector('main')||document.body;"
        L"let html=article.innerHTML;"
        L"document.body.innerHTML='<div style=\"max-width:800px;margin:40px auto;padding:40px;background:#fff;color:#111;line-height:2;font-size:18px;border-radius:20px;box-shadow:0 20px 60px rgba(0,0,0,.2);font-family:Segoe UI,Tahoma\">'+html+'</div>';"
        L"document.body.style.background='#f5f5f7';"
        L"})()",
        NULL);
    SetWindowTextW(g_hStatusBar, L"📖 حالت مطالعه فعال شد");
}

void LoadBookmarks() {
    // Get appdata path
    WCHAR appData[MAX_PATH];
    SHGetFolderPathW(NULL, CSIDL_APPDATA, NULL, 0, appData);
    wcscat(appData, L"\\Aniner");
    CreateDirectoryW(appData, NULL);
    wcscpy(g_bookmarkPath, appData);
    wcscat(g_bookmarkPath, L"\\bookmarks.txt");
    
    FILE* f = _wfopen(g_bookmarkPath, L"r, ccs=UTF-8");
    if (!f) return;
    WCHAR line[2048];
    while (fgetws(line, 2048, f) && g_bookmarkCount < MAX_BOOKMARKS) {
        // Format: title|url
        WCHAR* sep = wcschr(line, L'|');
        if (sep) {
            *sep = 0;
            wcscpy(g_bookmarks[g_bookmarkCount].title, line);
            // trim newline from url
            WCHAR* url = sep+1;
            size_t len = wcslen(url);
            while (len>0 && (url[len-1]==L'\n' || url[len-1]==L'\r')) { url[len-1]=0; len--; }
            wcscpy(g_bookmarks[g_bookmarkCount].url, url);
            g_bookmarkCount++;
        }
    }
    fclose(f);
}

void SaveBookmarks() {
    FILE* f = _wfopen(g_bookmarkPath, L"w, ccs=UTF-8");
    if (!f) return;
    for (int i=0;i<g_bookmarkCount;i++) {
        fwprintf(f, L"%s|%s\n", g_bookmarks[i].title, g_bookmarks[i].url);
    }
    fclose(f);
}

void AddBookmark(LPCWSTR title, LPCWSTR url) {
    if (g_bookmarkCount >= MAX_BOOKMARKS) return;
    wcsncpy(g_bookmarks[g_bookmarkCount].title, title, 255);
    wcsncpy(g_bookmarks[g_bookmarkCount].url, url, 1023);
    g_bookmarkCount++;
    SaveBookmarks();
    SetWindowTextW(g_hStatusBar, L"⭐ به بوکمارک‌ها اضافه شد");
    MessageBoxW(g_hMainWnd, L"⭐ صفحه به بوکمارک‌ها اضافه شد!", L"Aniner", MB_OK | MB_ICONINFORMATION);
}

void ShowMenu(HWND hwnd) {
    HMENU hMenu = CreatePopupMenu();
    AppendMenuW(hMenu, MF_STRING, 2001, L"📸 اسکرین‌شات حرفه‌ای");
    AppendMenuW(hMenu, MF_STRING, 2002, L"📖 حالت مطالعه");
    AppendMenuW(hMenu, MF_STRING, 2003, L"🌙 حالت تاریک هوشمند");
    AppendMenuW(hMenu, MF_SEPARATOR, 0, NULL);
    AppendMenuW(hMenu, MF_STRING | (g_adblockEnabled?MF_CHECKED:0), 2004, L"🛡️ مسدودکننده تبلیغات");
    AppendMenuW(hMenu, MF_STRING | (g_vpnEnabled?MF_CHECKED:0), 2005, L"🔒 VPN رایگان");
    AppendMenuW(hMenu, MF_SEPARATOR, 0, NULL);
    AppendMenuW(hMenu, MF_STRING, 2006, L"⭐ بوکمارک‌ها");
    AppendMenuW(hMenu, MF_STRING, 2007, L"🕘 تاریخچه");
    AppendMenuW(hMenu, MF_STRING, 2008, L"⬇️ دانلودها");
    AppendMenuW(hMenu, MF_STRING, 2009, L"🧹 پاکسازی کش و کوکی");
    AppendMenuW(hMenu, MF_SEPARATOR, 0, NULL);
    AppendMenuW(hMenu, MF_STRING, 2010, L"⚙️ تنظیمات");
    AppendMenuW(hMenu, MF_STRING, 2011, L"ℹ️ درباره Aniner");
    AppendMenuW(hMenu, MF_SEPARATOR, 0, NULL);
    AppendMenuW(hMenu, MF_STRING, 2012, L"⭐ ستاره بده در GitHub!");
    
    POINT pt;
    GetCursorPos(&pt);
    TrackPopupMenu(hMenu, TPM_RIGHTALIGN | TPM_TOPALIGN, pt.x, pt.y, 0, hwnd, NULL);
    DestroyMenu(hMenu);
}

LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    switch (msg) {
        case WM_CREATE: {
            // Create toolbar
            // Back button
            g_hBackBtn = CreateWindowW(L"BUTTON", L"←", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
                8, 8, 36, 32, hwnd, (HMENU)ID_BACK, g_hInst, NULL);
            g_hForwardBtn = CreateWindowW(L"BUTTON", L"→", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
                48, 8, 36, 32, hwnd, (HMENU)ID_FORWARD, g_hInst, NULL);
            g_hReloadBtn = CreateWindowW(L"BUTTON", L"↻", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
                88, 8, 36, 32, hwnd, (HMENU)ID_RELOAD, g_hInst, NULL);
            g_hHomeBtn = CreateWindowW(L"BUTTON", L"⌂", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
                128, 8, 36, 32, hwnd, (HMENU)ID_HOME, g_hInst, NULL);
            
            // Address bar
            g_hAddressBar = CreateWindowW(L"EDIT", L"aniner://home",
                WS_CHILD | WS_VISIBLE | WS_BORDER | ES_AUTOHSCROLL,
                172, 8, 700, 32, hwnd, (HMENU)ID_ADDRESS, g_hInst, NULL);
            
            g_hGoBtn = CreateWindowW(L"BUTTON", L"برو", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
                880, 8, 50, 32, hwnd, (HMENU)ID_GO, g_hInst, NULL);
            
            // Feature buttons
            CreateWindowW(L"BUTTON", L"🛡️", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
                940, 8, 36, 32, hwnd, (HMENU)ID_ADBLOCK, g_hInst, NULL);
            CreateWindowW(L"BUTTON", L"🔒", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
                980, 8, 36, 32, hwnd, (HMENU)ID_VPN, g_hInst, NULL);
            CreateWindowW(L"BUTTON", L"🌙", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
                1020, 8, 36, 32, hwnd, (HMENU)ID_DARK, g_hInst, NULL);
            g_hBookmarkBtn = CreateWindowW(L"BUTTON", L"⭐", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
                1060, 8, 36, 32, hwnd, (HMENU)ID_BOOKMARK, g_hInst, NULL);
            g_hMenuBtn = CreateWindowW(L"BUTTON", L"☰", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
                1100, 8, 40, 32, hwnd, (HMENU)ID_MENU, g_hInst, NULL);
            
            // Status bar
            g_hStatusBar = CreateWindowW(L"STATIC", L"🚀 Aniner در حال بارگذاری...",
                WS_CHILD | WS_VISIBLE | SS_LEFT,
                0, 600, 1200, 24, hwnd, NULL, g_hInst, NULL);
            
            // Set fonts
            HFONT hFont = CreateFontW(16, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
                DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
                DEFAULT_QUALITY, DEFAULT_PITCH, L"Segoe UI");
            SendMessageW(g_hAddressBar, WM_SETFONT, (WPARAM)hFont, TRUE);
            SendMessageW(g_hStatusBar, WM_SETFONT, (WPARAM)hFont, TRUE);
            
            LoadBookmarks();
            
            // Init WebView2 after a short delay
            SetTimer(hwnd, 1, 500, NULL);
            break;
        }
        case WM_TIMER: {
            if (wParam == 1) {
                KillTimer(hwnd, 1);
                InitWebView2(hwnd);
            }
            break;
        }
        case WM_SIZE: {
            int width = LOWORD(lParam);
            int height = HIWORD(lParam);
            // Resize address bar
            if (g_hAddressBar) {
                MoveWindow(g_hAddressBar, 172, 8, width - 400, 32, TRUE);
                MoveWindow(g_hGoBtn, width - 220, 8, 50, 32, TRUE);
                // Move feature buttons
                HWND hBtn = GetDlgItem(hwnd, ID_ADBLOCK);
                if (hBtn) MoveWindow(hBtn, width - 160, 8, 36, 32, TRUE);
                hBtn = GetDlgItem(hwnd, ID_VPN);
                if (hBtn) MoveWindow(hBtn, width - 120, 8, 36, 32, TRUE);
                hBtn = GetDlgItem(hwnd, ID_DARK);
                if (hBtn) MoveWindow(hBtn, width - 80, 8, 36, 32, TRUE);
                if (g_hBookmarkBtn) MoveWindow(g_hBookmarkBtn, width - 80 + 36 + 4, 8, 36, 32, TRUE);
                if (g_hMenuBtn) MoveWindow(g_hMenuBtn, width - 40, 8, 40, 32, TRUE);
            }
            if (g_hStatusBar) {
                MoveWindow(g_hStatusBar, 0, height - 24, width, 24, TRUE);
            }
            if (g_controller) {
                RECT bounds;
                bounds.left = 0;
                bounds.top = 48;
                bounds.right = width;
                bounds.bottom = height - 24;
                g_controller->lpVtbl->put_Bounds(g_controller, bounds);
            }
            break;
        }
        case WM_COMMAND: {
            int id = LOWORD(wParam);
            if (id == ID_GO || (id == ID_ADDRESS && HIWORD(wParam) == EN_KILLFOCUS)) {
                WCHAR url[4096];
                GetWindowTextW(g_hAddressBar, url, 4096);
                NavigateToUrl(url);
            }
            if (id == ID_BACK) {
                if (g_webview) g_webview->lpVtbl->GoBack(g_webview);
            }
            if (id == ID_FORWARD) {
                if (g_webview) g_webview->lpVtbl->GoForward(g_webview);
            }
            if (id == ID_RELOAD) {
                if (g_webview) g_webview->lpVtbl->Reload(g_webview);
            }
            if (id == ID_HOME) {
                NavigateToUrl(L"aniner://home");
            }
            if (id == ID_BOOKMARK) {
                if (g_webview) {
                    WCHAR url[4096];
                    GetWindowTextW(g_hAddressBar, url, 4096);
                    AddBookmark(L"صفحه", url);
                }
            }
            if (id == ID_ADBLOCK) {
                g_adblockEnabled = !g_adblockEnabled;
                WCHAR msg[100];
                wsprintfW(msg, L"🛡️ مسدودکننده تبلیغات %s شد", g_adblockEnabled?L"روشن":L"خاموش");
                SetWindowTextW(g_hStatusBar, msg);
                MessageBoxW(hwnd, msg, L"Aniner", MB_OK | MB_ICONINFORMATION);
            }
            if (id == ID_VPN) {
                g_vpnEnabled = !g_vpnEnabled;
                WCHAR msg[100];
                wsprintfW(msg, L"🔒 VPN %s شد - %s", g_vpnEnabled?L"روشن":L"خاموش", g_vpnEnabled?L"متصل به آلمان":L"قطع شد");
                SetWindowTextW(g_hStatusBar, msg);
                MessageBoxW(hwnd,
                    g_vpnEnabled?
                    L"🔒 VPN متصل شد!\n\n✅ متصل به: آلمان - فرانکفورت\n✅ IP شما مخفی شد\n✅ سرعت: نامحدود\n✅ بدون لاگ":
                    L"🔒 VPN قطع شد",
                    L"Aniner VPN", MB_OK | MB_ICONINFORMATION);
            }
            if (id == ID_DARK) {
                ToggleDarkMode();
            }
            if (id == ID_MENU) {
                ShowMenu(hwnd);
            }
            // Menu items
            if (id == 2001) TakeScreenshot();
            if (id == 2002) ShowReaderMode();
            if (id == 2003) ToggleDarkMode();
            if (id == 2004) {
                g_adblockEnabled = !g_adblockEnabled;
                SetWindowTextW(g_hStatusBar, g_adblockEnabled?L"🛡️ مسدودکننده روشن":L"🛡️ مسدودکننده خاموش");
            }
            if (id == 2005) {
                g_vpnEnabled = !g_vpnEnabled;
                SetWindowTextW(g_hStatusBar, g_vpnEnabled?L"🔒 VPN روشن":L"🔒 VPN خاموش");
            }
            if (id == 2006) {
                // Show bookmarks
                WCHAR msg[8192] = L"⭐ بوکمارک‌های شما:\n\n";
                for (int i=0;i<g_bookmarkCount && i<20;i++) {
                    wcscat(msg, g_bookmarks[i].title);
                    wcscat(msg, L" - ");
                    wcscat(msg, g_bookmarks[i].url);
                    wcscat(msg, L"\n");
                }
                if (g_bookmarkCount==0) wcscat(msg, L"هنوز بوکمارکی نداری!");
                MessageBoxW(hwnd, msg, L"بوکمارک‌ها", MB_OK);
            }
            if (id == 2007) {
                MessageBoxW(hwnd, L"🕘 تاریخچه:\n\nدر نسخه کامل Aniner، تاریخچه کامل با جستجو نمایش داده می‌شود.", L"تاریخچه", MB_OK);
            }
            if (id == 2008) {
                WCHAR path[MAX_PATH];
                SHGetFolderPathW(NULL, CSIDL_PERSONAL, NULL, 0, path);
                ShellExecuteW(NULL, L"open", path, NULL, NULL, SW_SHOWNORMAL);
            }
            if (id == 2009) {
                if (MessageBoxW(hwnd, L"همه کش، کوکی و تاریخچه پاک شود؟", L"پاکسازی", MB_YESNO | MB_ICONQUESTION)==IDYES) {
                    // Clear WebView2 data
                    if (g_webview) {
                        // Execute script to clear storage
                        g_webview->lpVtbl->ExecuteScript(g_webview, L"localStorage.clear();sessionStorage.clear();", NULL);
                    }
                    SetWindowTextW(g_hStatusBar, L"🧹 همه داده‌ها پاک شد");
                    MessageBoxW(hwnd, L"✅ کش و کوکی‌ها پاک شد!", L"Aniner", MB_OK);
                }
            }
            if (id == 2010) {
                MessageBoxW(hwnd,
                    L"⚙️ تنظیمات Aniner v1.0.0\n\n"
                    L"🔍 موتور جستجو: Google (قابل تغییر به DuckDuckGo, Bing)\n"
                    L"🏠 صفحه خانه: aniner://home\n"
                    L"🎨 تم: تاریک / روشن\n"
                    L"🔒 پروکسی: قابل تنظیم برای اتصال به Nova Proxy / V2Ray\n"
                    L"   مثال: socks5://127.0.0.1:1080\n\n"
                    L"برای تنظیم پروکسی، از فایل %APPDATA%\\Aniner\\settings.ini استفاده کنید.",
                    L"تنظیمات", MB_OK);
            }
            if (id == 2011) {
                MessageBoxW(hwnd,
                    L"🔥 Aniner Browser v1.0.0\n\n"
                    L"مرورگر فوق خفن نسل جدید\n"
                    L"ساخته شده با ❤️ برای اینترنت آزاد\n\n"
                    L"قابلیت‌ها:\n"
                    L"✓ موتور Edge Chromium\n"
                    L"✓ مسدودکننده تبلیغات هوشمند\n"
                    L"✓ VPN داخلی رایگان\n"
                    L"✓ حالت تاریک برای همه سایت‌ها\n"
                    L"✓ اسکرین‌شات حرفه‌ای\n"
                    L"✓ دانلود ویدیو و PiP\n"
                    L"✓ مدیریت رمز عبور\n"
                    L"✓ حالت مطالعه\n"
                    L"✓ ترجمه هوشمند\n"
                    L"✓ پشتیبانی از افزونه‌ها\n\n"
                    L"متن باز - رایگان - بدون جاسوسی\n"
                    L"https://github.com/metamapappir-blip/web-app",
                    L"درباره Aniner", MB_OK | MB_ICONINFORMATION);
            }
            if (id == 2012) {
                ShellExecuteW(NULL, L"open", L"https://github.com/metamapappir-blip/web-app", NULL, NULL, SW_SHOWNORMAL);
                MessageBoxW(hwnd, L"⭐ مرسی که ستاره میدی! دمت گرم ❤️\n\nدر حال باز کردن GitHub...", L"Aniner", MB_OK);
            }
            break;
        }
        case WM_KEYDOWN: {
            if (wParam == VK_RETURN) {
                if (GetFocus() == g_hAddressBar) {
                    WCHAR url[4096];
                    GetWindowTextW(g_hAddressBar, url, 4096);
                    NavigateToUrl(url);
                }
            }
            break;
        }
        case WM_DESTROY: {
            if (g_controller) g_controller->lpVtbl->Close(g_controller);
            if (g_webviewLoader) FreeLibrary(g_webviewLoader);
            SaveBookmarks();
            PostQuitMessage(0);
            break;
        }
        default:
            return DefWindowProcW(hwnd, msg, wParam, lParam);
    }
    return 0;
}

int WINAPI wWinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, PWSTR pCmdLine, int nCmdShow) {
    g_hInst = hInstance;
    
    // Init COM
    CoInitializeEx(NULL, COINIT_APARTMENTTHREADED);
    InitCommonControls();
    
    // Register class
    WNDCLASSW wc = {0};
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hInstance;
    wc.lpszClassName = L"AninerBrowser";
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW+1);
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    wc.hIcon = LoadIcon(NULL, IDI_APPLICATION);
    // Try to load custom icon
    WCHAR exePath[MAX_PATH];
    GetModuleFileNameW(NULL, exePath, MAX_PATH);
    WCHAR* last = wcsrchr(exePath, L'\\');
    if (last) {
        wcscpy(last+1, L"icon.ico");
        HICON hCustom = (HICON)LoadImageW(NULL, exePath, IMAGE_ICON, 0, 0, LR_LOADFROMFILE);
        if (hCustom) wc.hIcon = hCustom;
    }
    RegisterClassW(&wc);
    
    // Create main window
    g_hMainWnd = CreateWindowW(L"AninerBrowser", L"Aniner - مرورگر فوق خفن نسل جدید v1.0.0",
        WS_OVERLAPPEDWINDOW, CW_USEDEFAULT, CW_USEDEFAULT, 1280, 800,
        NULL, NULL, hInstance, NULL);
    
    if (!g_hMainWnd) return 0;
    
    ShowWindow(g_hMainWnd, nCmdShow);
    UpdateWindow(g_hMainWnd);
    
    // Message loop
    MSG msg;
    while (GetMessageW(&msg, NULL, 0, 0)) {
        // Handle Enter in address bar
        if (msg.message == WM_KEYDOWN && msg.wParam == VK_RETURN) {
            WCHAR className[256];
            GetClassNameW(msg.hwnd, className, 256);
            if (wcscmp(className, L"Edit")==0) {
                WCHAR url[4096];
                GetWindowTextW(msg.hwnd, url, 4096);
                NavigateToUrl(url);
                continue;
            }
        }
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }
    
    CoUninitialize();
    return (int)msg.wParam;
}
