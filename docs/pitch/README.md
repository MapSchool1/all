# Matute Guide — Pitch Deck

Slide deck visual para presentar el proyecto.

## Archivos

- **`Matute-Guide-Pitch.pdf`** — versión final lista para presentar (14 slides 16:9, ~2.8 MB)
- `deck.html` — fuente HTML editable con el branding MapSchool aplicado
- `shots/` — screenshots reales capturados de las páginas web del proyecto
- `shots/mobile-mockup.png` — mockup de iPhone con el dashboard estudiante
- `capture_screens.py` — Playwright que toma los screenshots
- `mockup_phone.py` — Pillow que compone el mockup móvil
- `render_pdf.py` — Playwright que renderiza el HTML → PDF

## Regenerar

```bash
# 1. Levantar Flask
source ../../.venv/bin/activate && python ../../run.py &

# 2. (Opcional) recapturar screenshots
python capture_screens.py

# 3. (Opcional) regenerar mockup móvil
python mockup_phone.py

# 4. Renderizar PDF
python render_pdf.py
```

## Contenido de los 14 slides

1. **Portada** — branding navy + tagline
2. **Problema** — tabla de fricciones actuales en CUValles
3. **Solución** — antes vs con Matute Guide
4. **Landing** — screenshot real
5. **Estudiante / Dashboard** — caso estrella con conflicto Mié 11:00
6. **Schedule grid** — bloques color-coded + conflicto pulsante
7. **Mapa + salones** — vistas SVG
8. **Móvil** — mockup iPhone con la app real
9. **Panel admin** — KPIs y CRUD
10. **Sistema de diseño** — MapSchool y /components demo
11. **Arquitectura** — 3 capas: web, mobile, backend
12. **Calidad** — 58 tests + 0 issues + audit log
13. **Roadmap** — listo vs siguiente sprint
14. **CTA** — clonar repo + cuentas demo
