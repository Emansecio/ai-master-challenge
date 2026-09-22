"""Measure UI review observations without editing application files or records."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

HERE=Path(__file__).resolve().parent
APP=HERE.parents[1]
BASE='http://127.0.0.1:8766'
results={}
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True)
    context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce')
    context.add_init_script("Object.defineProperty(navigator,'clipboard',{value:{writeText:async ()=>{}}});")
    def guard(route):
        if route.request.method not in ('GET','HEAD') and route.request.url not in (BASE+'/api/login',BASE+'/api/logout'):
            route.abort()
        else:
            route.continue_()
    context.route('**/api/**',guard)
    page=context.new_page()
    try:
        page.goto(BASE)
        page.wait_for_load_state('networkidle')
        code=json.loads((APP/'.local/access-codes.json').read_text())['admin']
        page.get_by_label('Código de acesso local').fill(code)
        page.get_by_role('button',name='Acessar carteira').click()
        expect(page.locator('#rows tr')).to_have_count(20)
        page.wait_for_load_state('networkidle')
        with page.expect_response(lambda r:'/api/opportunities?' in r.url) as response:
            page.get_by_role('button',name='Próxima página',exact=True).click()
        page.wait_for_load_state('networkidle')
        page.locator('#rows .open-deal').first.click()
        page.locator('#conference-summary > summary').click()
        page.locator('#copy-summary').click()
        expect(page.locator('#message')).to_contain_text('copiado')
        results['desktop_feedback']=page.evaluate("""()=>Object.fromEntries(['message','detail-message'].map(id=>{const e=document.getElementById(id),r=e.getBoundingClientRect(),s=getComputedStyle(e);return [id,{text:e.textContent,hidden:e.hidden,display:s.display,top:r.top,bottom:r.bottom,inViewport:s.display!=='none'&&r.bottom>0&&r.top<innerHeight}]}))""")
        page.screenshot(path=str(HERE/'desktop-feedback-viewport.png'))
        results['forms']=page.locator('input,select,textarea').evaluate_all("els=>els.map(e=>({id:e.id,name:e.name,autocomplete:e.getAttribute('autocomplete'),type:e.type,spellcheck:e.spellcheck}))")
        results['reduced_motion']=page.evaluate("({requested:matchMedia('(prefers-reduced-motion: reduce)').matches,transition:getComputedStyle(document.querySelector('button')).transitionDuration})")
        page.set_viewport_size({'width':320,'height':740})
        page.locator('#rows .open-deal').first.click()
        page.screenshot(path=str(HERE/'mobile-dialog-viewport.png'))
        focus=[]
        for _ in range(25):
            page.keyboard.press('Tab')
            focus.append(page.evaluate("""()=>{const e=document.activeElement,r=e.getBoundingClientRect(),top=document.querySelector('#detail-dialog .detail-topline').getBoundingClientRect(),s=getComputedStyle(e);return {id:e.id,tag:e.tagName,text:e.textContent.slice(0,70),top:r.top,bottom:r.bottom,headerBottom:top.bottom,hiddenByHeader:r.bottom<=top.bottom&&!e.closest('.detail-topline'),outline:s.outlineStyle+' '+s.outlineWidth,inside:document.getElementById('detail-dialog').contains(e)}}"""))
        results['mobile_focus']=focus
        results['modal_overscroll']=page.locator('#detail-dialog').evaluate("e=>getComputedStyle(e).overscrollBehaviorY")
        results['mobile_overflow']=page.evaluate('document.documentElement.scrollWidth>innerWidth')
        page.keyboard.press('Escape')
        page.get_by_role('button',name='Sair',exact=True).click()
        expect(page.locator('#login')).to_be_visible()
    finally:
        browser.close()
        (HERE/'design-probes.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'desktop_feedback':results.get('desktop_feedback'),'occluded_focus':[x for x in results.get('mobile_focus',[]) if x['hiddenByHeader']],'mobile_overflow':results.get('mobile_overflow'),'reduced_motion':results.get('reduced_motion')},ensure_ascii=False))
