# Sync Player

강습 녹음을 재생하면서 영어·한국어 자막을 함께 보는 플레이어. Windows · Mac · Android.

## 사용법
**파일 열기** 한 번이면 됩니다. 음성 또는 자막 중 하나만 골라도 **같은 이름의 짝 파일을 자동으로 불러옵니다.**

| 고른 파일 | 자동으로 찾는 파일 |
|---|---|
| `lesson.m4a` | `lesson.json` (없으면 `lesson.srt`, 또는 `lesson.en.srt` + `lesson.ko.srt`) |
| `lesson.json` / `lesson.ko.srt` | `lesson.m4a` (같은 이름의 오디오) |
| `enhanced.wav` ↔ `translated.json` | 받아쓰기 앱의 결과 폴더(`work/<이름>/`)는 이름이 달라도 짝으로 인식 |

- 이름 비교는 확장자와 `.en` `.ko` `_en` `-ko` `.translated` 같은 꼬리표를 뗀 뒤, 대소문자·한글 자모 형태(Mac/Windows 차이)를 무시하고 합니다.
- **Windows · Mac 앱**: 파일 하나만 골라도(끌어다 놓아도) 같은 폴더에서 짝을 찾습니다.
- **Android · 웹 브라우저**: 보안상 앱이 같은 폴더를 읽을 수 없어서, 파일 선택창에서 **음성과 자막을 함께 여러 개 선택**하면 이름으로 자동 연결됩니다.
- 이름이 달라도 직접 함께 고른 파일은 그대로 사용합니다. 아래 "오디오만 선택 / 자막만 선택"은 한쪽만 바꿀 때 씁니다.

## 영상 재생
mp4 · mov · webm · mkv 도 오디오와 똑같이 열립니다(같은 이름의 자막 자동 연결). **영상이면 위에 영상, 아래에 자막**, 오디오면 화면 전체가 자막입니다.
영상 클릭 = 재생/일시정지, 더블클릭 = 전체화면, **V** 좌우 반전(거울 모드), `,` `.` 한 프레임씩 이동. 코덱은 H.264/AAC mp4 를 권장합니다(HEVC 등은 소리만 나올 수 있음).

## 하단 자막 · 재생 방식 (Language Reactor 스타일)
- **하단 이중 자막**: 재생 중인 문장의 영어(크게)+한국어가 화면 아래에 항상 표시됩니다. 영어 **단어를 누르면** 일시정지 + 발음 듣기 · 사전(네이버) · 복사.
- **자막 가리기** (눈 아이콘 / H): 영어·한국어·둘 다 흐리게 가리고 듣기 연습. 마우스를 올리거나 탭, **E** 키, 일시정지하면 보입니다.
- **재생 방식** (좌측 하단 / M): 연속 · 문장마다 멈춤 · 따라 말하기(문장 길이만큼 쉬었다가 자동 재생, 0.5–2×) · 문장 반복(2/3/5회/무한).
- **집중 보기** (F / 상단 목록 아이콘): 목록을 숨기고 자막만 크게. 글자 크기는 눈 아이콘 메뉴에서.

| 기능 | 조작 |
|---|---|
| 재생/일시정지 | Space |
| 5초 뒤/앞 | ← / → |
| 이전/다음 문장 | ↑ / ↓ |
| 문장 반복 켜기/끄기 | L |
| 재생 방식 순환 | M |
| 가린 자막 잠깐 보기 | E |
| 자막 가리기 메뉴 | H |
| 집중 보기 ↔ 목록 | F |
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
`electron/preload.js` 는 데스크톱에서 같은 폴더의 짝 파일을 찾는 데만 쓰는 최소 기능(읽기 전용)입니다.
`test/verify.py`·`verify_auto.py`(웹), `verify_electron.py`(데스크톱 앱) 는 검증 스크립트입니다.
