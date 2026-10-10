import sys, json, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path('/home/claude/sync_player')
URL = (ROOT / 'www/index.html').as_uri()
T = ROOT / 'test'
OUT = T / 'shots'; OUT.mkdir(exist_ok=True)
results = []
def check(name, cond, extra=''):
    results.append((name, bool(cond), extra)); print(('PASS' if cond else 'FAIL'), name, extra)

with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])

    # ---------- 데스크톱 ----------
    ctx = b.new_context(viewport={'width': 1100, 'height': 760})
    pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
    pg.goto(URL)
    pg.screenshot(path=str(OUT / '01_empty.png'))
    check('빈 화면 표시', pg.locator('#empty').is_visible())

    pg.set_input_files('#fAudio', str(T / 'sample.wav'))
    pg.wait_for_function('window.__bp.audio.readyState >= 1')
    check('오디오 로드(길이 30초)', abs(pg.evaluate('window.__bp.audio.duration') - 30) < .5)
    pg.screenshot(path=str(OUT / '02_audio_only.png'))
    pg.set_input_files('#fSub', str(T / 'translated.json'))
    pg.wait_for_selector('.cue')
    check('JSON 자막 6문장', pg.locator('.cue').count() == 6)
    check('영어·한국어 동시 렌더', pg.locator('.cue .en').count() == 6 and pg.locator('.cue .ko').count() == 6)
    check('⚠ 불확실 문장 표시', pg.locator('.cue .warn').count() == 1)
    check('빈 화면 숨김·컨트롤 표시', (not pg.locator('#empty').is_visible()) and pg.locator('#dock').is_visible())

    pg.click('#play'); time.sleep(.3)
    check('재생 시작', pg.evaluate('!window.__bp.audio.paused'))
    pg.evaluate('window.__bp.audio.currentTime = 9'); time.sleep(.4)
    act = pg.evaluate('window.__bp.S.active')
    check('9초 → 3번째 문장 활성', act == 2, f'active={act}')
    pg.evaluate('window.__bp.audio.currentTime = 13'); time.sleep(.7)
    check('13초 → 4번째 문장 활성(⚠)', pg.evaluate('window.__bp.S.active') == 3)
    pg.screenshot(path=str(OUT / '03_playing_both.png'))

    # 자동 스크롤: 활성 카드가 스크롤 영역 중앙 근처
    box = pg.evaluate("""() => { const a=document.querySelector('.cue.active').getBoundingClientRect(), s=document.querySelector('#scroller').getBoundingClientRect();
      return {ac:(a.top+a.bottom)/2, sc:(s.top+s.bottom)/2}; }""")
    check('활성 문장이 화면 중앙에 위치', abs(box['ac'] - box['sc']) < 90, str(box))

    # 클릭 이동
    pg.locator('.cue').nth(1).click(); time.sleep(.3)
    t = pg.evaluate('window.__bp.audio.currentTime')
    check('문장 클릭 → 해당 시작 시각으로 이동', 3.9 < t < 5.0, f't={t:.2f}')

    # 이전/다음 문장
    pg.click('#next'); time.sleep(.2)
    check('다음 문장 버튼', pg.evaluate('window.__bp.S.active') == 2)
    pg.click('#prev'); time.sleep(.2)
    check('이전 문장 버튼', pg.evaluate('window.__bp.S.active') == 1)

    # 5초 이동
    pg.evaluate('window.__bp.audio.currentTime = 10'); pg.click('#fwd'); time.sleep(.15)
    check('+5초', 14.9 < pg.evaluate('window.__bp.audio.currentTime') < 15.8)
    pg.click('#back'); time.sleep(.15)
    check('-5초', 9.9 < pg.evaluate('window.__bp.audio.currentTime') < 10.8)

    # 문장 반복
    pg.evaluate('window.__bp.audio.currentTime = 4.2'); time.sleep(.3)
    pg.click('#loopBtn')
    pg.evaluate('window.__bp.audio.currentTime = 8.0'); time.sleep(1.0)   # 문장2 끝(8.5) 지나면 4.0으로 돌아와야 함
    t = pg.evaluate('window.__bp.audio.currentTime'); a = pg.evaluate('window.__bp.S.active')
    check('문장 반복: 끝에서 문장 처음으로 복귀', a == 1 and t < 8.5, f't={t:.2f} active={a}')
    pg.click('#loopBtn')

    # 속도
    pg.click('#speedBtn'); pg.click('#speedPop button[data-r="0.8"]')
    check('속도 0.8×', abs(pg.evaluate('window.__bp.audio.playbackRate') - .8) < .001 and '0.8' in pg.inner_text('#speedBtn'))

    # 표시 모드
    pg.click('#modeSeg button[data-mode="en"]')
    check('EN 모드: 한국어 숨김', not pg.locator('.cue.active .ko').is_visible() and pg.locator('.cue.active .en').is_visible())
    pg.click('#modeSeg button[data-mode="ko"]')
    check('한 모드: 영어 숨김', pg.locator('.cue.active .ko').is_visible() and not pg.locator('.cue.active .en').is_visible())
    pg.click('#modeSeg button[data-mode="both"]')

    # 글자 크기
    f0 = pg.evaluate("getComputedStyle(document.querySelector('.cue .en')).fontSize")
    pg.click('#fsUp'); pg.click('#fsUp')
    f1 = pg.evaluate("getComputedStyle(document.querySelector('.cue .en')).fontSize")
    check('글자 크게', float(f1[:-2]) > float(f0[:-2]), f'{f0}→{f1}')
    pg.click('#fsDown'); pg.click('#fsDown')

    # 키보드
    pg.evaluate('window.__bp.audio.pause()'); pg.keyboard.press('Space'); time.sleep(.2)
    check('Space 재생', pg.evaluate('!window.__bp.audio.paused'))
    pg.keyboard.press('Space'); time.sleep(.2)
    check('Space 일시정지', pg.evaluate('window.__bp.audio.paused'))

    # 시크바
    pg.evaluate("(()=>{const s=document.querySelector('#seek'); s.value=500; s.dispatchEvent(new Event('input')); s.dispatchEvent(new Event('change'));})()")
    time.sleep(.2)
    check('시크바 50% → 15초', abs(pg.evaluate('window.__bp.audio.currentTime') - 15) < .6)
    pg.evaluate('window.__bp.audio.currentTime = 22.5'); time.sleep(.5)
    pg.screenshot(path=str(OUT / '04_desktop_final.png'))
    check('콘솔/페이지 오류 없음(데스크톱)', not errs, '; '.join(errs)[:300])
    ctx.close()

    # ---------- SRT 2개(영/한) 병합 ----------
    ctx = b.new_context(viewport={'width': 1100, 'height': 760}); pg = ctx.new_page()
    pg.goto(URL)
    pg.set_input_files('#fAudio', str(T / 'sample.wav'))
    pg.set_input_files('#fSub', [str(T / 'en.srt'), str(T / 'ko.srt')])
    pg.wait_for_selector('.cue')
    check('SRT 영·한 2파일 병합', pg.locator('.cue').count() == 6 and pg.locator('.cue .ko').count() == 6 and '발보아' in pg.inner_text('.cue >> nth=0'))
    pg.set_input_files('#fSub', str(T / 'bilingual.srt')); pg.wait_for_timeout(300)
    check('SRT 한 파일(영+한 줄) 분리', pg.locator('.cue').count() == 6 and pg.locator('.cue .ko').count() == 6 and pg.locator('.cue .en').count() == 6)
    ctx.close()

    # ---------- 모바일(안드로이드 폭) ----------
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
    pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(URL); pg.screenshot(path=str(OUT / '05_mobile_empty.png'))
    pg.set_input_files('#fAudio', str(T / 'sample.wav')); pg.set_input_files('#fSub', str(T / 'translated.json'))
    pg.wait_for_selector('.cue'); pg.evaluate('window.__bp.audio.play()'); pg.evaluate('window.__bp.audio.currentTime = 6'); time.sleep(.8)
    pg.screenshot(path=str(OUT / '06_mobile_playing.png'))
    ov = pg.evaluate('document.documentElement.scrollWidth > window.innerWidth')
    check('모바일 가로 넘침 없음', not ov)
    dock = pg.evaluate("(()=>{const r=document.querySelector('.dock-in').getBoundingClientRect(); return [r.left>=0, r.right<=innerWidth]})()")
    check('모바일 컨트롤 영역이 화면 안', all(dock))
    check('콘솔/페이지 오류 없음(모바일)', not errs)
    ctx.close(); b.close()

bad = [r for r in results if not r[1]]
print(f'\n{len(results)-len(bad)}/{len(results)} passed')
sys.exit(1 if bad else 0)
