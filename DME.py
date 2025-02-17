import pygame
import math
import sys
import time

# -------------------------------------------------------------------------------------
# PYGAME WINDOW SETUP
# -------------------------------------------------------------------------------------
WIDTH, HEIGHT = 800, 600
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("DME Simulation")
clock = pygame.time.Clock()

# -------------------------------------------------------------------------------------
# CONSTANTS AND CONFIG
# -------------------------------------------------------------------------------------
# DME station location (in pixels, but 1 px = 1 mile for demonstration)
DME_X = 600
DME_Y = 300

# Airplane size and initial position
PLANE_SIZE = 20
plane_x = 200
plane_y = 200
dragging = False

# DME timing parameters
MICROSECS_PER_MILE_ROUNDTRIP = 5.37  # approx 5.37 us for radio wave to go 1 mile out and back
DME_REPLY_DELAY_US = 50.0           # the standard 50 us delay
PING_INTERVAL = 3.0                 # seconds between pings

# We'll track the last measured DME distance and the time of the last ping
last_measured_distance = 0.0
last_ping_time = 0.0
time_of_next_ping = PING_INTERVAL

# Font for text
font = pygame.font.SysFont(None, 26)

# -------------------------------------------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------------------------------------------
def actual_distance_miles(px, py, dx, dy):
    """Return the geometric distance in miles (1 px = 1 mile)."""
    return math.hypot(px - dx, py - dy)

def dme_measure_distance(px, py, dx, dy):
    """
    Simulate a DME measurement:
      1) Actual distance d
      2) Round trip time (ideal) = 2*d*5.37 us
      3) Station adds 50 us
      4) Plane subtracts 50 us => leftover is 2*d*5.37
      5) Computed distance = leftover / (2*5.37)
    Returns the "DME-computed" distance in miles.
    """
    d = actual_distance_miles(px, py, dx, dy)
    ideal_rtt = 2.0 * d * MICROSECS_PER_MILE_ROUNDTRIP
    # Station adds 50 us
    total_rtt = ideal_rtt + DME_REPLY_DELAY_US
    # Plane subtracts 50 us
    plane_time = total_rtt - DME_REPLY_DELAY_US
    # Convert time back to distance
    dme_distance = plane_time / (2.0 * MICROSECS_PER_MILE_ROUNDTRIP)
    return dme_distance

# -------------------------------------------------------------------------------------
# MAIN LOOP
# -------------------------------------------------------------------------------------
start_time = time.time()

while True:
    dt = clock.tick(30) / 1000.0  # dt in seconds
    current_time = time.time() - start_time

    # Handle events
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

    # Constrain plane inside window
    plane_x = max(0, min(WIDTH - PLANE_SIZE, plane_x))
    plane_y = max(0, min(HEIGHT - PLANE_SIZE, plane_y))

    # Check if it's time to ping the DME
    if current_time >= time_of_next_ping:
        # Perform a DME measurement
        last_measured_distance = dme_measure_distance(plane_x, plane_y, DME_X, DME_Y)
        last_ping_time = current_time
        time_of_next_ping += PING_INTERVAL

    # ---------------------------------------------------------------------------------
    # DRAW
    # ---------------------------------------------------------------------------------
    screen.fill((0,0,0))  # Black background

    # 1) Draw the DME station
    pygame.draw.circle(screen, (255, 0, 0), (DME_X, DME_Y), 8)

    # 2) Draw the plane (yellow box)
    pygame.draw.rect(screen, (255, 255, 0), (plane_x, plane_y, PLANE_SIZE, PLANE_SIZE))

    # 3) Draw a line from plane to DME (optional, just for clarity)
    pygame.draw.line(screen, (100,100,100), (plane_x + PLANE_SIZE/2, plane_y + PLANE_SIZE/2),
                     (DME_X, DME_Y), 1)

    # 4) Show distances
    actual_dist = actual_distance_miles(plane_x + PLANE_SIZE/2, plane_y + PLANE_SIZE/2, DME_X, DME_Y)

    # Next ping countdown
    time_to_ping = time_of_next_ping - current_time
    if time_to_ping < 0: 
        time_to_ping = 0.0

    text_lines = [
        f"Actual distance to DME: {actual_dist:.2f} miles",
        f"Last DME measured distance: {last_measured_distance:.2f} miles",
        f"Next ping in: {time_to_ping:.1f} s",
    ]

    y_offset = 10
    for line in text_lines:
        surf = font.render(line, True, (255,255,255))
        screen.blit(surf, (10, y_offset))
        y_offset += 30

    pygame.display.flip()
