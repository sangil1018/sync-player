const { app, BrowserWindow, Menu, shell, nativeTheme, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const { pathToFileURL } = require('url');

nativeTheme.themeSource = 'dark';

function createWindow() {
  const win = new BrowserWindow({
    width: 1080, height: 780, minWidth: 420, minHeight: 560,
    backgroundColor: '#0d0e11',
    title: 'Sync Player',
    icon: path.join(__dirname, '..', 'build', 'icon.png'),
    autoHideMenuBar: true,
    webPreferences: { preload: path.join(__dirname, 'preload.js'), contextIsolation: true, sandbox: true, autoplayPolicy: 'no-user-gesture-required', spellcheck: false }
  });
  Menu.setApplicationMenu(process.platform === 'darwin' ? Menu.buildFromTemplate([
    { role: 'appMenu' }, { role: 'editMenu' }, { role: 'viewMenu' }, { role: 'windowMenu' }
  ]) : null);
  win.loadFile(path.join(__dirname, '..', 'www', 'index.html'));
  // 외부 링크는 기본 브라우저로
  win.webContents.setWindowOpenHandler(({ url }) => { shell.openExternal(url); return { action: 'deny' }; });
  win.webContents.on('will-navigate', (e, url) => { if (!url.startsWith('file://')) { e.preventDefault(); shell.openExternal(url); } });
}

/* ---- 같은 이름 파일 자동 연결용 (고른 파일과 같은 폴더의 오디오/자막만, 읽기 전용) ---- */
const AUDIO_RE = /\.(mp3|m4a|wav|aac|ogg|flac|mp4|webm|opus|m4b|mov|mkv)$/i;
const SUB_RE = /\.(json|srt|vtt)$/i;
const MAX_SUB_BYTES = 20 * 1024 * 1024;
const okPath = (p) => typeof p === 'string' && path.isAbsolute(p);
const fromApp = (e) => !e.senderFrame || e.senderFrame.url.startsWith('file://');

ipcMain.handle('sn:list', async (e, p) => {
  if (!fromApp(e) || !okPath(p)) return [];
  const dir = path.dirname(p);
  try {
    const ents = await fs.promises.readdir(dir, { withFileTypes: true });
    return ents.filter((d) => d.isFile() && (AUDIO_RE.test(d.name) || SUB_RE.test(d.name)))
      .map((d) => ({ name: d.name, path: path.join(dir, d.name) }));
  } catch (err) { return []; }
});
ipcMain.handle('sn:text', async (e, p) => {
  if (!fromApp(e) || !okPath(p) || !SUB_RE.test(p)) throw new Error('not allowed');
  const st = await fs.promises.stat(p);
  if (st.size > MAX_SUB_BYTES) throw new Error('file too large');
  return fs.promises.readFile(p, 'utf8');
});
ipcMain.handle('sn:url', (e, p) => {
  if (!fromApp(e) || !okPath(p) || !AUDIO_RE.test(p)) throw new Error('not allowed');
  return pathToFileURL(p).href;
});

const lock = app.requestSingleInstanceLock();
if (!lock) app.quit();
else {
  app.whenReady().then(() => {
    createWindow();
    app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
  });
  app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
}
