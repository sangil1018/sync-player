// macOS: Apple 개발자 서명이 없어도 Apple Silicon에서 실행되도록 ad-hoc 서명을 적용
const { execSync } = require('child_process');
const path = require('path');
exports.default = async function (context) {
  if (context.electronPlatformName !== 'darwin') return;
  const app = path.join(context.appOutDir, `${context.packager.appInfo.productFilename}.app`);
  console.log('  • ad-hoc codesign', app);
  execSync(`codesign --force --deep --sign - "${app}"`, { stdio: 'inherit' });
};
