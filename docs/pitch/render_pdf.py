"""Renderiza deck.html a PDF en formato 16:9 (1920×1080 px → 20×11.25 in)."""
import os
from playwright.sync_api import sync_playwright

DECK = '/Users/diego/Documents/proyectos/web/docs/pitch/deck.html'
OUT = '/Users/diego/Documents/proyectos/web/docs/pitch/Matute-Guide-Pitch.pdf'


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})
        page.goto(f'file://{DECK}')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2000)  # carga de fonts + imágenes

        page.pdf(
            path=OUT,
            width='1920px',
            height='1080px',
            print_background=True,
            margin={'top': '0', 'right': '0', 'bottom': '0', 'left': '0'},
            prefer_css_page_size=True,
            scale=1.0,
        )
        browser.close()
    sz = os.path.getsize(OUT) / 1024 / 1024
    print(f'✓ {OUT}  ({sz:.1f} MB)')


if __name__ == '__main__':
    main()
