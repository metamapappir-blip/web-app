#define UNICODE
#define _UNICODE
#include <windows.h>
#include <shlobj.h>
#include <shlwapi.h>
#include <stdio.h>

#pragma comment(lib, "ole32.lib")
#pragma comment(lib, "shell32.lib")
#pragma comment(lib, "shlwapi.lib")

BOOL CreateShortcut(LPCWSTR target, LPCWSTR shortcutPath, LPCWSTR description, LPCWSTR iconPath) {
    IShellLinkW* psl = NULL;
    IPersistFile* ppf = NULL;
    HRESULT hr = CoCreateInstance(&CLSID_ShellLink, NULL, CLSCTX_INPROC_SERVER, &IID_IShellLinkW, (void**)&psl);
    if (FAILED(hr)) return FALSE;
    
    psl->lpVtbl->SetPath(psl, target);
    psl->lpVtbl->SetDescription(psl, description);
    psl->lpVtbl->SetWorkingDirectory(psl, target);
    // Set icon
    if (iconPath) psl->lpVtbl->SetIconLocation(psl, iconPath, 0);
    
    hr = psl->lpVtbl->QueryInterface(psl, &IID_IPersistFile, (void**)&ppf);
    if (SUCCEEDED(hr)) {
        hr = ppf->lpVtbl->Save(ppf, shortcutPath, TRUE);
        ppf->lpVtbl->Release(ppf);
    }
    psl->lpVtbl->Release(psl);
    return SUCCEEDED(hr);
}

int WINAPI wWinMain(HINSTANCE hInst, HINSTANCE hPrev, PWSTR cmdLine, int show) {
    CoInitialize(NULL);
    
    WCHAR exePath[MAX_PATH];
    GetModuleFileNameW(NULL, exePath, MAX_PATH);
    WCHAR* lastSlash = wcsrchr(exePath, L'\\');
    WCHAR currentDir[MAX_PATH];
    if (lastSlash) {
        wcsncpy(currentDir, exePath, lastSlash - exePath);
        currentDir[lastSlash - exePath] = 0;
    } else {
        GetCurrentDirectoryW(MAX_PATH, currentDir);
    }
    
    // Show welcome
    int res = MessageBoxW(NULL,
        L"🔥 به نصب Aniner Browser خوش آمدید!\n\n"
        L"این نصب کننده:\n"
        L"✓ Aniner را در Program Files نصب می‌کند\n"
        L"✓ آیکون روی دسکتاپ می‌سازد\n"
        L"✓ آیکون در منوی استارت می‌سازد\n"
        L"✓ WebView2 Runtime را چک می‌کند\n\n"
        L"ادامه می‌دهید؟",
        L"Aniner Browser - نصب",
        MB_YESNO | MB_ICONQUESTION);
    
    if (res != IDYES) {
        CoUninitialize();
        return 0;
    }
    
    // Get Program Files path
    WCHAR programFiles[MAX_PATH];
    SHGetFolderPathW(NULL, CSIDL_PROGRAM_FILES, NULL, 0, programFiles);
    wcscat(programFiles, L"\\Aniner");
    CreateDirectoryW(programFiles, NULL);
    
    // Copy files
    WCHAR srcExe[MAX_PATH], dstExe[MAX_PATH];
    wsprintfW(srcExe, L"%s\\Aniner.exe", currentDir);
    wsprintfW(dstExe, L"%s\\Aniner.exe", programFiles);
    
    // If src doesn't exist (installer in same dir as exe), try current exe dir
    if (!PathFileExistsW(srcExe)) {
        // The installer itself might be Aniner.exe? Check if we are portable
        // For portable, just create shortcut to current exe
        wcscpy(srcExe, exePath);
        wcscpy(dstExe, exePath); // Don't copy if portable
    }
    
    if (wcscmp(srcExe, dstExe) != 0) {
        CopyFileW(srcExe, dstExe, FALSE);
        
        // Copy WebView2Loader.dll
        WCHAR srcDll[MAX_PATH], dstDll[MAX_PATH];
        wsprintfW(srcDll, L"%s\\WebView2Loader.dll", currentDir);
        wsprintfW(dstDll, L"%s\\WebView2Loader.dll", programFiles);
        if (PathFileExistsW(srcDll)) CopyFileW(srcDll, dstDll, FALSE);
        
        // Copy icon
        WCHAR srcIcon[MAX_PATH], dstIcon[MAX_PATH];
        wsprintfW(srcIcon, L"%s\\icon.ico", currentDir);
        wsprintfW(dstIcon, L"%s\\icon.ico", programFiles);
        if (PathFileExistsW(srcIcon)) CopyFileW(srcIcon, dstIcon, FALSE);
    } else {
        // Portable mode - dst is same as src
        wcscpy(programFiles, currentDir);
        wsprintfW(dstExe, L"%s\\Aniner.exe", programFiles);
    }
    
    // Create desktop shortcut
    WCHAR desktop[MAX_PATH];
    SHGetFolderPathW(NULL, CSIDL_DESKTOP, NULL, 0, desktop);
    WCHAR shortcutPath[MAX_PATH];
    wsprintfW(shortcutPath, L"%s\\Aniner Browser.lnk", desktop);
    
    WCHAR iconPath[MAX_PATH];
    wsprintfW(iconPath, L"%s\\icon.ico", programFiles);
    if (!PathFileExistsW(iconPath)) wcscpy(iconPath, dstExe);
    
    if (CreateShortcut(dstExe, shortcutPath, L"Aniner - مرورگر فوق خفن نسل جدید", iconPath)) {
        // Success
    }
    
    // Create start menu shortcut
    WCHAR startMenu[MAX_PATH];
    SHGetFolderPathW(NULL, CSIDL_PROGRAMS, NULL, 0, startMenu);
    wcscat(startMenu, L"\\Aniner");
    CreateDirectoryW(startMenu, NULL);
    WCHAR startShortcut[MAX_PATH];
    wsprintfW(startShortcut, L"%s\\Aniner Browser.lnk", startMenu);
    CreateShortcut(dstExe, startShortcut, L"Aniner Browser", iconPath);
    
    // Check WebView2 Runtime
    HKEY hKey;
    BOOL webView2Installed = FALSE;
    if (RegOpenKeyExW(HKEY_LOCAL_MACHINE, L"SOFTWARE\\WOW6432Node\\Microsoft\\EdgeUpdate\\Clients\\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}", 0, KEY_READ, &hKey) == ERROR_SUCCESS) {
        webView2Installed = TRUE;
        RegCloseKey(hKey);
    }
    if (RegOpenKeyExW(HKEY_LOCAL_MACHINE, L"SOFTWARE\\Microsoft\\EdgeUpdate\\Clients\\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}", 0, KEY_READ, &hKey) == ERROR_SUCCESS) {
        webView2Installed = TRUE;
        RegCloseKey(hKey);
    }
    
    WCHAR msg[1024];
    if (webView2Installed) {
        wsprintfW(msg,
            L"✅ نصب Aniner با موفقیت انجام شد!\n\n"
            L"📁 محل نصب: %s\n"
            L"🖥️ آیکون روی دسکتاپ ساخته شد\n"
            L"📋 آیکون در منوی استارت ساخته شد\n\n"
            L"آیا می‌خواهید Aniner را اجرا کنید؟",
            programFiles);
    } else {
        wsprintfW(msg,
            L"✅ نصب Aniner انجام شد اما WebView2 Runtime یافت نشد!\n\n"
            L"برای اجرای Aniner باید Microsoft Edge WebView2 Runtime را نصب کنید.\n"
            L"آیا می‌خواهید صفحه دانلود WebView2 باز شود؟\n\n"
            L"📁 محل نصب: %s\n"
            L"🖥️ آیکون روی دسکتاپ ساخته شد",
            programFiles);
    }
    
    int run = MessageBoxW(NULL, msg, L"Aniner - نصب کامل شد", MB_YESNO | MB_ICONINFORMATION);
    if (run == IDYES) {
        if (webView2Installed) {
            ShellExecuteW(NULL, L"open", dstExe, NULL, NULL, SW_SHOWNORMAL);
        } else {
            ShellExecuteW(NULL, L"open", L"https://developer.microsoft.com/en-us/microsoft-edge/webview2/", NULL, NULL, SW_SHOWNORMAL);
        }
    }
    
    CoUninitialize();
    return 0;
}
