"""Read-only browser reconnaissance. Authentication is the only permitted POST."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

HERE = Path(__file__).resolve().parent
APP = HERE.parents[1]
BASE = 'http://127.0.0.1:8766'

with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=True)
    context = browser.new_context(viewport={'width': 1440, 'height': 1000})
    blocked = []
    def guard(route):
        request = route.request
        if request.method not in ('GET', 'HEAD') and request.url not in (BASE+'/api/login', BASE+'/api/logout'):
            blocked.append({'method': request.method, 'url': request.url})
            route.abort()
        else:
            route.continue_()
    context.route('**/api/**', guard)
    page = context.new_page()
    try:
        page.goto(BASE)
        page.wait_for_load_state('networkidle')
        (HERE/'login-dom.txt').write_text(page.locator('body').aria_snapshot(), encoding='utf-8')
        code = json.loads((APP/'.local/access-codes.json').read_text())['admin']
        page.get_by_label('Código de acesso local').fill(code)
        page.get_by_role('button', name='Acessar carteira').click()
        expect(page.locator('#shell')).to_be_visible()
        page.wait_for_load_state('networkidle')
        expect(page.locator('#rows tr')).to_have_count(20)
        (HERE/'desktop-dom.txt').write_text(page.locator('body').aria_snapshot(), encoding='utf-8')
        page.screenshot(path=str(HERE/'desktop.png'), full_page=True)
        print(json.dumps({'rows': page.locator('#rows tr').count(), 'title': page.title(), 'blocked': blocked}))
    finally:
        if page.locator('#shell').is_visible():
            page.get_by_role('button', name='Sair', exact=True).click()
            expect(page.locator('#login')).to_be_visible()
        browser.close()
