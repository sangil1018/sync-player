// 렌더러(index.html)에 "같은 폴더의 짝 파일 찾기"에 필요한 최소 기능만 노출
const { contextBridge, ipcRenderer, webUtils } = require('electron');

contextBridge.exposeInMainWorld('syncNative', {
  getPath: (file) => { try { return webUtils.getPathForFile(file) || ''; } catch (e) { return ''; } },
  listSiblings: (p) => ipcRenderer.invoke('sn:list', p),   // [{name, path}] 같은 폴더의 오디오/자막 파일
  readText: (p) => ipcRenderer.invoke('sn:text', p),       // 자막 파일 내용
  fileUrl: (p) => ipcRenderer.invoke('sn:url', p),         // 오디오 파일의 file:// 주소
});
