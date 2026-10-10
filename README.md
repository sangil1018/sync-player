# Sync Player

강습 녹음을 재생하면서 영어·한국어 자막을 함께 보는 플레이어. Windows · Mac · Android.

## 사용법
1. **오디오 열기** → 강습 녹음(mp3 / m4a / wav / mp4)
2. **자막 열기** → 받아쓰기 앱이 만든 `translated.json`
   (영어 SRT + 한국어 SRT 2개를 같이 선택해도 되고, 영·한이 함께 든 SRT/VTT 1개도 됩니다)
3. 재생하면 현재 문장이 화면 가운데에서 강조되며 자동으로 넘어갑니다. 문장을 누르면 그 지점부터 재생.

| 기능 | 조작 |
|---|---|
| 재생/일시정지 | Space |
| 5초 뒤/앞 | ← / → |
| 이전/다음 문장 | ↑ / ↓ |
| 현재 문장 반복 | L |
| 현재 문장 처음부터 | R |
| 속도 | `[` `]` 또는 우측 하단 버튼 (0.5×–2×) |
| 표시 | 1 영·한 / 2 영어 / 3 한국어 |

⚠ 표시는 현장 음질 때문에 받아쓰기가 불확실한 문장입니다. 마지막 재생 위치는 파일별로 기억합니다.

## 설치
- **Windows**: `SyncPlayer-*-win-x64-portable.zip` 압축 해제 → `Sync Player.exe` 실행
  (SmartScreen 경고: 추가 정보 → 실행)
- **Android**: `.apk` 설치 (설정에서 "출처를 알 수 없는 앱 설치" 허용)
- **Mac**: 아래 빌드 후 `.dmg` 설치. 처음 한 번은 앱을 우클릭 → 열기.
  Apple 개발자 서명이 없는 앱이라, 막히면 터미널에서 `xattr -dr com.apple.quarantine "/Applications/Sync Player.app"`

## 빌드 (Mac / Windows 설치 파일)
GitHub에 올리고 `Actions → Build Sync Player → Run workflow` 를 누르면
Windows 설치 파일(.exe), Mac(.dmg, Intel+Apple Silicon 겸용), Android(.apk) 가 한 번에 만들어집니다.
`v1.0.0` 같은 태그를 푸시하면 Releases에 자동 게시됩니다.

로컬 빌드:
```
npm install
npm run build:mac      # Mac에서
npm run build:win      # Windows에서 (설치 파일 + 포터블)
npx cap sync android && cd android && ./gradlew assembleDebug   # APK (JDK 17+, Android SDK)
```

## 구조
`www/index.html` 하나가 전체 앱입니다. Electron(데스크톱)과 Capacitor(Android)가 이 파일을 그대로 감쌉니다.
`test/verify.py` 는 헤드리스 브라우저 검증 스크립트입니다.
