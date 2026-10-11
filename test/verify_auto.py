"""같은 이름 파일 자동 연결 — 웹(브라우저) 쪽 검증: 규칙 단위 테스트 + 여러 파일 한 번에 선택"""
import sys, os, shutil, tempfile, unicodedata
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = (ROOT / 'www/index.html').as_uri()
T = ROOT / 'test'
SCR = os.environ.get('SCRATCH') or '/tmp/claude-0/-home-claude-sync-player/7943cfc6-733c-57f0-b14a-00bb973656aa/scratchpad'
Path(SCR).mkdir(parents=True, exist_ok=True)
D = Path(tempfile.mkdtemp(dir=SCR, prefix='auto_'))
res = []
def check(n, c, x=''): res.append(bool(c)); print('PASS' if c else 'FAIL', n, x)

wav = T / 'sample.wav'; js = T / 'translated.json'; en = T / 'en.srt'; ko = T / 'ko.srt'
def mk(name, src): p = D / name; shutil.copy(src, p); return str(p)

with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    pg = b.new_page(viewport={'width': 1000, 'height': 720}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(URL)

    # ---- 규칙 단위 테스트 ----
    stem = lambda n: pg.evaluate('n => window.__bp.stemOf(n)', n)
    check('stem: 확장자·언어 꼬리표 제거', stem('Lesson.EN.srt') == 'lesson' and stem('lesson_ko.srt') == 'lesson' and stem('lesson.en-ko.json') == 'lesson' and stem('lesson.translated.json') == 'lesson')
    check('stem: 꼬리표가 이름 전체면 유지', stem('translated.json') == 'translated' and stem('en.srt') == 'en')
    check('stem: 한글 NFC/NFD 동일', stem(unicodedata.normalize('NFD', '강습 녹음.m4a')) == stem(unicodedata.normalize('NFC', '강습 녹음.json')))
    comp = lambda base, pool: pg.evaluate('([b,p]) => { const c = window.__bp.companionsFor({name:b}, p.map(n=>({name:n}))); return {audio:c.audio&&c.audio.name, subs:c.subs.map(s=>s.name)}; }', [base, pool])
    c = comp('lesson.m4a', ['lesson.m4a', 'lesson.json', 'lesson.srt', 'other.json'])
    check('오디오→자막: 같은 이름 json 우선', c == {'audio': 'lesson.m4a', 'subs': ['lesson.json']}, str(c))
    c = comp('lesson.m4a', ['lesson.m4a', 'lesson.en.srt', 'lesson.ko.srt', 'other.srt'])
    check('오디오→자막: 영·한 srt 두 개', c['subs'] == ['lesson.en.srt', 'lesson.ko.srt'], str(c))
    c = comp('lesson.ko.srt', ['lesson.m4a', 'lesson.en.srt', 'lesson.ko.srt', 'x.wav'])
    check('자막→오디오+짝 자막', c['audio'] == 'lesson.m4a' and sorted(c['subs']) == ['lesson.en.srt', 'lesson.ko.srt'], str(c))
    c = comp('lesson.json', ['lesson.m4a', 'lesson.json', 'lesson.srt'])
    check('json을 고르면 json만', c['subs'] == ['lesson.json'] and c['audio'] == 'lesson.m4a', str(c))
    c = comp('enhanced.wav', ['enhanced.wav', 'raw_segments.json', 'proofread_segments.json', 'translated.json'])
    check('앱 결과 폴더: enhanced.wav → translated.json', c['subs'] == ['translated.json'], str(c))
    c = comp('translated.json', ['enhanced.wav', 'translated.json', 'result.md'])
    check('앱 결과 폴더: translated.json → enhanced.wav', c['audio'] == 'enhanced.wav', str(c))
    c = comp('lesson.m4a', ['lesson.m4a', 'other.json', 'raw_segments.json'])
    check('이름이 다르면 엉뚱한 자막을 붙이지 않음', c['subs'] == [], str(c))
    c = comp('lesson.m4a', ['lesson.m4a', 'lesson.txt', 'lesson.pdf'])
    check('txt·기타 파일은 자동 연결 제외', c['subs'] == [], str(c))

    # ---- 한 번에 여러 파일 선택 ----
    def fresh():
        pg.goto(URL); return pg
    fresh()
    pg.set_input_files('#fAny', [mk('lesson.wav', wav), mk('lesson.json', js)])
    pg.wait_for_selector('.cue')
    check('lesson.wav + lesson.json 동시 선택 → 자동 연결', pg.evaluate('window.__bp.S.audioName') == 'lesson.wav' and pg.locator('.cue').count() == 6 and not pg.locator('#empty').is_visible())
    check('연결 안내 토스트', '같은 이름으로 연결' in pg.inner_text('#toast'))

    fresh()
    pg.set_input_files('#fAny', [mk('class.wav', wav), mk('class.en.srt', en), mk('class.ko.srt', ko), mk('other.json', js)])
    pg.wait_for_selector('.cue')
    names = sorted(pg.evaluate('window.__bp.S.subNames'))
    check('class.* 자막만 선택(other.json 제외)', names == ['class.en.srt', 'class.ko.srt'], str(names))
    check('영·한 srt 병합 6문장', pg.locator('.cue').count() == 6 and pg.locator('.cue .ko').count() == 6)

    fresh()
    pg.set_input_files('#fAny', [mk('a.wav', wav), mk('b.wav', wav), mk('b.json', js)])
    pg.wait_for_selector('.cue')
    check('오디오 2개 + b.json → b.wav 선택', pg.evaluate('window.__bp.S.audioName') == 'b.wav')

    fresh()
    pg.set_input_files('#fAny', [mk('song.wav', wav), mk('notes_other.json', js)])
    pg.wait_for_selector('.cue')
    check('이름이 달라도 직접 함께 고른 자막은 사용', pg.evaluate('window.__bp.S.audioName') == 'song.wav' and pg.locator('.cue').count() == 6)

    # ---- 하나만 선택(웹은 폴더를 못 읽음) → 안내 ----
    fresh()
    pg.set_input_files('#fAny', [mk('solo.wav', wav)])
    pg.wait_for_function('window.__bp.audio.readyState >= 1')
    check('웹: 오디오 하나만 → 로드 + 안내', pg.evaluate('window.__bp.S.audioName') == 'solo.wav' and '함께 선택' in pg.inner_text('#toast'), pg.inner_text('#toast'))
    pg.set_input_files('#fAny', [mk('solo.json', js)])
    pg.wait_for_selector('.cue')
    check('웹: 이어서 자막 하나 → 둘 다 연결 상태 유지', pg.locator('.cue').count() == 6 and pg.evaluate('window.__bp.S.audioName') == 'solo.wav' and not pg.locator('#empty').is_visible())

    # ---- 화면 ----
    fresh(); pg.screenshot(path=str(T / 'shots/08_open_screen.png'))
    check('열기 화면에 "파일 열기" 버튼', pg.locator('#pickAny').is_visible() and '자동' in pg.inner_text('#emptyMsg'))
    check('콘솔/페이지 오류 없음', not errs, '; '.join(errs)[:200])
    b.close()

shutil.rmtree(D, ignore_errors=True)
print(f'{sum(res)}/{len(res)} passed'); sys.exit(0 if all(res) else 1)
