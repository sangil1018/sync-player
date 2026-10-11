import subprocess, time, sys, os
from pathlib import Path
from playwright.sync_api import sync_playwright
R = Path('/home/claude/sync_player'); T = R/'test'
env = dict(os.environ, DISPLAY=':99')
xv = subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1280x900x24'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.2)
app = subprocess.Popen([str(R/'node_modules/.bin/electron'), str(R), '--no-sandbox', '--remote-debugging-port=9333'], env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
res = []
def check(n, c, x=''): res.append(c); print('PASS' if c else 'FAIL', n, x)
try:
    with sync_playwright() as p:
        for _ in range(40):
            try: b = p.chromium.connect_over_cdp('http://127.0.0.1:9333'); break
            except Exception: time.sleep(.5)
        else: raise SystemExit('Electron CDP 연결 실패')
        pg = b.contexts[0].pages[0]
        pg.wait_for_load_state('load')
        check('Electron 창 제목', 'Sync' in pg.title(), pg.title())
        pg.set_input_files('#fAudio', str(T/'sample.wav')); pg.set_input_files('#fSub', str(T/'translated.json'))
        pg.wait_for_selector('.cue')
        check('자막 6문장 로드', pg.locator('.cue').count() == 6)
        pg.click('#play'); time.sleep(.4)
        check('재생 중', pg.evaluate('!window.__bp.audio.paused'))
        pg.evaluate('window.__bp.audio.currentTime = 18'); time.sleep(.6)
        check('18초 → 5번째 문장 활성', pg.evaluate('window.__bp.S.active') == 4)
        pg.screenshot(path=str(T/'shots/07_electron.png'))
        pg.keyboard.press('Space'); time.sleep(.2)
        check('Space 일시정지', pg.evaluate('window.__bp.audio.paused'))

        # ---- 같은 이름 파일 자동 연결 (한 파일만 골라도 같은 폴더에서 짝을 찾음) ----
        import shutil, tempfile
        SCR = os.environ.get('SCRATCH') or '/tmp/claude-0/-home-claude-sync-player/7943cfc6-733c-57f0-b14a-00bb973656aa/scratchpad'
        Path(SCR).mkdir(parents=True, exist_ok=True)
        W = Path(tempfile.mkdtemp(dir=SCR, prefix='el_'))
        def folder(name, files):
            d = W / name; d.mkdir()
            for fn, src in files.items(): shutil.copy(T / src, d / fn)
            return d
        wav, js, en, ko = 'sample.wav', 'translated.json', 'en.srt', 'ko.srt'
        def pick(paths):
            """실제 파일 선택창에서 고른 것과 같게(디스크 경로가 있는 File) #fAny에 파일을 넣는다"""
            if not isinstance(paths, list): paths = [paths]
            cdp = pg.context.new_cdp_session(pg)
            doc = cdp.send('DOM.getDocument', {'depth': -1})
            nid = cdp.send('DOM.querySelector', {'nodeId': doc['root']['nodeId'], 'selector': '#fAny'})['nodeId']
            cdp.send('DOM.setFileInputFiles', {'files': [str(x) for x in paths], 'nodeId': nid})
        def reopen():
            pg.reload(); pg.wait_for_load_state('load'); pg.wait_for_function('!!window.syncNative')
        reopen()
        check('preload 브리지(syncNative) 노출', pg.evaluate('typeof window.syncNative.getPath') == 'function')

        d1 = folder('one', {'lesson.wav': wav, 'lesson.json': js, 'other.json': js})
        pick(str(d1 / 'lesson.wav')); pg.wait_for_selector('.cue', timeout=8000)
        check('오디오만 선택 → 같은 이름 json 자동 로드', pg.evaluate('window.__bp.S.audioName') == 'lesson.wav' and pg.evaluate('window.__bp.S.subNames') == ['lesson.json'] and pg.locator('.cue').count() == 6)
        check('연결 안내 토스트', '같은 이름으로 연결' in pg.inner_text('#toast'), pg.inner_text('#toast'))

        reopen(); d2 = folder('two', {'class.wav': wav, 'class.en.srt': en, 'class.ko.srt': ko, 'other.srt': en})
        pick(str(d2 / 'class.ko.srt')); pg.wait_for_selector('.cue', timeout=8000)
        check('자막만 선택 → 같은 이름 오디오 + 영·한 srt 자동 로드',
              pg.evaluate('window.__bp.S.audioName') == 'class.wav' and sorted(pg.evaluate('window.__bp.S.subNames')) == ['class.en.srt', 'class.ko.srt'] and pg.locator('.cue .ko').count() == 6)

        reopen(); d3 = folder('three', {'enhanced.wav': wav, 'translated.json': js, 'raw_segments.json': js, 'proofread_segments.json': js})
        pick(str(d3 / 'translated.json')); pg.wait_for_selector('.cue', timeout=8000)
        check('앱 결과 폴더: translated.json → enhanced.wav 자동 로드', pg.evaluate('window.__bp.S.audioName') == 'enhanced.wav' and pg.locator('.cue').count() == 6)
        pg.wait_for_function('window.__bp.audio.readyState >= 1', timeout=8000)
        check('file:// 오디오 실제 재생 가능(30초)', abs(pg.evaluate('window.__bp.audio.duration') - 30) < .5)
        pg.click('#play'); time.sleep(.4); pg.evaluate('window.__bp.audio.currentTime = 9'); time.sleep(.5)
        check('자동 연결 후 재생·문장 동기', pg.evaluate('!window.__bp.audio.paused') and pg.evaluate('window.__bp.S.active') == 2)

        reopen(); d4 = folder('four', {'lone.wav': wav, 'other.json': js})
        pick(str(d4 / 'lone.wav')); pg.wait_for_function('window.__bp.audio.readyState >= 1', timeout=8000)
        check('짝이 없으면 오디오만 로드 + 안내', pg.evaluate('window.__bp.S.cues.length') == 0 and '찾지 못했습니다' in pg.inner_text('#toast'), pg.inner_text('#toast'))

        reopen(); d5 = folder('five', {'a.wav': wav, 'a.json': js})
        pick([str(d5 / 'a.wav'), str(d5 / 'a.json')]); pg.wait_for_selector('.cue', timeout=8000)
        check('여러 개 동시 선택도 정상', pg.evaluate('window.__bp.S.audioName') == 'a.wav' and pg.locator('.cue').count() == 6)
        pg.screenshot(path=str(T/'shots/09_electron_auto.png'))
        shutil.rmtree(W, ignore_errors=True)
        b.close()
finally:
    app.terminate(); xv.terminate()
print(f'{sum(res)}/{len(res)} passed'); sys.exit(0 if all(res) else 1)
