import time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path('/home/claude/sync_player'); URL=(ROOT/'www/index.html').as_uri(); T=ROOT/'test'; OUT=T/'shots'
res=[]
def check(n,c,x=''): res.append(bool(c)); print('PASS' if c else 'FAIL',n,x)
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    for (w,h,tag) in [(1100,760,'desktop'),(390,780,'mobile')]:
        ctx=b.new_context(viewport={'width':w,'height':h}); pg=ctx.new_page(); errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
        pg.goto(URL)
        pg.set_input_files('#fAny',[str(T/'sample.webm'),str(T/'translated.json')]); pg.wait_for_selector('.cue')
        pg.wait_for_function('window.__bp.audio.readyState>=1 && window.__bp.S.video')
        check(f'[{tag}] 영상 인식', pg.locator('#stage').is_visible() and pg.locator('#media').is_visible())
        pg.evaluate('window.__bp.audio.currentTime=5'); pg.click('#play'); time.sleep(.6); pg.click('#play')
        r=pg.evaluate("""()=>{const q=s=>document.querySelector(s).getBoundingClientRect();const v=q('#stage'),l=q('#scroller'),s=q('#sub .sub-in'),d=q('#dock .dock-in');return {vb:v.bottom,lt:l.top,sb:s.bottom,dt:d.top,sh:s.top,lb:l.bottom,dbm:d.bottom,vh:innerHeight,vh_:v.height}}""")
        check(f'[{tag}] 영상이 위, 목록은 영상 아래', r['lt']>=r['vb']-1, str(r))
        check(f'[{tag}] 자막 카드·컨트롤 겹침 없음', r['sb']<=r['dt']+1 and r['dbm']<=r['vh']+1)
        check(f'[{tag}] 목록 영역이 남아 있음(>60px)', r['lb']-r['lt']>60, f"{r['lb']-r['lt']:.0f}px")
        check(f'[{tag}] 자막 동기', 'chest' in pg.inner_text('#subEn'))
        pg.screenshot(path=str(OUT/f'20_video_{tag}.png'))
        pg.click('#media'); time.sleep(.3)
        check(f'[{tag}] 영상 클릭 재생/일시정지', pg.evaluate('!window.__bp.audio.paused'))
        pg.click('#media'); time.sleep(.2)
        pg.keyboard.press('v'); check(f'[{tag}] V 키 좌우 반전', pg.evaluate("document.querySelector('#media').classList.contains('mirror')"))
        t=pg.evaluate('window.__bp.audio.currentTime'); pg.keyboard.press('.'); time.sleep(.2)
        check(f'[{tag}] 프레임 이동', pg.evaluate('window.__bp.audio.currentTime')>t)
        pg.keyboard.press('f'); time.sleep(.3)
        check(f'[{tag}] 집중 보기: 영상 유지·목록 숨김', pg.locator('#stage').is_visible() and not pg.locator('#scroller').is_visible() and pg.locator('#subEn').is_visible())
        pg.screenshot(path=str(OUT/f'21_video_focus_{tag}.png')); pg.keyboard.press('f')
        # 오디오로 교체 → 전부 자막
        pg.set_input_files('#fAudio',str(T/'sample.wav')); pg.wait_for_function('!window.__bp.S.video'); time.sleep(.3)
        r2=pg.evaluate("document.querySelector('#scroller').getBoundingClientRect().top - document.querySelector('main').getBoundingClientRect().top")
        check(f'[{tag}] 오디오: 영상 숨김·목록 전체', not pg.locator('#stage').is_visible() and r2<2, str(r2))
        check(f'[{tag}] 콘솔 오류 없음', not errs, str(errs[:3]))
    b.close()
print(sum(res),'/',len(res))
