// macOS: Apple 개발자 서명이 없어도 Apple Silicon에서 실행되도록 ad-hoc 서명을 적용
// universal 빌드는 x64/arm64를 따로 만든 뒤 합치므로, 합치기 전 임시 폴더(-temp)는 서명하지 않는다
// (서명 파일이 아키텍처마다 달라 병합이 실패함)
const { execSync } = require('child_process');
const path = require('path');
exports.default = async function (context) {
  if (context.electronPlatformName !== 'darwin') return;
  if (/-temp$/.test(path.basename(context.appOutDir))) return;
  const app = path.join(context.appOutDir, `${context.packager.appInfo.productFilename}.app`);
  console.log('  • ad-hoc codesign', app);
  execSync(`codesign --force --deep --sign - "${app}"`, { stdio: 'inherit' });
};
