"""Compone un mockup de iPhone con el screenshot móvil."""
from PIL import Image, ImageDraw

SCREEN = '/Users/diego/Documents/proyectos/web/docs/pitch/shots/mobile-dashboard.png'
OUT = '/Users/diego/Documents/proyectos/web/docs/pitch/shots/mobile-mockup.png'

NAVY = (23, 40, 70)
SURFACE = (248, 249, 250)

# Phone frame: 432×888 (proporción ~iPhone 14 Pro con bezel)
FRAME_W, FRAME_H = 480, 980
BEZEL = 18
NOTCH_W, NOTCH_H = 130, 28

screen = Image.open(SCREEN).convert('RGB')
sw, sh = screen.size  # debe ser 390×844 @3x = 1170×2532

# Resize screenshot al área del display
display_w = FRAME_W - 2 * BEZEL
display_h = FRAME_H - 2 * BEZEL
screen_resized = screen.resize((display_w, display_h), Image.Resampling.LANCZOS)

# Compose
mockup = Image.new('RGBA', (FRAME_W, FRAME_H), (0, 0, 0, 0))
d = ImageDraw.Draw(mockup)

# Frame del teléfono (negro con border-radius)
RADIUS = 56
d.rounded_rectangle([0, 0, FRAME_W, FRAME_H], radius=RADIUS,
                    fill=(15, 15, 20, 255))

# Pegar el screenshot dentro
mask = Image.new('L', (display_w, display_h), 0)
md = ImageDraw.Draw(mask)
md.rounded_rectangle([0, 0, display_w, display_h], radius=RADIUS - BEZEL,
                     fill=255)
mockup.paste(screen_resized.convert('RGBA'),
             (BEZEL, BEZEL), mask)

# Notch
notch_x = (FRAME_W - NOTCH_W) // 2
d.rounded_rectangle([notch_x, BEZEL + 4, notch_x + NOTCH_W,
                     BEZEL + 4 + NOTCH_H], radius=14, fill=(15, 15, 20, 255))

# Speaker dot dentro del notch
d.ellipse([notch_x + NOTCH_W - 22, BEZEL + 14,
           notch_x + NOTCH_W - 12, BEZEL + 24], fill=(40, 40, 50, 255))

mockup.save(OUT, 'PNG', optimize=True)
print(f'✓ {OUT}')

# También un mockup del horario (usando otro screenshot móvil)
print('Capturando segundo screenshot móvil para horario...')
