package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"runtime"
	"strings"
	"sync"
	"syscall"
	"time"
	"unsafe"
)

const (
	version = "1.0.2.7"

	className  = "SlayTheStarCraftLauncherWindow"
	windowName = "Slay the StarCraft"

	wmCreate          = 0x0001
	wmDestroy         = 0x0002
	wmClose           = 0x0010
	wmCommand         = 0x0111
	wmTimer           = 0x0113
	wmSetFont         = 0x0030
	wmCtlColorStatic  = 0x0138
	wmAppDownloadDone = 0x8001
	wmAppLaunchDone   = 0x8002

	wsOverlappedWindow = 0x00CF0000
	wsVisible          = 0x10000000
	wsChild            = 0x40000000
	wsDisabled         = 0x08000000
	bsPushButton       = 0x00000000
	ssLeft             = 0x00000000
	swShow             = 5
	cwUseDefault       = ^uintptr(0x7fffffff)

	idDownload = 1001
	idLaunch   = 1002
	idLog      = 1003
	idSC2      = 1004

	colorWindow    = 5
	defaultGuiFont = 17
	transparent    = 1

	messageBoxError = 0x10
	messageBoxInfo  = 0x40

	bifReturnOnlyFSDirs = 0x0001
	bifNewDialogStyle   = 0x0040
)

type point struct {
	X int32
	Y int32
}

type msg struct {
	Hwnd    syscall.Handle
	Message uint32
	WParam  uintptr
	LParam  uintptr
	Time    uint32
	Pt      point
}

type wndClassEx struct {
	CbSize        uint32
	Style         uint32
	LpfnWndProc   uintptr
	CbClsExtra    int32
	CbWndExtra    int32
	HInstance     syscall.Handle
	HIcon         syscall.Handle
	HCursor       syscall.Handle
	HbrBackground syscall.Handle
	LpszMenuName  *uint16
	LpszClassName *uint16
	HIconSm       syscall.Handle
}

type browseInfo struct {
	HwndOwner      uintptr
	PidlRoot       uintptr
	PszDisplayName *uint16
	LpszTitle      *uint16
	UlFlags        uint32
	Lpfn           uintptr
	LParam         uintptr
	IImage         int32
}

type installConfig struct {
	FormatVersion int    `json:"format_version"`
	SlayVersion   string `json:"slay_version"`
	RuntimeMode   string `json:"runtime_mode"`
	SC2Root       string `json:"sc2_root"`
}

type runtimeInfo struct {
	SlayVersion    string `json:"slay_version"`
	PythonVersion  string `json:"python_version"`
	ArchipelagoRef string `json:"archipelago_ref"`
	SC2DataAPI     string `json:"sc2_data_api"`
}

var (
	user32   = syscall.NewLazyDLL("user32.dll")
	kernel32 = syscall.NewLazyDLL("kernel32.dll")
	shell32  = syscall.NewLazyDLL("shell32.dll")
	ole32    = syscall.NewLazyDLL("ole32.dll")
	gdi32    = syscall.NewLazyDLL("gdi32.dll")

	procRegisterClassExW    = user32.NewProc("RegisterClassExW")
	procCreateWindowExW     = user32.NewProc("CreateWindowExW")
	procDefWindowProcW      = user32.NewProc("DefWindowProcW")
	procShowWindow          = user32.NewProc("ShowWindow")
	procUpdateWindow        = user32.NewProc("UpdateWindow")
	procGetMessageW         = user32.NewProc("GetMessageW")
	procTranslateMessage    = user32.NewProc("TranslateMessage")
	procDispatchMessageW    = user32.NewProc("DispatchMessageW")
	procPostQuitMessage     = user32.NewProc("PostQuitMessage")
	procDestroyWindow       = user32.NewProc("DestroyWindow")
	procSendMessageW        = user32.NewProc("SendMessageW")
	procSetWindowTextW      = user32.NewProc("SetWindowTextW")
	procEnableWindow        = user32.NewProc("EnableWindow")
	procSetTimer            = user32.NewProc("SetTimer")
	procPostMessageW        = user32.NewProc("PostMessageW")
	procMessageBoxW         = user32.NewProc("MessageBoxW")
	procSetTextColor        = gdi32.NewProc("SetTextColor")
	procSetBkMode           = gdi32.NewProc("SetBkMode")
	procGetStockObject      = gdi32.NewProc("GetStockObject")
	procGetSysColorBrush    = user32.NewProc("GetSysColorBrush")
	procLoadCursorW         = user32.NewProc("LoadCursorW")
	procGetModuleHandleW    = kernel32.NewProc("GetModuleHandleW")
	procSHBrowseForFolderW  = shell32.NewProc("SHBrowseForFolderW")
	procSHGetPathFromIDList = shell32.NewProc("SHGetPathFromIDListW")
	procCoTaskMemFree       = ole32.NewProc("CoTaskMemFree")
)

var (
	rootDir     string
	mainWindow  syscall.Handle
	statusLabel syscall.Handle
	detailLabel syscall.Handle
	sc2Label    syscall.Handle
	downloadBtn syscall.Handle
	launchBtn   syscall.Handle
	logBtn      syscall.Handle
	sc2Btn      syscall.Handle
	guiFont     uintptr

	stateMu           sync.Mutex
	downloadRunning   bool
	launchRunning     bool
	lastDownloadCode  int
	lastLaunchText    string
	firstRefresh      = true
	downloadStartedAt time.Time
)

func utf16Ptr(s string) *uint16 {
	p, _ := syscall.UTF16PtrFromString(s)
	return p
}

func loword(v uintptr) uint16 { return uint16(v & 0xffff) }

func rgb(r, g, b byte) uintptr {
	return uintptr(uint32(r) | uint32(g)<<8 | uint32(b)<<16)
}

func messageBox(title, body string, flags uintptr) {
	procMessageBoxW.Call(
		uintptr(mainWindow),
		uintptr(unsafe.Pointer(utf16Ptr(body))),
		uintptr(unsafe.Pointer(utf16Ptr(title))),
		flags,
	)
}

func setText(hwnd syscall.Handle, s string) {
	procSetWindowTextW.Call(uintptr(hwnd), uintptr(unsafe.Pointer(utf16Ptr(s))))
}

func enable(hwnd syscall.Handle, yes bool) {
	value := uintptr(0)
	if yes {
		value = 1
	}
	procEnableWindow.Call(uintptr(hwnd), value)
}

func createControl(class, text string, style uintptr, x, y, w, h int32, parent syscall.Handle, id int) syscall.Handle {
	hwnd, _, _ := procCreateWindowExW.Call(
		0,
		uintptr(unsafe.Pointer(utf16Ptr(class))),
		uintptr(unsafe.Pointer(utf16Ptr(text))),
		style,
		uintptr(x), uintptr(y), uintptr(w), uintptr(h),
		uintptr(parent), uintptr(id), 0, 0,
	)
	if hwnd != 0 && guiFont != 0 {
		procSendMessageW.Call(hwnd, wmSetFont, guiFont, 1)
	}
	return syscall.Handle(hwnd)
}

func isDir(path string) bool {
	st, err := os.Stat(path)
	return err == nil && st.IsDir()
}

func isFile(path string) bool {
	st, err := os.Stat(path)
	return err == nil && !st.IsDir()
}

func validSC2Root(candidate string) bool {
	if candidate == "" || !isDir(candidate) {
		return false
	}
	return isDir(filepath.Join(candidate, "Versions")) || isFile(filepath.Join(candidate, "Support64", "SC2Switcher_x64.exe"))
}

func sc2FromExecuteInfo() string {
	home, err := os.UserHomeDir()
	if err != nil {
		return ""
	}
	paths := []string{
		filepath.Join(home, "Documents", "StarCraft II", "ExecuteInfo.txt"),
		filepath.Join(home, "OneDrive", "Documents", "StarCraft II", "ExecuteInfo.txt"),
	}
	re := regexp.MustCompile(`(?i)=\s*(.+?)Versions`)
	for _, path := range paths {
		data, err := os.ReadFile(path)
		if err != nil {
			continue
		}
		match := re.FindStringSubmatch(string(data))
		if len(match) < 2 {
			continue
		}
		candidate := strings.Trim(strings.TrimSpace(match[1]), `"`)
		candidate = strings.TrimRight(candidate, `\\/`)
		if validSC2Root(candidate) {
			abs, _ := filepath.Abs(candidate)
			return abs
		}
	}
	return ""
}

func loadInstallConfig() installConfig {
	var cfg installConfig
	data, err := os.ReadFile(filepath.Join(rootDir, "Config", "slay_install.json"))
	if err == nil {
		_ = json.Unmarshal(data, &cfg)
	}
	return cfg
}

func detectSC2Root() string {
	cfg := loadInstallConfig()
	if validSC2Root(cfg.SC2Root) {
		abs, _ := filepath.Abs(cfg.SC2Root)
		return abs
	}
	if env := strings.TrimSpace(os.Getenv("SC2PATH")); validSC2Root(env) {
		abs, _ := filepath.Abs(env)
		return abs
	}
	if fromInfo := sc2FromExecuteInfo(); fromInfo != "" {
		return fromInfo
	}
	candidates := []string{
		`C:\Program Files (x86)\StarCraft II`,
		`C:\Program Files\StarCraft II`,
		`C:\Games\StarCraft II`,
	}
	if pf86 := os.Getenv("ProgramFiles(x86)"); pf86 != "" {
		candidates = append([]string{filepath.Join(pf86, "StarCraft II")}, candidates...)
	}
	if pf := os.Getenv("ProgramFiles"); pf != "" {
		candidates = append([]string{filepath.Join(pf, "StarCraft II")}, candidates...)
	}
	for _, candidate := range candidates {
		if validSC2Root(candidate) {
			abs, _ := filepath.Abs(candidate)
			return abs
		}
	}
	return ""
}

func browseForSC2() string {
	var display [260]uint16
	bi := browseInfo{
		HwndOwner:      uintptr(mainWindow),
		PszDisplayName: &display[0],
		LpszTitle:      utf16Ptr("Select your StarCraft II folder (the folder containing Versions)."),
		UlFlags:        bifReturnOnlyFSDirs | bifNewDialogStyle,
	}
	pidl, _, _ := procSHBrowseForFolderW.Call(uintptr(unsafe.Pointer(&bi)))
	if pidl == 0 {
		return ""
	}
	defer procCoTaskMemFree.Call(pidl)
	var path [32768]uint16
	ok, _, _ := procSHGetPathFromIDList.Call(pidl, uintptr(unsafe.Pointer(&path[0])))
	if ok == 0 {
		return ""
	}
	candidate := syscall.UTF16ToString(path[:])
	if !validSC2Root(candidate) {
		messageBox(windowName, "That folder is not a valid StarCraft II installation. Select the folder containing the Versions directory.", messageBoxError)
		return ""
	}
	abs, _ := filepath.Abs(candidate)
	return abs
}

func runtimeDataReady() (bool, string) {
	markerPath := filepath.Join(rootDir, "Runtime", "runtime.json")
	data, err := os.ReadFile(markerPath)
	if err != nil {
		return false, "Required data is not downloaded yet."
	}
	data = []byte(strings.TrimPrefix(string(data), "\ufeff"))
	var info runtimeInfo
	if json.Unmarshal(data, &info) != nil || info.SlayVersion != version {
		return false, "Required data needs to be downloaded/updated for this Slay version."
	}
	required := []string{
		filepath.Join(rootDir, "Runtime", "Python", "python.exe"),
		filepath.Join(rootDir, "Runtime", "Archipelago", "Generate.py"),
		filepath.Join(rootDir, "Runtime", "Archipelago", "MultiServer.py"),
		filepath.Join(rootDir, "Runtime", "Archipelago", "SlayTheStarCraftLauncher.py"),
	}
	for _, path := range required {
		if !isFile(path) {
			return false, "Required data is incomplete. Click Download Data to repair it."
		}
	}
	sc2Root := detectSC2Root()
	if !validSC2Root(sc2Root) {
		return false, "StarCraft II was not found. Select its folder, then click Download Data."
	}
	if !isFile(filepath.Join(sc2Root, "Mods", "ArchipelagoTriggers.SC2Mod", "Base.SC2Data", "APRogue.galaxy")) {
		return false, "Slay's StarCraft II data is missing. Click Download Data to repair it."
	}
	return true, "Required data is ready."
}

func downloadStatusPath() string {
	return filepath.Join(rootDir, "Runtime", "Logs", "download-status.txt")
}
func downloadLogPath() string { return filepath.Join(rootDir, "Runtime", "Logs", "data-download.log") }
func downloadErrorPath() string {
	return filepath.Join(rootDir, "Runtime", "Logs", "data-download-error.txt")
}
func bootstrapProcessLogPath() string {
	return filepath.Join(rootDir, "Runtime", "Logs", "bootstrap-process.log")
}
func launcherLogPath() string { return filepath.Join(rootDir, "Runtime", "Logs", "SlayLauncher.log") }

func readTrimmed(path string) string {
	data, err := os.ReadFile(path)
	if err != nil {
		return ""
	}
	return strings.TrimSpace(strings.TrimPrefix(string(data), "\ufeff"))
}

func appendLauncherLog(format string, args ...any) {
	path := launcherLogPath()
	_ = os.MkdirAll(filepath.Dir(path), 0o755)
	f, err := os.OpenFile(path, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		return
	}
	defer f.Close()
	_, _ = fmt.Fprintf(f, "[%s] %s\r\n", time.Now().Format(time.RFC3339), fmt.Sprintf(format, args...))
}

func startDataDownload() {
	stateMu.Lock()
	if downloadRunning {
		stateMu.Unlock()
		return
	}
	downloadRunning = true
	lastDownloadCode = 0
	downloadStartedAt = time.Now()
	stateMu.Unlock()

	sc2Root := detectSC2Root()
	if !validSC2Root(sc2Root) {
		sc2Root = browseForSC2()
	}
	if !validSC2Root(sc2Root) {
		stateMu.Lock()
		downloadRunning = false
		downloadStartedAt = time.Time{}
		stateMu.Unlock()
		refreshUI()
		return
	}

	_ = os.MkdirAll(filepath.Join(rootDir, "Runtime", "Logs"), 0o755)
	_ = os.Remove(downloadErrorPath())
	_ = os.WriteFile(downloadStatusPath(), []byte("Preparing data download\r\n"), 0o644)

	script := filepath.Join(rootDir, "Tools", "bootstrap_slay_runtime.ps1")
	if !isFile(script) {
		stateMu.Lock()
		downloadRunning = false
		downloadStartedAt = time.Time{}
		stateMu.Unlock()
		messageBox(windowName, "The package is missing Tools\\bootstrap_slay_runtime.ps1. Re-extract the complete Slay ZIP.", messageBoxError)
		refreshUI()
		return
	}

	enable(downloadBtn, false)
	enable(launchBtn, false)
	setText(statusLabel, "Downloading required data...")
	setText(detailLabel, "Please leave this launcher open while downloading data. This may take several minutes.")

	go func(sc2 string) {
		args := []string{
			"-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden",
			"-File", script,
			"-Sc2Root", sc2,
			"-NonInteractive",
			"-LogPath", downloadLogPath(),
			"-StatusPath", downloadStatusPath(),
			"-ErrorPath", downloadErrorPath(),
		}
		cmd := exec.Command("powershell.exe", args...)
		cmd.Dir = rootDir
		cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true, CreationFlags: 0x08000000}
		bootstrapLog, logErr := os.OpenFile(bootstrapProcessLogPath(), os.O_CREATE|os.O_TRUNC|os.O_WRONLY, 0o644)
		if logErr == nil {
			defer bootstrapLog.Close()
			cmd.Stdout = bootstrapLog
			cmd.Stderr = bootstrapLog
		}
		err := cmd.Run()
		code := 0
		if err != nil {
			code = 1
			if exitErr, ok := err.(*exec.ExitError); ok {
				code = exitErr.ExitCode()
			}
		}
		stateMu.Lock()
		downloadRunning = false
		downloadStartedAt = time.Time{}
		lastDownloadCode = code
		stateMu.Unlock()
		procPostMessageW.Call(uintptr(mainWindow), wmAppDownloadDone, uintptr(code), 0)
	}(sc2Root)
}

func slayEnvironment(sc2Root string) []string {
	pythonExe := filepath.Join(rootDir, "Runtime", "Python", "python.exe")
	env := os.Environ()
	env = setEnv(env, "SLAY_LAUNCHER_MODE", "1")
	env = setEnv(env, "SLAY_PORTABLE_ROOT", rootDir)
	env = setEnv(env, "SKIP_REQUIREMENTS_UPDATE", "1")
	env = setEnv(env, "PYTHONNOUSERSITE", "1")
	env = setEnv(env, "PYTHONDONTWRITEBYTECODE", "1")
	env = setEnv(env, "PYTHONUTF8", "1")
	env = setEnv(env, "SLAY_MANAGED_SC2_DATA", "1")
	env = setEnv(env, "SC2PATH", sc2Root)
	env = setEnv(env, "KIVY_HOME", filepath.Join(rootDir, "Runtime", "KivyHome"))
	env = setEnv(env, "SLAY_LAUNCH_LOG", launcherLogPath())
	env = setEnv(env, "PATH", filepath.Dir(pythonExe)+";"+filepath.Join(filepath.Dir(pythonExe), "Scripts")+";"+os.Getenv("PATH"))
	return env
}

func setEnv(env []string, key, value string) []string {
	prefix := strings.ToUpper(key) + "="
	out := make([]string, 0, len(env)+1)
	for _, item := range env {
		if !strings.HasPrefix(strings.ToUpper(item), prefix) {
			out = append(out, item)
		}
	}
	return append(out, key+"="+value)
}

func tryAutoLaunchReadyClient() (bool, error) {
	ready, _ := runtimeDataReady()
	if !ready {
		return false, nil
	}
	sc2Root := detectSC2Root()
	if !validSC2Root(sc2Root) {
		return false, nil
	}

	pythonExe := filepath.Join(rootDir, "Runtime", "Python", "python.exe")
	apRoot := filepath.Join(rootDir, "Runtime", "Archipelago")
	entry := filepath.Join(apRoot, "SlayTheStarCraftLauncher.py")
	logFile, err := os.OpenFile(launcherLogPath(), os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		return false, fmt.Errorf("could not open SlayLauncher.log: %w", err)
	}
	defer logFile.Close()

	appendLauncherLog("Required data and StarCraft II detected; auto-launching Slay without native launcher window")
	appendLauncherLog("Portable root: %s", rootDir)
	appendLauncherLog("StarCraft II root: %s", sc2Root)
	cmd := exec.Command(pythonExe, entry)
	cmd.Dir = apRoot
	cmd.Env = slayEnvironment(sc2Root)
	cmd.Stdout = logFile
	cmd.Stderr = logFile
	cmd.SysProcAttr = &syscall.SysProcAttr{CreationFlags: 0x08000000}
	if err := cmd.Start(); err != nil {
		return false, fmt.Errorf("could not auto-launch Slay: %w", err)
	}
	appendLauncherLog("Auto-launched Python client PID %d", cmd.Process.Pid)

	finished := make(chan error, 1)
	go func() { finished <- cmd.Wait() }()
	select {
	case waitErr := <-finished:
		if waitErr == nil {
			return false, errors.New(`Slay closed during automatic startup; open Runtime\Logs\SlayLauncher.log for details`)
		}
		return false, fmt.Errorf("Slay exited during automatic startup: %w", waitErr)
	case <-time.After(4 * time.Second):
		appendLauncherLog("Python client remained alive for 4 seconds; automatic handoff complete and native launcher is exiting")
		return true, nil
	}
}

func launchSlay() {
	stateMu.Lock()
	if launchRunning {
		stateMu.Unlock()
		return
	}
	launchRunning = true
	lastLaunchText = ""
	stateMu.Unlock()

	ready, why := runtimeDataReady()
	if !ready {
		stateMu.Lock()
		launchRunning = false
		stateMu.Unlock()
		messageBox(windowName, why+"\n\nClick Download Data first.", messageBoxInfo)
		refreshUI()
		return
	}
	sc2Root := detectSC2Root()
	enable(launchBtn, false)
	setText(statusLabel, "Starting Slay the StarCraft...")
	setText(detailLabel, "The game launcher is starting from the private runtime in this folder.")

	go func() {
		pythonExe := filepath.Join(rootDir, "Runtime", "Python", "python.exe")
		apRoot := filepath.Join(rootDir, "Runtime", "Archipelago")
		entry := filepath.Join(apRoot, "SlayTheStarCraftLauncher.py")
		_ = os.MkdirAll(filepath.Join(rootDir, "Runtime", "Logs"), 0o755)
		logFile, err := os.OpenFile(launcherLogPath(), os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
		if err != nil {
			finishLaunch("Could not open SlayLauncher.log: "+err.Error(), 1)
			return
		}
		defer logFile.Close()
		appendLauncherLog("Slay the StarCraft v%s native lightweight launcher starting client", version)
		appendLauncherLog("Portable root: %s", rootDir)
		appendLauncherLog("StarCraft II root: %s", sc2Root)
		cmd := exec.Command(pythonExe, entry)
		cmd.Dir = apRoot
		cmd.Env = slayEnvironment(sc2Root)
		cmd.Stdout = logFile
		cmd.Stderr = logFile
		cmd.SysProcAttr = &syscall.SysProcAttr{CreationFlags: 0x08000000}
		if err := cmd.Start(); err != nil {
			finishLaunch("Could not start Slay: "+err.Error(), 1)
			return
		}
		appendLauncherLog("Started Python client PID %d", cmd.Process.Pid)
		finished := make(chan error, 1)
		go func() { finished <- cmd.Wait() }()
		select {
		case waitErr := <-finished:
			if waitErr == nil {
				finishLaunch("Slay closed during startup. Open the logs folder for details.", 1)
			} else {
				finishLaunch("Slay exited during startup: "+waitErr.Error(), 1)
			}
		case <-time.After(4 * time.Second):
			appendLauncherLog("Python client remained alive for 4 seconds; launcher handoff complete.")
			finishLaunch("Slay client started. If its window does not appear, click Open Logs.", 0)
		}
	}()
}

func finishLaunch(text string, code int) {
	stateMu.Lock()
	launchRunning = false
	lastLaunchText = text
	stateMu.Unlock()
	procPostMessageW.Call(uintptr(mainWindow), wmAppLaunchDone, uintptr(code), 0)
}

func openLog() {
	path := filepath.Join(rootDir, "Runtime", "Logs")
	if err := os.MkdirAll(path, 0o755); err != nil {
		messageBox(windowName, "Could not create the logs folder: "+err.Error(), messageBoxError)
		return
	}
	cmd := exec.Command("explorer.exe", path)
	if err := cmd.Start(); err != nil {
		messageBox(windowName, "Could not open the logs folder: "+err.Error(), messageBoxError)
	}
}

func refreshUI() {
	sc2Root := detectSC2Root()
	if validSC2Root(sc2Root) {
		setText(sc2Label, "StarCraft II: "+sc2Root)
	} else {
		setText(sc2Label, "StarCraft II: not detected")
	}

	stateMu.Lock()
	downloading := downloadRunning
	launching := launchRunning
	launchText := lastLaunchText
	startedAt := downloadStartedAt
	stateMu.Unlock()

	if downloading {
		status := readTrimmed(downloadStatusPath())
		if status == "" {
			status = "Downloading required data..."
		}
		elapsed := ""
		if !startedAt.IsZero() {
			d := time.Since(startedAt).Round(time.Second)
			if d < 0 {
				d = 0
			}
			elapsed = fmt.Sprintf(" Elapsed: %s.", d.String())
		}
		setText(statusLabel, status)
		setText(detailLabel, "Please leave this launcher open while downloading data. This may take several minutes."+elapsed+" Files stay private to this Slay folder.")
		enable(downloadBtn, false)
		enable(launchBtn, false)
		enable(sc2Btn, false)
		return
	}

	ready, why := runtimeDataReady()
	setText(statusLabel, why)
	if ready {
		if launchText != "" {
			setText(detailLabel, launchText)
		} else {
			setText(detailLabel, "You can launch immediately. Download Data can also repair or refresh the private data later.")
		}
		enable(launchBtn, !launching)
		enable(downloadBtn, true)
	} else {
		setText(detailLabel, "Click Download Data. It downloads the private Python/Archipelago runtime and SC2 support data; nothing is installed globally, everything is installed in this folder.")
		enable(launchBtn, false)
		enable(downloadBtn, true)
	}
	enable(sc2Btn, !launching)
	enable(logBtn, true)
	firstRefresh = false
}

func wndProc(hwnd syscall.Handle, message uint32, wParam, lParam uintptr) uintptr {
	switch message {
	case wmCreate:
		mainWindow = hwnd
		guiFont, _, _ = procGetStockObject.Call(defaultGuiFont)
		createControl("STATIC", "Slay the StarCraft v"+version, wsChild|wsVisible|ssLeft, 24, 20, 540, 26, hwnd, 0)
		statusLabel = createControl("STATIC", "Checking required data...", wsChild|wsVisible|ssLeft, 24, 58, 540, 24, hwnd, 0)
		detailLabel = createControl("STATIC", "", wsChild|wsVisible|ssLeft, 24, 86, 540, 52, hwnd, 0)
		sc2Label = createControl("STATIC", "StarCraft II: checking...", wsChild|wsVisible|ssLeft, 24, 140, 540, 22, hwnd, 0)
		downloadBtn = createControl("BUTTON", "Download Data", wsChild|wsVisible|bsPushButton, 24, 182, 150, 36, hwnd, idDownload)
		launchBtn = createControl("BUTTON", "Launch Slay", wsChild|wsVisible|wsDisabled|bsPushButton, 186, 182, 130, 36, hwnd, idLaunch)
		sc2Btn = createControl("BUTTON", "Select SC2 Folder", wsChild|wsVisible|bsPushButton, 328, 182, 130, 36, hwnd, idSC2)
		logBtn = createControl("BUTTON", "Open Logs", wsChild|wsVisible|bsPushButton, 470, 182, 94, 36, hwnd, idLog)
		procSetTimer.Call(uintptr(hwnd), 1, 600, 0)
		refreshUI()
		return 0

	case wmCommand:
		switch int(loword(wParam)) {
		case idDownload:
			startDataDownload()
		case idLaunch:
			launchSlay()
		case idLog:
			openLog()
		case idSC2:
			if chosen := browseForSC2(); chosen != "" {
				cfg := installConfig{FormatVersion: 3, SlayVersion: version, RuntimeMode: "bootstrap", SC2Root: chosen}
				_ = os.MkdirAll(filepath.Join(rootDir, "Config"), 0o755)
				if data, err := json.MarshalIndent(cfg, "", "  "); err == nil {
					data = append(data, '\n')
					_ = os.WriteFile(filepath.Join(rootDir, "Config", "slay_install.json"), data, 0o644)
				}
				refreshUI()
			}
		}
		return 0

	case wmTimer:
		refreshUI()
		return 0

	case wmAppDownloadDone:
		refreshUI()
		code := int(wParam)
		if code != 0 {
			detail := readTrimmed(downloadErrorPath())
			logPath := downloadLogPath()
			if detail == "" {
				bootstrapDetail := readTrimmed(bootstrapProcessLogPath())
				if bootstrapDetail != "" {
					if len(bootstrapDetail) > 1400 {
						bootstrapDetail = bootstrapDetail[len(bootstrapDetail)-1400:]
					}
					detail = "The data bootstrap failed before its normal log could start:\n\n" + bootstrapDetail
					logPath = bootstrapProcessLogPath()
				} else {
					detail = "The data download failed before its normal log could start."
					logPath = bootstrapProcessLogPath()
				}
			}
			messageBox(windowName, detail+"\n\nLog: "+logPath, messageBoxError)
		}
		return 0

	case wmAppLaunchDone:
		if int(wParam) == 0 {
			procDestroyWindow.Call(uintptr(hwnd))
			return 0
		}
		refreshUI()
		stateMu.Lock()
		text := lastLaunchText
		stateMu.Unlock()
		if text == "" {
			text = "Slay failed to start."
		}
		messageBox(windowName, text+"\n\nLog: "+launcherLogPath(), messageBoxError)
		return 0

	case wmCtlColorStatic:
		hdc := wParam
		ctl := syscall.Handle(lParam)
		if ctl == statusLabel {
			ready, _ := runtimeDataReady()
			stateMu.Lock()
			downloading := downloadRunning
			stateMu.Unlock()
			if downloading {
				procSetTextColor.Call(hdc, rgb(160, 100, 0))
			} else if ready {
				procSetTextColor.Call(hdc, rgb(0, 120, 45))
			} else {
				procSetTextColor.Call(hdc, rgb(180, 70, 0))
			}
			procSetBkMode.Call(hdc, transparent)
			brush, _, _ := procGetSysColorBrush.Call(colorWindow)
			return brush
		}

	case wmClose:
		procDestroyWindow.Call(uintptr(hwnd))
		return 0

	case wmDestroy:
		procPostQuitMessage.Call(0)
		return 0
	}
	ret, _, _ := procDefWindowProcW.Call(uintptr(hwnd), uintptr(message), wParam, lParam)
	return ret
}

func run() error {
	exePath, err := os.Executable()
	if err != nil {
		return err
	}
	exePath, _ = filepath.Abs(exePath)
	rootDir = filepath.Dir(exePath)
	if !isFile(filepath.Join(rootDir, "Tools", "bootstrap_slay_runtime.ps1")) || !isDir(filepath.Join(rootDir, "Payload")) {
		return errors.New("this launcher is missing its Tools or Payload folder; re-extract the complete Slay ZIP")
	}
	_ = os.MkdirAll(filepath.Join(rootDir, "Runtime", "Logs"), 0o755)
	appendLauncherLog("Native lightweight launcher v%s opened", version)

	if launched, autoErr := tryAutoLaunchReadyClient(); launched {
		return nil
	} else if autoErr != nil {
		lastLaunchText = "Automatic launch failed: " + autoErr.Error() + ". Open Logs for details."
		appendLauncherLog("Automatic launch failed; falling back to native launcher: %v", autoErr)
	}

	hInstRaw, _, errCall := procGetModuleHandleW.Call(0)
	if hInstRaw == 0 {
		return fmt.Errorf("GetModuleHandleW failed: %v", errCall)
	}
	hInst := syscall.Handle(hInstRaw)
	cursor, _, _ := procLoadCursorW.Call(0, 32512)
	cls := wndClassEx{
		CbSize:        uint32(unsafe.Sizeof(wndClassEx{})),
		LpfnWndProc:   syscall.NewCallback(wndProc),
		HInstance:     hInst,
		HCursor:       syscall.Handle(cursor),
		HbrBackground: syscall.Handle(colorWindow + 1),
		LpszClassName: utf16Ptr(className),
	}
	atom, _, errCall := procRegisterClassExW.Call(uintptr(unsafe.Pointer(&cls)))
	if atom == 0 {
		return fmt.Errorf("RegisterClassExW failed: %v", errCall)
	}

	hwndRaw, _, errCall := procCreateWindowExW.Call(
		0,
		uintptr(unsafe.Pointer(utf16Ptr(className))),
		uintptr(unsafe.Pointer(utf16Ptr(windowName+" v"+version))),
		wsOverlappedWindow|wsVisible,
		cwUseDefault, cwUseDefault, 610, 300,
		0, 0, uintptr(hInst), 0,
	)
	if hwndRaw == 0 {
		return fmt.Errorf("CreateWindowExW failed: %v", errCall)
	}
	mainWindow = syscall.Handle(hwndRaw)
	procShowWindow.Call(hwndRaw, swShow)
	procUpdateWindow.Call(hwndRaw)

	var m msg
	for {
		ret, _, _ := procGetMessageW.Call(uintptr(unsafe.Pointer(&m)), 0, 0, 0)
		if int32(ret) == -1 {
			return errors.New("GetMessageW failed")
		}
		if ret == 0 {
			return nil
		}
		procTranslateMessage.Call(uintptr(unsafe.Pointer(&m)))
		procDispatchMessageW.Call(uintptr(unsafe.Pointer(&m)))
	}
}

func main() {
	runtime.LockOSThread()
	if err := run(); err != nil {
		messageBox(windowName, err.Error(), messageBoxError)
		os.Exit(2)
	}
}
