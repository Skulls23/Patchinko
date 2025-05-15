import pygame
import random
import math
import time

pygame.init()
WIDTH, HEIGHT = 600, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pachinko Scrolling Suivi Balle")
clock = pygame.time.Clock()

# Couleurs
WHITE = (255, 255, 255)
GREY = (220, 220, 220)
BLUE = (100, 100, 255)
RED = (255, 100, 100)
BLACK = (0, 0, 0)

# Constantes
BALL_RADIUS = 8
PEG_RADIUS = 6
GRAVITY = 0.3

NUM_ROWS = 80             # Grande hauteur
PEGS_PER_ROW = 10
PEG_SPACING_X = WIDTH // PEGS_PER_ROW
PEG_SPACING_Y = 60

ZONE_HEIGHT = 100
ZONES = 6
zone_width = WIDTH // ZONES
scores = [100, 200, 500, 0, 500, 100]

Y_TARGET = 150  # position fixe de la balle sur l'écran (caméra suit)

# Classe Balle
class Ball:
    def __init__(self, x):
        self.x = x
        self.real_y = 0
        self.vx = 0
        self.vy = 0

    def update(self):
        self.vy += GRAVITY
        self.real_y += self.vy

        self.x += self.vx
        if self.x < BALL_RADIUS:
            self.x = BALL_RADIUS
            self.vx *= -0.7
        elif self.x > WIDTH - BALL_RADIUS:
            self.x = WIDTH - BALL_RADIUS
            self.vx *= -0.7

    def draw(self, offset_y):
        screen_y = self.real_y - offset_y
        if -50 < screen_y < HEIGHT + 50:
            pygame.draw.circle(screen, RED, (int(self.x), int(screen_y)), BALL_RADIUS)

# Génération des pegs
pegs = []
for row in range(NUM_ROWS):
    y = row * PEG_SPACING_Y
    offset = (row % 2) * (PEG_SPACING_X // 2)
    for i in range(PEGS_PER_ROW):
        x = i * PEG_SPACING_X + offset
        if 0 < x < WIDTH:
            pegs.append((x, y))

def draw_pegs(offset_y):
    for x, y in pegs:
        screen_y = y - offset_y
        if -10 < screen_y < HEIGHT + 10:
            pygame.draw.circle(screen, BLUE, (int(x), int(screen_y)), PEG_RADIUS)

def draw_zones(offset_y):
    base_y = NUM_ROWS * PEG_SPACING_Y
    y = base_y - offset_y
    for i in range(ZONES):
        x = i * zone_width
        pygame.draw.rect(screen, GREY, (x, y, zone_width, ZONE_HEIGHT))
        pygame.draw.rect(screen, BLACK, (x, y, zone_width, ZONE_HEIGHT), 2)
        font = pygame.font.SysFont(None, 28)
        text = font.render(str(scores[i]), True, BLACK)
        screen.blit(text, (x + zone_width // 2 - 15, y + 10))

# Collisions
def check_collision(ball):
    for px, py in pegs:
        dx = ball.x - px
        dy = ball.real_y - py
        dist = math.hypot(dx, dy)
        min_dist = BALL_RADIUS + PEG_RADIUS

        if dist < min_dist and dist != 0:
            # Normalisation du vecteur collision
            nx = dx / dist
            ny = dy / dist

            # Correction de la position
            overlap = min_dist - dist
            ball.x += nx * overlap
            ball.real_y += ny * overlap

            # Calcul du rebond : réflexion simple sur la normale
            v_dot_n = ball.vx * nx + ball.vy * ny
            ball.vx -= 2 * v_dot_n * nx
            ball.vy -= 2 * v_dot_n * ny

            # Réduction de vitesse (énergie perdue)
            ball.vx *= 0.9
            ball.vy *= 0.9

            # Ajout d'une toute petite variation aléatoire pour éviter blocage parfait
            ball.vx += random.uniform(-0.1, 0.1)


balls = []
total_score = 0

# Lancer la balle dès le début
balls.append(Ball(WIDTH // 2))

# Boucle principale
running = True
finished = False
while running:
    dt = clock.tick(60) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(WHITE)

    if balls:
        ball = balls[0]
        ball.update()
        check_collision(ball)

        # Caméra suit la balle
        offset_y = ball.real_y - Y_TARGET
    else:
        offset_y = NUM_ROWS * PEG_SPACING_Y - HEIGHT  # montre le bas fixe

    draw_pegs(offset_y)
    draw_zones(offset_y)

    for ball in balls[:]:
        ball.draw(offset_y)

        # Si la balle atteint le bas du monde
        if ball.real_y > NUM_ROWS * PEG_SPACING_Y - ZONE_HEIGHT:
            zone_index = int(ball.x // zone_width)
            if 0 <= zone_index < len(scores):
                total_score += scores[zone_index]
            balls.remove(ball)
            finished = True

    # Affichage score
    font = pygame.font.SysFont(None, 32)
    score_text = font.render(f"Score: {total_score}", True, BLACK)
    screen.blit(score_text, (10, 10))

    if finished:
        text = font.render("Fin ! Appuie sur Échap pour quitter", True, BLACK)
        screen.blit(text, (WIDTH // 2 - 150, HEIGHT // 2))

    pygame.display.flip()

pygame.quit()
