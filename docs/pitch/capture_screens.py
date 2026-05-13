"""Captura screenshots de las páginas clave de Matute Guide para el pitch deck."""
import os
from playwright.sync_api import sync_playwright

BASE = 'http://localhost:5001'
OUT = '/Users/diego/Documents/proyectos/web/docs/pitch/shots'
os.makedirs(OUT, exist_ok=True)

ALVARO = ('alvaro.diaz@alumnos.udg.mx', 'Estudiante1!')
ADMIN = ('admin@udg.mx', 'Admin1234!')


def login(page, email, password):
    page.goto(f'{BASE}/auth/login')
    page.wait_for_load_state('networkidle')
    page.fill('input#email', email)
    page.fill('input#password', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')


def shot(page, path, full_page=True):
    page.screenshot(path=f'{OUT}/{path}', full_page=full_page)
    print(f'  ✓ {path}')


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={'width': 1440, 'height': 900},
                                  device_scale_factor=2)

        page = ctx.new_page()
        for url, name in [
            ('/', 'landing.png'),
            ('/auth/login', 'login.png'),
            ('/oferta', 'oferta.png'),
            ('/salones', 'salones.png'),
            ('/salones/A-203', 'salon-detail.png'),
            ('/mapa', 'mapa.png'),
            ('/components', 'components-demo.png'),
        ]:
            page.goto(f'{BASE}{url}')
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(800)
            shot(page, name, full_page=(name != 'mapa.png'))
        page.close()

        page = ctx.new_page()
        login(page, *ALVARO)
        page.goto(f'{BASE}/dashboard')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(1000)
        shot(page, 'student-dashboard.png')

        page.goto(f'{BASE}/dashboard?tab=horario')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(1000)
        try:
            page.click('button[data-tab="horario"]')
            page.wait_for_timeout(500)
        except Exception:
            pass
        shot(page, 'student-horario.png')

        page.goto(f'{BASE}/inscripciones')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(1000)
        shot(page, 'student-inscripciones.png')

        page.goto(f'{BASE}/tramites')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(800)
        shot(page, 'student-tramites.png')
        page.close()

        page = ctx.new_page()
        login(page, *ADMIN)
        page.goto(f'{BASE}/admin')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2000)
        shot(page, 'admin-dashboard.png')

        page.goto(f'{BASE}/admin/usuarios')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(1500)
        shot(page, 'admin-usuarios.png')

        page.goto(f'{BASE}/admin/horarios')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(800)
        try:
            page.click('#btn-cargar-carrera')
            page.wait_for_timeout(1500)
        except Exception:
            pass
        shot(page, 'admin-horarios.png')

        page.goto(f'{BASE}/admin/salones')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(1500)
        shot(page, 'admin-salones.png')

        page.goto(f'{BASE}/admin/reportes')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(1500)
        shot(page, 'admin-reportes.png')

        page.close()

        ctx_m = browser.new_context(
            viewport={'width': 390, 'height': 844},
            device_scale_factor=3,
        )
        page = ctx_m.new_page()
        login(page, *ALVARO)
        page.goto(f'{BASE}/dashboard')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(1500)
        shot(page, 'mobile-dashboard.png', full_page=False)
        page.close()

        browser.close()
    print(f'\n✓ {len(os.listdir(OUT))} screenshots en {OUT}')


if __name__ == '__main__':
    main()
