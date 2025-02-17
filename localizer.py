import pygame
import math
import sys

# -------------------------------------------------------------------------------------
# 1) BASIC SETUP
# -------------------------------------------------------------------------------------
WIDTH, HEIGHT = 800, 800
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Localizer (Top View) Simulation")
clock = pygame.time.Clock()

# -------------------------------------------------------------------------------------
# 2) CONFIGURATION / PARAMETERS
# -------------------------------------------------------------------------------------
# Runway threshold: We'll place it near the right side (x=700, y=300).
RUNWAY_X = 400
RUNWAY_Y = 100

# We'll define 3 angles (in radians), so lines converge at the runway threshold:
#  - center line is angle 0° => extends left horizontally
#  - left line is angle +2° => slightly "fanned" upward
#  - right line is angle -2° => slightly "fanned" downward
ANGLE_CENTER = math.radians(0.0)
ANGLE_LEFT   = math.radians(10.0)
ANGLE_RIGHT  = math.radians(-10.0)

# We create a smooth localizer "difference" function using a hyperbolic tangent (tanh).
# The smaller this SCALE, the sharper the transition; the bigger, the smoother.
TRANSITION_SCALE = 20.0

# Airplane representation
PLANE_SIZE = 20
# Start plane around x=400, y=300 => roughly on the center line
plane_x = 400 - PLANE_SIZE // 2
plane_y = 600 
dragging = False

# We'll display a localizer dial near top-left
DIAL_CENTER_X = 150
DIAL_CENTER_Y = 100
DIAL_RADIUS   = 50

# -------------------------------------------------------------------------------------
# 3) MATH FOR LINES
# -------------------------------------------------------------------------------------
def localizer_x(y, angle):
    """
    Return the x-position for a line that converges at (RUNWAY_X, RUNWAY_Y) 
    with slope defined by 'angle' in radians.

    Conceptually:
       dx = (some function of y)
       x  = RUNWAY_X - tan(angle)*(RUNWAY_Y - y)

    So that at y=RUNWAY_Y, x=RUNWAY_X for all lines, 
    and as y changes, x fans out depending on angle.
    """
    dy = (RUNWAY_Y - y)
    return RUNWAY_X - math.tan(angle)*dy

def x_left_line(y):
    return localizer_x(y, ANGLE_LEFT)

def x_center_line(y):
    return localizer_x(y, ANGLE_CENTER)

def x_right_line(y):
    return localizer_x(y, ANGLE_RIGHT)

# -------------------------------------------------------------------------------------
# 4) SMOOTH LOCALIZER SIGNALS
#    We'll measure how far left/right the plane is from the "center line."
#    If plane_x < center => "90Hz" is stronger. If plane_x > center => "150Hz" is stronger.
# -------------------------------------------------------------------------------------
def localizer_90_strength(px, py):
    """
    Yields a value from 0..1, stronger if the plane is to the LEFT of the center line.
    We'll do a smooth transition using tanh.
    """
    center_x = x_center_line(py)  # The ideal center x for this y
    dist = px - center_x          # If dist<0 => plane is left, dist>0 => plane is right

    # We want "90Hz ~1" if dist<<0, "90Hz ~0" if dist>>0
    # Let's define val = 0.5 + 0.5*tanh(-dist/TRANSITION_SCALE)
    val = 0.5 + 0.5 * math.tanh(-dist / TRANSITION_SCALE)
    return val

def localizer_150_strength(px, py):
    """
    Yields a value from 0..1, stronger if the plane is to the RIGHT of the center line.
    """
    center_x = x_center_line(py)
    dist = px - center_x

    # If dist>0 => plane is right => 150Hz ~1
    # val = 0.5 + 0.5*tanh(dist/TRANSITION_SCALE)
    val = 0.5 + 0.5 * math.tanh(dist / TRANSITION_SCALE)
    return val

def localizer_diff(px, py):
    """
    localizer_90_strength - localizer_150_strength.
      >0 => plane is LEFT of center => needle should deflect to the RIGHT (fly right).
      <0 => plane is RIGHT => needle deflects LEFT (fly left).
      =0 => exactly on center line.
    """
    s90 = localizer_90_strength(px, py)
    s150 = localizer_150_strength(px, py)
    return s90 - s150

# -------------------------------------------------------------------------------------
# 5) DRAWING FUNCTIONS
# -------------------------------------------------------------------------------------
def draw_background_lobes():
    """
    Color the background to show areas where 90Hz vs 150Hz is dominant (red vs blue).
    We'll do a coarse grid for performance.
    """
    step = 8
    for x in range(0, WIDTH, step):
        for y in range(0, HEIGHT, step):
            s90 = localizer_90_strength(x, y)
            s150 = localizer_150_strength(x, y)
            ratio = s150 / (s90 + 1e-6)
            red   = min(255, int(255 * ratio/(1+ratio)))
            blue  = min(255, int(255 * (1/(1+ratio))))
            color = (red, 0, blue)
            rect = pygame.Rect(x, y, step, step)
            pygame.draw.rect(screen, color, rect)

def draw_localizer_lines():
    """
    Draw three lines:
     - left boundary (blueish)
     - center line (white)
     - right boundary (redish)
    All converge at (RUNWAY_X, RUNWAY_Y).
    We'll sample 'y' from 0..HEIGHT in small steps, compute x for each line, and connect them.
    """
    pts_left   = []
    pts_center = []
    pts_right  = []
    for y in range(0, HEIGHT, 10):
        pts_left.append((x_left_line(y),   y))
        pts_center.append((x_center_line(y), y))
        pts_right.append((x_right_line(y),  y))

    pygame.draw.lines(screen, (100,100,255), False, pts_left, 2)   # left boundary => bluish
    pygame.draw.lines(screen, (255,255,255), False, pts_center, 2) # center => white
    pygame.draw.lines(screen, (255,100,100), False, pts_right, 2)  # right boundary => reddish

    # Mark the runway threshold
    pygame.draw.circle(screen, (255,255,0), (RUNWAY_X, RUNWAY_Y), 5)

def draw_localizer_dial(diff):
    """
    A small "localizer" dial with a VERTICAL needle that moves left or right 
    based on 'diff'. If diff>0 => plane is left => needle is right. 
    If diff<0 => plane is right => needle is left.
    """
    # Dial circle
    pygame.draw.circle(screen, (160,160,160), (DIAL_CENTER_X, DIAL_CENTER_Y), DIAL_RADIUS, 0)
    pygame.draw.circle(screen, (0,0,0), (DIAL_CENTER_X, DIAL_CENTER_Y), DIAL_RADIUS, 2)

    # We'll clamp diff to [-1..+1] for full-scale deflection
    d = max(-1.0, min(1.0, diff))
    needle_max = 30

    # If diff>0 => plane is left => needle on the RIGHT => + offset
    # We'll do offset = +d * needle_max
    offset = d * needle_max

    needle_len = 40
    nx = DIAL_CENTER_X + offset
    y1 = DIAL_CENTER_Y - needle_len//2
    y2 = DIAL_CENTER_Y + needle_len//2
    pygame.draw.line(screen, (255,255,0), (nx, y1), (nx, y2), 4)

    # Center tick
    pygame.draw.line(screen, (255,255,255),
                     (DIAL_CENTER_X, DIAL_CENTER_Y - 5),
                     (DIAL_CENTER_X, DIAL_CENTER_Y + 5), 2)

    # Label "LOC"
    font = pygame.font.SysFont(None, 24)
    label = font.render("LOC", True, (255,255,255))
    screen.blit(label, (DIAL_CENTER_X - 14, DIAL_CENTER_Y - DIAL_RADIUS - 20))

# -------------------------------------------------------------------------------------
# 6) MAIN LOOP
# -------------------------------------------------------------------------------------
while True:
    clock.tick(30)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            plane_rect = pygame.Rect(plane_x, plane_y, PLANE_SIZE, PLANE_SIZE)
            if plane_rect.collidepoint(mx, my):
                dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            dragging = False
        elif event.type == pygame.MOUSEMOTION and dragging:
            mx, my = event.pos
            plane_x = mx - PLANE_SIZE // 2
            plane_y = my - PLANE_SIZE // 2

    # Bound plane within the window
    plane_x = max(0, min(WIDTH - PLANE_SIZE, plane_x))
    plane_y = max(0, min(HEIGHT - PLANE_SIZE, plane_y))

    # DRAW
    screen.fill((0,0,0))

    # 1) Background coloring to show 90Hz/150Hz dominance
    draw_background_lobes()

    # 2) Draw the localizer lines (left boundary, center, right boundary)
    draw_localizer_lines()

    # 3) Draw the plane
    pygame.draw.rect(screen, (255,255,0), (plane_x, plane_y, PLANE_SIZE, PLANE_SIZE))

    # 4) Compute localizer difference => drive the vertical needle
    diff = localizer_diff(plane_x + PLANE_SIZE // 2, plane_y + PLANE_SIZE // 2)
    draw_localizer_dial(diff)

    pygame.display.flip()
