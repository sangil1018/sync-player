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
        b.close()
finally:
    app.terminate(); xv.terminate()
print(f'{sum(res)}/{len(res)} passed'); sys.exit(0 if all(res) else 1)
