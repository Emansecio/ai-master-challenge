"""Review checks: real reads and isolated UI responses, never commercial writes."""
import copy
import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

HERE = Path(__file__).resolve().parent
APP = HERE.parents[1]
BASE = 'http://127.0.0.1:8766'
checks, observations, errors, blocked = [], [], [], []

def record(name, condition=True, detail=None):
    checks.append({'name': name, 'passed': bool(condition), 'detail': detail})
    assert condition, name

def listing(page, action):
    with page.expect_response(lambda r: '/api/opportunities?' in r.url and r.status == 200) as response:
        action()
    page.wait_for_load_state('networkidle')
    return response.value.json()

def guard(route):
    request = route.request
    if request.method not in ('GET', 'HEAD') and request.url not in (BASE+'/api/login', BASE+'/api/logout'):
        blocked.append({'method': request.method, 'url': request.url})
        route.abort()
    else:
        route.continue_()

def login(page, role):
    page.goto(BASE)
    page.wait_for_load_state('networkidle')
    codes = json.loads((APP/'.local/access-codes.json').read_text())
    page.get_by_label('Código de acesso local').fill(codes[role])
    page.get_by_role('button', name='Acessar carteira').click()
    expect(page.locator('#shell')).to_be_visible()
    page.wait_for_load_state('networkidle')

def logout(page):
    page.get_by_role('button', name='Sair', exact=True).click()
    expect(page.locator('#login')).to_be_visible()

with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=True)
    try:
        context = browser.new_context(viewport={'width':1440,'height':1000})
        context.route('**/api/**', guard)
        page = context.new_page()
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(BASE)
        page.wait_for_load_state('networkidle')
        page.get_by_label('Código de acesso local').fill('invalid-review-code')
        page.get_by_role('button', name='Acessar carteira').click()
        expect(page.locator('#login-error')).to_contain_text('inválido')
        record('Login inválido apresenta mensagem e mantém formulário')
        login(page, 'admin')
        expect(page.locator('#rows tr')).to_have_count(20)
        expect(page.locator('#metric-total')).to_have_text('2.089')
        record('Login administrativo e primeira página real')
        result = listing(page, lambda: page.get_by_role('button', name='Próxima página', exact=True).click())
        record('Paginação real e foco no título dos resultados', result['page']==2 and page.locator('#portfolio-title').evaluate('(e)=>e===document.activeElement'))
        result = listing(page, lambda: page.locator('#search').fill('SEMRESULTADO-REVISAO-2026'))
        expect(page.locator('#empty')).to_be_visible()
        record('Busca vazia oferece recuperação', result['total']==0)
        result = listing(page, lambda: page.locator('#clear-empty').click())
        record('Limpar busca restaura carteira', result['total']==2089)
        result = listing(page, lambda: page.locator('#region').select_option('East'))
        record('Filtro regional aplicado', result['total']>0 and all(r['region']=='East' for r in result['rows']))
        observations.append({'name':'URL depois do filtro regional','url':page.url,'filter':'East'})
        page.reload()
        page.wait_for_load_state('networkidle')
        observations.append({'name':'Filtro regional depois de recarregar','value':page.locator('#region').input_value()})
        listing(page, lambda: page.locator('#queues button[data-action="identify_account"]').click())
        result = listing(page, lambda: page.locator('#search').fill('A7SA2L21'))
        page.locator('#rows button.open-deal').first.click()
        expect(page.locator('#account-heading')).to_have_text('Confirme e vincule a empresa')
        record('Cadastro aparece antes da explicação', page.locator('#detail').evaluate('(e)=>!!(e.querySelector("#account-heading").compareDocumentPosition(e.querySelector("#recommendation-title")) & Node.DOCUMENT_POSITION_FOLLOWING)'))
        page.locator('#conference-summary > summary').click()
        text = page.locator('#conference-text').input_value()
        record('Resumo explicita data histórica, identidade e ausência de atendimento', all(x in text for x in ['A7SA2L21','31/12/2017','ATENDIMENTO NÃO REGISTRADO']))
        page.locator('#audit > summary').click()
        expect(page.locator('#audit-content')).to_contain_text('Versões dos dados')
        record('Histórico real disponível')
        listing(page, lambda: page.locator('#clear').click())
        page.set_viewport_size({'width':320,'height':740})
        record('Página em 320 px sem rolagem horizontal global', page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'))
        page.screenshot(path=str(HERE/'mobile-list.png'), full_page=True)
        button = page.locator('#rows button.open-deal').first
        selected_id = button.get_attribute('data-id')
        button.click()
        expect(page.locator('#detail-dialog')).to_be_visible()
        record('Detalhe móvel abre com foco no título', page.locator('#detail-title').evaluate('(e)=>e===document.activeElement'))
        for _ in range(18):
            page.keyboard.press('Tab')
            assert page.locator('#detail-dialog').evaluate('(e)=>e.contains(document.activeElement)')
        record('Foco permanece no diálogo móvel durante navegação por Tab')
        page.screenshot(path=str(HERE/'mobile-detail.png'), full_page=True)
        page.keyboard.press('Escape')
        expect(page.locator('#detail-dialog')).not_to_be_visible()
        record('Escape fecha diálogo e devolve foco ao registro', page.evaluate('document.activeElement.dataset.id')==selected_id)
        logout(page)
        record('Logout remove carteira visível')
        context.close()

        for role, label in [('gestor','Gestor'),('vendedor','Vendedor')]:
            ctx = browser.new_context(viewport={'width':1440,'height':1000})
            ctx.route('**/api/**', guard)
            pg = ctx.new_page()
            login(pg, role)
            expect(pg.locator('#user-role')).to_have_text(label)
            total = int(pg.locator('#metric-total').inner_text().replace('.',''))
            record('Carteira restrita no perfil '+role, 0<total<2089, {'visible_total':total})
            logout(pg)
            ctx.close()

        # All API calls in this context are fulfilled locally. No login or data write reaches the server.
        cases = json.loads((APP/'evidence/business-review.json').read_text())['cases']
        rows = [copy.deepcopy(next(c['opportunity'] for c in cases if c['opportunity']['id']==i)) for i in ['A7SA2L21','DB801ISB']]
        for row in rows:
            row.update(classification=None, status='unclassified')
        pending, api_calls = [], []
        def fixture(route):
            path = route.request.url.split(BASE)[1].split('?')[0]
            api_calls.append({'method':route.request.method,'path':path})
            def reply(body, status=200):
                route.fulfill(status=status, json=body)
            if path=='/api/meta':
                return reply({'user':{'id':'teste-local','role':'admin'},'filters':{'sales_agent':[],'manager':[],'region':[]},'accounts':['Acme Corporation','Globex'],'key_configured':False})
            if path=='/api/opportunities':
                return reply({'rows':rows,'total':2,'scope_total':2,'counts':{'identify_account':2},'page':1,'pages':1})
            match = re.fullmatch(r'/api/opportunities/([^/]+)(/audit)?',path)
            if match:
                row = next(r for r in rows if r['id']==match[1])
                if match[2]:
                    return reply({'opportunity_id':row['id'],'current_version':row['version'],'policy_hash':'fixture','policy_version':'test','dataset_sha256':'fixture','history_limit':20,'version_count':1,'classification_count':0,'attempt_count':0,'versions':[],'classifications':[],'attempts':[]})
                if route.request.method=='PATCH':
                    pending.append((route, row, route.request.post_data_json))
                    return
                return reply(row)
            raise AssertionError('Unexpected fixture request: '+path)
        ctx = browser.new_context(viewport={'width':1440,'height':1000})
        ctx.route('**/api/**', fixture)
        ctx.add_init_script("Object.defineProperty(navigator,'clipboard',{value:{writeText:async text=>{window.reviewClipboard=text;if(window.reviewDenyClipboard)throw Error('Test denial')}}});")
        pg = ctx.new_page()
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.goto(BASE)
        pg.wait_for_load_state('networkidle')
        a = '#rows button[data-id="A7SA2L21"]'
        b = '#rows button[data-id="DB801ISB"]'
        pg.locator('#account-select').select_option('Acme Corporation')
        pg.locator(b).click()
        pg.locator(a).click()
        record('Rascunho preservado ao trocar oportunidade', pg.locator('#account-select').input_value()=='Acme Corporation')
        pg.locator('#save-account').click()
        expect(pg.locator('#account-select')).to_be_disabled()
        assert pending
        pg.locator(b).click()
        route, row, body = pending.pop()
        row.update(account=body['account'],version=row['version']+1)
        row['state']['account_identified']=True
        row['decision']['next_action']='review_old_negotiation'
        route.fulfill(json=row)
        expect(pg.locator('#message')).to_contain_text('A7SA2L21')
        expect(pg.locator('#detail-message')).not_to_be_visible()
        record('Salvamento atrasado não atribui sucesso à oportunidade errada')
        pg.locator(a).click()
        pg.locator('#conference-summary > summary').click()
        pg.locator('#copy-summary').click()
        expect(pg.locator('#detail-message')).to_contain_text('copiado')
        record('Cópia do resumo corresponde à oportunidade atual', 'A7SA2L21' in pg.evaluate('window.reviewClipboard'))
        pg.evaluate('window.reviewDenyClipboard=true')
        pg.locator('#copy-summary').click()
        expect(pg.locator('#detail-message')).to_contain_text('manualmente')
        record('Falha de clipboard seleciona texto para cópia manual', pg.locator('#conference-text').evaluate('(e)=>e===document.activeElement && e.selectionEnd===e.value.length'))
        pg.locator('#account-select').select_option('Globex')
        pg.locator('#save-account').click()
        expect(pg.locator('#account-select')).to_be_disabled()
        route, row, body = pending.pop()
        row['version']+=1
        route.fulfill(status=409,json={'error':'a oportunidade foi alterada; atualize a tela'})
        expect(pg.locator('#detail-message')).to_contain_text('alterada')
        expect(pg.locator('#account-select')).to_have_value('Acme Corporation')
        record('Conflito de versão descarta rascunho antigo e apresenta aviso')
        pg.screenshot(path=str(HERE/'fixture-conflict.png'), full_page=True)
        record('Fixture não consulta o classificador', all(c['path']!='/api/classify' for c in api_calls))
        ctx.close()
        record('Nenhum erro JavaScript não tratado', not errors, errors)
        record('Nenhuma tentativa de escrita comercial na aplicação real', not blocked, blocked)
    finally:
        browser.close()
        report={'browser':'Chromium via Microsoft Edge headless','checks':checks,'observations':observations,'page_errors':errors,'blocked_real_writes':blocked,'live_model_calls':0}
        (HERE/'browser-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'checks':len(checks),'passed':sum(c['passed'] for c in checks),'observations':observations,'page_errors':errors,'blocked':blocked},ensure_ascii=False))
