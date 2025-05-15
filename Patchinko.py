import pygame
import random
import math
import time

pygame.init()
WIDTH, HEIGHT = 600, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pachinko Scrolling Suivi Balle Génération 61s")
clock = pygame.time.Clock()

# Couleurs
WHITE = (255, 255, 255)
GREY  = (220, 220, 220)
BLUE  = (100, 100, 255)
RED   = (255, 100, 100)
BLACK = (0, 0, 0)

BACKGROUND_LAYER_GAUCHE = (240, 240, 255, 230) # Bleu très clair avec un peu de transparence
BACKGROUND_LAYER_DROITE = (255, 240, 240, 230) # Rouge très clair avec un peu de transparence

#############
# CONSTANTS #
#############

TEXTE_GAUCHE = "TG"
TEXTE_DROITE = "TD"

BALL_RADIUS = 8
PEG_RADIUS  = 6
GRAVITY     = 1
MAX_VY      = 5  # vitesse max verticale (pixels/frame)

# Generation des Pegs (bloqueurs)
PEG_ROW_RATE        = 1 / 0.5  # 2 lignes par seconde (toutes les 0.5 secondes)
PEG_ROWS_PER_SECOND = PEG_ROW_RATE
PEG_ROW_INTERVAL    = 1 / PEG_ROWS_PER_SECOND
PEGS_PER_ROW  = 10
PEG_SPACING_X = WIDTH // PEGS_PER_ROW
PEG_SPACING_Y = 60
PEGS_DECALAGE_X_GAUCHE = -10 # Négatif car on le bouge vers la gauche
PEGS_DECALAGE_X_DROITE = 10

# Generation des boosters
BOOSTER_RADIUS    = 12
BOOSTER_TIME_GAIN = 5  # secondes ajoutées quand on touche un booster
BOOSTER_CHANCE    = 100  # 10% de chance par ligne
BOOSTER_COULEUR_AJOUT_GAUCHE = BLACK # (0, 200, 0)
BOOSTER_COULEUR_AJOUT_DROITE = WHITE # (200, 0, 200)

ZONE_HEIGHT = 100
ZONES = 6

# Amortissement lors des rebonds
AMORTISSEMENT_REBOND_X = 0.9 # amortir plus fort latéralement?
AMORTISSEMENT_REBOND_Y = 0.9 # amortir moins la verticale pour plus de rebond naturel?

Y_TARGET = 150  # position fixe de la balle sur l'écran (caméra suit)
GENERATION_DURATION = 61  # secondes avant la fin de la generation de peg

NOMBRE_ECRAN_DEVANT_LA_BALLE = 2  # On genere les pegs jusqu'a X écrans en dessous de la balle pour eviter qu'elle aille plus vite que la gen

# Ajouter au début du code, juste après les constantes déjà définies :
TRAIL_LENGTH = 15  # nombre de positions mémorisées pour le trail

#############
# VARIABLES #
#############

zone_width = WIDTH // ZONES
scores = [100, 200, 500, 0, 500, 100]

next_row_index = 0

# Dans la classe Ball, ajoute un attribut pour mémoriser le trail dans __init__ :
class Ball:
    def __init__(self, x):
        self.x      = x
        self.real_y = 0
        self.vx     = 0
        self.vy     = 0
        self.trail  = []  # liste de positions (x, y)

    def update(self):
        self.vy += GRAVITY

        # Limiter la vitesse verticale max (en descente comme en montée)
        if self.vy > MAX_VY:
            self.vy = MAX_VY
        elif self.vy < -MAX_VY:
            self.vy = -MAX_VY

        self.real_y += self.vy
        self.x      += self.vx

        if self.x < BALL_RADIUS:
            self.x   = BALL_RADIUS
            self.vx *= -0.7
        elif self.x > WIDTH - BALL_RADIUS:
            self.x   = WIDTH - BALL_RADIUS
            self.vx *= -0.7
            
        # Friction horizontale
        self.vx *= 0.98

        # Mettre à jour le trail
        self.trail.append((self.x, self.real_y))
        if len(self.trail) > TRAIL_LENGTH:
            self.trail.pop(0)

    def draw(self, offset_y):
        # Dessiner le trail avec transparence dégressive
        for i, (tx, ty) in enumerate(self.trail):
            screen_y = ty - offset_y
            if -50 < screen_y < HEIGHT + 50:
                alpha       = int(255 * (i / len(self.trail)))  # transparence du plus vieux au plus récent
                trail_color = (255, 100, 100, alpha)
                trail_surf  = pygame.Surface((BALL_RADIUS*2, BALL_RADIUS*2), pygame.SRCALPHA)
                pygame.draw.circle(trail_surf, trail_color, (BALL_RADIUS, BALL_RADIUS), BALL_RADIUS)
                screen.blit(trail_surf, (int(tx - BALL_RADIUS), int(screen_y - BALL_RADIUS)))

        # Dessiner la balle principale
        screen_y = self.real_y - offset_y
        if -50 < screen_y < HEIGHT + 50:
            pygame.draw.circle(screen, RED, (int(self.x), int(screen_y)), BALL_RADIUS)

class Booster:
    def __init__(self, x, y, side):
        self.x = x
        self.y = y
        self.side = side  # "left" ou "right"
        self.collected = False

    def draw(self, offset_y):
        if self.collected:
            return
        screen_y = self.y - offset_y
        if -50 < screen_y < HEIGHT + 50:
            color = BOOSTER_COULEUR_AJOUT_DROITE if self.side == "left" else BOOSTER_COULEUR_AJOUT_GAUCHE
            pygame.draw.circle(screen, color, (int(self.x), int(screen_y)), BOOSTER_RADIUS)

# Pegs dynamiques
pegs       = []
next_row_y = 0
bassine_y  = None

def generate_row(y):
    # Offset classique en quinconce
    offset = (int(y // PEG_SPACING_Y) % 2) * (PEG_SPACING_X // 2)
    
    # Décalage aléatoire entre PEGS_DECALAGE_X_GAUCHE et PEGS_DECALAGE_X_DROITE pixels sur toute la ligne
    random_shift = random.randint(PEGS_DECALAGE_X_GAUCHE, PEGS_DECALAGE_X_DROITE)

    row = []
    for i in range(PEGS_PER_ROW):
        x = i * PEG_SPACING_X + offset + random_shift
        if 0 < x < WIDTH:
            row.append((x, y))
    return row


def draw_pegs(offset_y):
    for x, y in pegs:
        screen_y = y - offset_y
        if -10 < screen_y < HEIGHT + 10:
            pygame.draw.circle(screen, BLUE, (int(x), int(screen_y)), PEG_RADIUS)

def draw_zones(offset_y, y):
    screen_y = y - offset_y
    for i in range(ZONES):
        x = i * zone_width
        pygame.draw.rect(screen, GREY, (x, screen_y, zone_width, ZONE_HEIGHT))
        pygame.draw.rect(screen, BLACK, (x, screen_y, zone_width, ZONE_HEIGHT), 2)
        font = pygame.font.SysFont(None, 28)
        text = font.render(str(scores[i]), True, BLACK)
        screen.blit(text, (x + zone_width // 2 - 15, screen_y + 10))

def check_collision(ball):
    global time_left, time_right # On doit les recuperer pour ajouter du temps

    for px, py in pegs:
        dx   = ball.x - px
        dy   = ball.real_y - py
        dist = math.hypot(dx, dy)
        min_dist = BALL_RADIUS + PEG_RADIUS

        if dist < min_dist and dist != 0:
            nx      = dx / dist
            ny      = dy / dist
            overlap = min_dist - dist
            ball.x += nx * overlap
            ball.real_y += ny * overlap

            v_dot_n = ball.vx * nx + ball.vy * ny
            ball.vx -= 2 * v_dot_n * nx
            ball.vy -= 2 * v_dot_n * ny

            # Amortissement plus différencié
            ball.vx *= AMORTISSEMENT_REBOND_X
            ball.vy *= AMORTISSEMENT_REBOND_Y

            # Ajouter un peu de bruit aléatoire sur les 2 axes
            ball.vx += random.uniform(-0.2, 0.2)
            ball.vy += random.uniform(-0.1, 0.1)
            
    for booster in boosters:
        if not booster.collected:
            dx = ball.x - booster.x
            dy = ball.real_y - booster.y
            dist = math.hypot(dx, dy)
            if dist < BALL_RADIUS + BOOSTER_RADIUS:
                booster.collected = True
                if booster.side == "left": # Punition pour permettre aux autres de remonter
                    time_right += BOOSTER_TIME_GAIN
                else:
                    time_left += BOOSTER_TIME_GAIN


#########
# DEBUT #
#########


time_left  = 0
time_right = 0

balls       = [Ball(WIDTH // 2)]
total_score = 0
finished    = False

start_time = time.time()
running    = True

boosters = []

while running:
    dt = clock.tick(60) / 1000
    elapsed = time.time() - start_time

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and finished:
                running = False

    # Génération dynamique continue
    GENERATE_AHEAD_Y = HEIGHT * NOMBRE_ECRAN_DEVANT_LA_BALLE

    while next_row_index * PEG_SPACING_Y < balls[0].real_y + GENERATE_AHEAD_Y and (next_row_index * PEG_SPACING_Y) < GENERATION_DURATION * MAX_VY * 60:
        # Pegs
        y     = next_row_index * PEG_SPACING_Y
        pegs += generate_row(y)
        
        # Booster
        if random.random() < BOOSTER_CHANCE:
            boosterX = random.randint(BOOSTER_RADIUS, WIDTH - BOOSTER_RADIUS)
            bside = "left" if boosterX < WIDTH // 2 else "right"
            boosters.append(Booster(boosterX, y, bside))

        next_row_index += 1

    # Une fois la génération "temps" dépassée, on fixe la bassine (zone finale) à la fin
    if bassine_y is None and next_row_index * PEG_SPACING_Y >= GENERATION_DURATION * MAX_VY * 60:
        bassine_y = next_row_index * PEG_SPACING_Y

    screen.fill(WHITE) # Background

    if balls:
        ball = balls[0]
        ball.update()
        check_collision(ball)
        offset_y = ball.real_y - Y_TARGET

        # Mise à jour des timers selon position x de la balle
        if ball.x < WIDTH / 2:
            time_left += dt
        else:
            time_right += dt
    else:
        offset_y = bassine_y - HEIGHT  # montrer le bas si la balle est terminée

    # Dessiner les backgrounds gauche et droit
    left_surf = pygame.Surface((WIDTH // 2, HEIGHT), pygame.SRCALPHA).convert_alpha()
    right_surf = pygame.Surface((WIDTH // 2, HEIGHT), pygame.SRCALPHA).convert_alpha()

    left_surf.fill(BACKGROUND_LAYER_GAUCHE)   # BG GAUCHE avec alpha
    right_surf.fill(BACKGROUND_LAYER_DROITE)  # BG DROIT avec alpha

    screen.blit(left_surf, (0, 0))
    screen.blit(right_surf, (WIDTH // 2, 0))

    draw_pegs(offset_y)

    if bassine_y:
        draw_zones(offset_y, bassine_y)

    for ball in balls[:]:
        ball.draw(offset_y)
        if bassine_y and ball.real_y > bassine_y:
            zone_index = int(ball.x // zone_width)
            # total_score += scores[zone_index]  # plus utilisé pour le moment
            balls.remove(ball)
            finished = True
            
    for booster in boosters:
        booster.draw(offset_y)

    # Affichage des temps
    font = pygame.font.SysFont(None, 32)
    time_left_text = font.render(f"{TEXTE_GAUCHE} : {time_left:.1f}s", True, BLACK)
    time_right_text = font.render(f"{TEXTE_DROITE} : {time_right:.1f}s", True, BLACK)
    screen.blit(time_left_text, (10, 10))
    screen.blit(time_right_text, (500, 10))

    if finished:
        text = font.render("Fin ! Appuie sur Échap pour quitter", True, BLACK)
        screen.blit(text, (WIDTH // 2 - 150, HEIGHT // 2))

    pygame.display.flip()

pygame.quit()