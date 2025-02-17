import pygame
import math
import sys

# -------------------------------------------------------------------------------------
# WINDOW & PYGAME INIT
# -------------------------------------------------------------------------------------
WIDTH, HEIGHT = 800, 600
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Smooth Glideslope Needle with Converging Lines")
clock = pygame.time.Clock()

# -------------------------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------------------------
# 1) Runway threshold (where all lines converge)
RUNWAY_X = 700
RUNWAY_Y = 500

# 2) Angles (in radians): top, middle, bottom
ANGLE_MIDDLE = math.radians(9.0)   # ~9° (white line)
ANGLE_TOP    = math.radians(15.0)   # ~15° (blue line)
ANGLE_BOTTOM = math.radians(3.0)   # ~3° (red line)

# 3) Airplane
PLANE_SIZE = 20
START_PLANE_X = 100  # We'll start plane at x=100, on the middle line

# 4) Glideslope dial location
DIAL_CENTER_X = 700
DIAL_CENTER_Y = 100
DIAL_RADIUS   = 50

# 5) Tanh transition scale for signal strengths
#    Smaller => transitions more sharply around the line,
#    Larger => more gradual
TRANSITION_SCALE = 20.0

# -------------------------------------------------------------------------------------
# GEOMETRY: LINES
# -------------------------------------------------------------------------------------
def line_y(x, angle):
    """
    Returns y for a line converging at (RUNWAY_X, RUNWAY_Y) with slope 'angle'.
    """
    dx = (RUNWAY_X - x)
    return RUNWAY_Y - math.tan(angle) * dx

def y_top_line(x):
    return line_y(x, ANGLE_TOP)

def y_middle_line(x):
    return line_y(x, ANGLE_MIDDLE)

def y_bottom_line(x):
    return line_y(x, ANGLE_BOTTOM)

# -------------------------------------------------------------------------------------
# SMOOTH 90 Hz vs 150 Hz SIGNALS
# -------------------------------------------------------------------------------------
def signal_strength_90hz(px, py):
    """
    Stronger above the middle line => dist<0 => s90 ~ 1, 
    but smoothly transitions across dist=0 using tanh.
    """
    y_ideal = y_middle_line(px)
    dist = py - y_ideal
    # val goes from ~1 if dist << 0 to ~0 if dist >> 0
    val = 0.5 + 0.5 * math.tanh(-dist / TRANSITION_SCALE)
    return val

def signal_strength_150hz(px, py):
    """
    Stronger below the middle line => dist>0 => s150 ~ 1,
    smoothly transitions using tanh as well.
    """
    y_ideal = y_middle_line(px)
    dist = py - y_ideal
    val = 0.5 + 0.5 * math.tanh(dist / TRANSITION_SCALE)
    return val

def glideslope_diff(px, py):
    """
    90 Hz - 150 Hz => ranges from +1 (well above) to -1 (well below).
    Exactly 0 when on the middle line => needle centered.
    """
    s90 = signal_strength_90hz(px, py)
    s150 = signal_strength_150hz(px, py)
    return s90 - s150

# -------------------------------------------------------------------------------------
# DRAWING FUNCTIONS
# -------------------------------------------------------------------------------------
def draw_background():
    """
    Fill the background with red/blue to show which signal is stronger at each point.
    We'll do a coarse grid for performance.
    """
    step = 8
    for x in range(0, WIDTH, step):
        for y in range(0, HEIGHT, step):
            s90 = signal_strength_90hz(x, y)
            s150 = signal_strength_150hz(x, y)
            ratio = s150 / (s90 + 1e-6)
            red   = min(255, int(255 * ratio / (1 + ratio)))
            blue  = min(255, int(255 * (1 / (1 + ratio))))
            color = (red, 0, blue)
            pygame.draw.rect(screen, color, (x, y, step, step))

def draw_three_converging_lines():
    """
    Draw top, middle, bottom lines (meeting at (RUNWAY_X, RUNWAY_Y)).
    Each has its own slope so they truly converge at one point.
    """
    pts_top = []
    pts_mid = []
    pts_bot = []
    for x in range(0, WIDTH, 10):
        pts_top.append((x, y_top_line(x)))
        pts_mid.append((x, y_middle_line(x)))
        pts_bot.append((x, y_bottom_line(x)))

    pygame.draw.lines(screen, (100,100,255), False, pts_top, 2)      # top => bluish
    pygame.draw.lines(screen, (255,255,255), False, pts_mid, 2)      # middle => white
    pygame.draw.lines(screen, (255,100,100), False, pts_bot, 2)      # bottom => reddish

    # Mark the runway threshold
    pygame.draw.circle(screen, (255,255,0), (RUNWAY_X, RUNWAY_Y), 5)

def draw_glideslope_dial(diff):
    """
    Small dial at (DIAL_CENTER_X, DIAL_CENTER_Y) with a horizontal needle 
    that moves smoothly up/down as 'diff' goes from +1 to -1.
    """
    # Dial face
    pygame.draw.circle(screen, (160,160,160), (DIAL_CENTER_X, DIAL_CENTER_Y), DIAL_RADIUS, 0)
    pygame.draw.circle(screen, (0,0,0), (DIAL_CENTER_X, DIAL_CENTER_Y), DIAL_RADIUS, 2)

    # Clamp diff to [-1, +1]
    d = max(-1.0, min(1.0, diff))
    needle_max = 30
    # If diff>0 => above => needle goes downward => negative offset
    offset = -d * needle_max

    needle_len = 40
    ny = DIAL_CENTER_Y + offset
    x1 = DIAL_CENTER_X - needle_len//2
    x2 = DIAL_CENTER_X + needle_len//2
    pygame.draw.line(screen, (255,255,0), (x1, ny), (x2, ny), 4)

    # Center tick
    pygame.draw.line(screen, (255,255,255),
                     (DIAL_CENTER_X - 5, DIAL_CENTER_Y),
                     (DIAL_CENTER_X + 5, DIAL_CENTER_Y), 2)

    # Label
    font = pygame.font.SysFont(None, 24)
    label = font.render("GS", True, (255,255,255))
    screen.blit(label, (DIAL_CENTER_X - 10, DIAL_CENTER_Y - DIAL_RADIUS - 20))

# -------------------------------------------------------------------------------------
# INITIALIZE PLANE ON THE MIDDLE LINE (so dial is centered at start)
# -------------------------------------------------------------------------------------
plane_x = START_PLANE_X
plane_y = y_middle_line(plane_x) - PLANE_SIZE // 2

# -------------------------------------------------------------------------------------
# MAIN LOOP
# -------------------------------------------------------------------------------------
dragging = False
while True:
    clock.tick(30)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if pygame.Rect(plane_x, plane_y, PLANE_SIZE, PLANE_SIZE).collidepoint(mx, my):
                dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            dragging = False
        elif event.type == pygame.MOUSEMOTION and dragging:
            mx, my = event.pos
            plane_x = mx - PLANE_SIZE // 2
            plane_y = my - PLANE_SIZE // 2

    # Bound plane to the screen
    plane_x = max(0, min(WIDTH - PLANE_SIZE, plane_x))
    plane_y = max(0, min(HEIGHT - PLANE_SIZE, plane_y))

    # Draw everything
    screen.fill((0,0,0))
    draw_background()
    draw_three_converging_lines()

    pygame.draw.rect(screen, (255,255,0), (plane_x, plane_y, PLANE_SIZE, PLANE_SIZE))

    # Smooth difference => needle
    diff = glideslope_diff(plane_x + PLANE_SIZE // 2, plane_y + PLANE_SIZE // 2)
    # diff = glideslope_diff(mx, my)
    draw_glideslope_dial(diff)

    pygame.display.flip()
