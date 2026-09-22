"""Browser regression checks for URL state and copy feedback; no commercial writes."""
import json
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright, expect

APP = Path(__file__).resolve().parents[1]
OUT = APP/'evidence/post-review-fixes'
BASE = 'http://127.0.0.1:8766'
checks, errors, blocked = [], [], []
def check(name, condition=True, detail=None):
    checks.append({'name':name,'passed':bool(condition),'detail':detail})
    assert condition, name
def listing(page, action):
    with page.expect_response(lambda r:'/api/opportunities?' in r.url and r.status==200) as response:
        action()
    page.wait_for_load_state('networkidle')
    return response.value.json()
def params(page):
    return {k:v[0] for k,v in parse_qs(urlparse(page.url).query).items()}
def viewport_feedback(page):
    return page.locator('#copy-status').evaluate("""e=>{const r=e.getBoundingClientRect(),d=document.getElementById('detail').getBoundingClientRect();return {top:r.top,bottom:r.bottom,fullyVisible:r.top>=Math.max(0,d.top)&&r.bottom<=Math.min(innerHeight,d.bottom)}}""")

with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True)
    ctx=browser.new_context(viewport={'width':1440,'height':1000})
    ctx.add_init_script("""Object.defineProperty(navigator,'clipboard',{value:{writeText:async text=>{window.reviewClipboardText=text;if(window.reviewDelayClipboard)await new Promise(resolve=>window.reviewResolveClipboard=resolve);if(window.reviewDenyClipboard)throw Error('Test denial')}}});""")
    def guard(route):
        r=route.request
        if r.method not in ('GET','HEAD') and r.url not in (BASE+'/api/login',BASE+'/api/logout'):
            blocked.append({'method':r.method,'url':r.url})
            route.abort()
        else:
            route.continue_()
    ctx.route('**/api/**',guard)
    page=ctx.new_page()
    page.on('pageerror',lambda e:errors.append(str(e)))
    try:
        page.goto(BASE+'/?region=East&action=identify_account&page=2#main-content')
        page.wait_for_load_state('networkidle')
        codes=json.loads((APP/'.local/access-codes.json').read_text())
        page.get_by_label('Código de acesso local').fill(codes['admin'])
        response=listing(page,lambda:page.get_by_role('button',name='Acessar carteira').click())
        check('URL de entrada sobrevive ao login',params(page)=={'region':'East','action':'identify_account','page':'2'} and response['page']==2)
        check('Filtro e fila da URL correspondem aos registros',all(r['region']=='East' and not r['account'] for r in response['rows']))
        expect(page.locator('#region')).to_have_value('East')
        page.reload()
        page.wait_for_load_state('networkidle')
        expect(page.locator('#page-label')).to_contain_text('página 2')
        check('Recarregar restaura região, fila e página',params(page)=={'region':'East','action':'identify_account','page':'2'})
        shared=ctx.new_page()
        shared.goto(page.url)
        shared.wait_for_load_state('networkidle')
        expect(shared.locator('#region')).to_have_value('East')
        expect(shared.locator('#page-label')).to_contain_text('página 2')
        check('Link compartilhado restaura a seleção em outra aba')
        shared.close()
        listing(page,lambda:page.locator('#region').select_option('West'))
        listing(page,lambda:page.locator('#queues button[data-action="qualify_prospect"]').click())
        listing(page,lambda:page.locator('#search').fill('GTX'))
        check('Busca e mudanças de fila entram no histórico',params(page)=={'search':'GTX','region':'West','action':'qualify_prospect'})
        page.go_back()
        expect(page.locator('#search')).to_have_value('')
        page.wait_for_load_state('networkidle')
        check('Voltar restaura busca e fila',params(page)=={'region':'West','action':'qualify_prospect'})
        page.go_back()
        page.wait_for_load_state('networkidle')
        expect(page.locator('#queues button[data-action="identify_account"]')).to_have_attribute('aria-pressed','true')
        check('Voltar novamente restaura fila anterior')
        page.go_forward()
        page.wait_for_load_state('networkidle')
        expect(page.locator('#queues button[data-action="qualify_prospect"]')).to_have_attribute('aria-pressed','true')
        check('Avançar restaura fila seguinte')
        page.locator('#search').fill('NAO-DEVE-REAPARECER')
        page.go_back()
        page.wait_for_timeout(350)
        expect(page.locator('#search')).to_have_value('')
        check('Histórico cancela busca ainda aguardando debounce','search' not in params(page))
        listing(page,lambda:page.locator('#clear').click())
        check('Limpar remove parâmetros próprios e preserva âncora',params(page)=={} and urlparse(page.url).fragment=='main-content')
        page.go_back()
        page.wait_for_load_state('networkidle')
        expect(page.locator('#region')).to_have_value('West')
        check('Limpar pode ser desfeito pelo histórico')
        listing(page,lambda:page.locator('#clear').click())
        listing(page,lambda:page.get_by_role('button',name='Próxima página',exact=True).click())
        check('Paginação atualiza URL',params(page)=={'page':'2'})
        page.locator('#rows .open-deal').first.click()
        selected=page.locator('#rows .open-deal').first.get_attribute('data-id')
        page.locator('#conference-summary > summary').click()
        page.locator('#copy-summary').click()
        expect(page.locator('#copy-status')).to_contain_text('copiado')
        expect(page.locator('#message')).not_to_be_visible()
        expect(page.locator('#detail-message')).not_to_be_visible()
        rect=viewport_feedback(page)
        check('Confirmação de cópia fica visível perto do botão após paginar',rect['fullyVisible'],rect)
        check('Resumo copiado pertence à oportunidade selecionada',selected in page.evaluate('window.reviewClipboardText'))
        page.screenshot(path=str(OUT/'desktop-copy-feedback.png'))
        page.evaluate('window.reviewDenyClipboard=true')
        page.locator('#copy-summary').click()
        expect(page.locator('#copy-status')).to_contain_text('manualmente')
        check('Falha de cópia oferece seleção manual',page.locator('#conference-text').evaluate('(e)=>e===document.activeElement&&e.selectionEnd===e.value.length'))
        page.evaluate('window.reviewDenyClipboard=false;window.reviewDelayClipboard=true')
        page.locator('#copy-summary').click()
        page.locator('#rows .open-deal').nth(1).click()
        page.evaluate('window.reviewResolveClipboard()')
        expect(page.locator('#message')).to_contain_text(selected)
        expect(page.locator('#copy-status')).not_to_be_visible()
        check('Cópia atrasada mantém ID de origem ao trocar de oportunidade')
        page.set_viewport_size({'width':320,'height':740})
        page.locator('#rows .open-deal').nth(1).click()
        page.evaluate('window.reviewDelayClipboard=false')
        page.locator('#conference-summary > summary').click()
        page.locator('#copy-summary').click()
        expect(page.locator('#copy-status')).to_contain_text('copiado')
        check('Confirmação móvel fica dentro do diálogo',page.locator('#copy-status').evaluate('(e)=>!!e.closest("dialog[open]")'))
        rect=viewport_feedback(page)
        check('Confirmação móvel fica na área visível',rect['fullyVisible'],rect)
        page.screenshot(path=str(OUT/'mobile-copy-feedback.png'))
        page.keyboard.press('Escape')
        page.set_viewport_size({'width':1440,'height':1000})
        page.goto(BASE+'/?page=-3&action=invalid&region=unknown&search=SEMRESULTADO')
        page.wait_for_load_state('networkidle')
        expect(page.locator('#empty')).to_be_visible()
        check('Parâmetros inválidos são normalizados',params(page)=={'search':'SEMRESULTADO'})
        page.goto(BASE+'/?page=99999')
        page.wait_for_load_state('networkidle')
        expect(page.locator('#page-label')).to_contain_text('página 105 de 105')
        check('Página além do total é normalizada na URL',params(page)=={'page':'105'})
        # Team fields are restored together, using values actually present in a real row.
        row=page.request.get(BASE+'/api/opportunities').json()['rows'][0]
        from urllib.parse import urlencode
        team={k:row[k] for k in ['sales_agent','manager','region']}
        page.goto(BASE+'/?'+urlencode(team))
        page.wait_for_load_state('networkidle')
        check('Vendedor, gestor e região restaurados juntos',all(page.locator('#'+k).input_value()==v for k,v in team.items()))
        page.get_by_role('button',name='Sair',exact=True).click()
        expect(page.locator('#login')).to_be_visible()
        page.goto(BASE+'/?sales_agent=INVALID_SCOPE_ONLY_TEST&manager=INVALID_SCOPE_ONLY_TEST&region=unknown&page=99999')
        page.wait_for_load_state('networkidle')
        page.get_by_label('Código de acesso local').fill(codes['vendedor'])
        response=listing(page,lambda:page.get_by_role('button',name='Acessar carteira').click())
        scope=page.request.get(BASE+'/api/meta').json()['user']['scope']
        check('URL não amplia a carteira do vendedor',0<response['scope_total']<2089 and all(r['sales_agent']==scope for r in response['rows']))
        check('Filtros indisponíveis para o perfil são removidos',all(k not in params(page) for k in ['sales_agent','manager','region']))
        page.get_by_role('button',name='Sair',exact=True).click()
        expect(page.locator('#login')).to_be_visible()
        check('Nenhum erro JavaScript não tratado',not errors,errors)
        check('Nenhuma tentativa de escrita comercial real',not blocked,blocked)
    finally:
        browser.close()
        OUT.mkdir(exist_ok=True)
        (OUT/'ui-results.json').write_text(json.dumps({'checks':checks,'errors':errors,'blocked':blocked},ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'checks':len(checks),'passed':sum(c['passed'] for c in checks),'errors':errors,'blocked':blocked},ensure_ascii=False))
