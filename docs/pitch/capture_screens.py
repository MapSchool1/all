"""Captura screenshots con login real esperando la navegación."""
import os
from playwright.sync_api import sync_playwright

BASE = 'http://localhost:5001'
OUT = '/Users/diego/Documents/proyectos/web/docs/pitch/shots'
os.makedirs(OUT, exist_ok=True)

ALVARO = ('alvaro.diaz@alumnos.udg.mx', 'Estudiante1!')
ADMIN = ('admin@udg.mx', 'Admin1234!')


def login(page, email, password, expect_path):
    """Hace login y ESPERA explícitamente la redirección."""
    page.goto(f'{BASE}/auth/login')
    page.wait_for_load_state('domcontentloaded')
    page.fill('input#email', email)
    page.fill('input#password', password)
    # JS hace 2 fetches y luego window.location.href = s.redirect.
    # Esperamos por la URL final.
    page.click('button[type="submit"]')
    page.wait_for_url(f'**{expect_path}**', timeout=15000)
    # Las páginas autenticadas tienen SSE → networkidle nunca termina.
    # Usamos DOMContentLoaded + un timeout fijo.
    page.wait_for_load_state('domcontentloaded')
    page.wait_for_timeout(1500)
    assert expect_path in page.url, \
        f'Login falló: esperado {expect_path}, estoy en {page.url}'
    print(f'  ✓ login OK ({email}) → {page.url}')


def shot(page, path, full_page=True):
    page.screenshot(path=f'{OUT}/{path}', full_page=full_page)
    print(f'  ✓ {path}')


def new_ctx(browser, mobile=False):
    """Contexto limpio (cookies aisladas) por usuario."""
    if mobile:
        return browser.new_context(
            viewport={'width': 390, 'height': 844}, device_scale_factor=3)
    return browser.new_context(
        viewport={'width': 1440, 'height': 900}, device_scale_factor=2)


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        # ===== Públicas =====
        ctx = new_ctx(browser)
        page = ctx.new_page()
        for url, name in [
            ('/', 'landing.png'),
            ('/auth/login', 'login.png'),
            ('/auth/register', 'register.png'),
            ('/oferta', 'oferta.png'),
            ('/salones', 'salones.png'),
            ('/salones/A-203', 'salon-detail.png'),
            ('/mapa', 'mapa.png'),
            ('/components', 'components-demo.png'),
        ]:
            page.goto(f'{BASE}{url}')
            page.wait_for_load_state('domcontentloaded')
            page.wait_for_timeout(800)
            shot(page, name, full_page=(name != 'mapa.png'))
        ctx.close()

        # ===== ESTUDIANTE — Álvaro (contexto limpio) =====
        ctx = new_ctx(browser)
        page = ctx.new_page()
        login(page, *ALVARO, expect_path='/dashboard')
        page.wait_for_timeout(1500)
        shot(page, 'student-dashboard.png')

        page.click('button[data-tab="horario"]')
        page.wait_for_timeout(1200)
        shot(page, 'student-horario.png')

        page.click('button[data-tab="calificaciones"]')
        page.wait_for_timeout(800)
        shot(page, 'student-calificaciones.png')

        page.goto(f'{BASE}/inscripciones')
        page.wait_for_load_state('domcontentloaded')
        page.wait_for_timeout(2500)
        shot(page, 'student-inscripciones.png')

        page.goto(f'{BASE}/tramites')
        page.wait_for_load_state('domcontentloaded')
        page.wait_for_timeout(800)
        shot(page, 'student-tramites.png')

        page.goto(f'{BASE}/horario')
        page.wait_for_load_state('domcontentloaded')
        page.wait_for_timeout(2000)
        shot(page, 'student-horario-builder.png')
        ctx.close()

        # ===== ADMIN (contexto limpio, sin cookies de Álvaro) =====
        ctx = new_ctx(browser)
        page = ctx.new_page()
        login(page, *ADMIN, expect_path='/admin')
        page.wait_for_timeout(2500)
        shot(page, 'admin-dashboard.png')

        page.goto(f'{BASE}/admin/usuarios')
        page.wait_for_load_state('domcontentloaded')
        page.wait_for_timeout(2000)
        shot(page, 'admin-usuarios.png')

        page.goto(f'{BASE}/admin/horarios')
        page.wait_for_load_state('domcontentloaded')
        page.wait_for_timeout(800)
        try:
            page.click('#btn-cargar-carrera')
            page.wait_for_timeout(2000)
        except Exception as e:
            print(f'    ! cargar-carrera: {e}')
        shot(page, 'admin-horarios.png')

        page.goto(f'{BASE}/admin/salones')
        page.wait_for_load_state('domcontentloaded')
        page.wait_for_timeout(2000)
        shot(page, 'admin-salones.png')

        page.goto(f'{BASE}/admin/carreras')
        page.wait_for_load_state('domcontentloaded')
        page.wait_for_timeout(1500)
        shot(page, 'admin-carreras.png')

        page.goto(f'{BASE}/admin/reportes')
        page.wait_for_load_state('domcontentloaded')
        page.wait_for_timeout(2000)
        shot(page, 'admin-reportes.png')

        page.goto(f'{BASE}/admin/tramites')
        page.wait_for_load_state('domcontentloaded')
        page.wait_for_timeout(1500)
        shot(page, 'admin-tramites.png')
        ctx.close()

        # ===== MÓVIL =====
        ctx_m = new_ctx(browser, mobile=True)
        page = ctx_m.new_page()
        login(page, *ALVARO, expect_path='/dashboard')
        page.wait_for_timeout(1800)
        shot(page, 'mobile-dashboard.png', full_page=False)

        page.click('button[data-tab="horario"]')
        page.wait_for_timeout(1200)
        shot(page, 'mobile-horario.png', full_page=False)
        page.close()

        browser.close()
    print(f'\n✓ {len(os.listdir(OUT))} screenshots en {OUT}')


if __name__ == '__main__':
    main()
