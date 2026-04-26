import pygame
import math

LARGEUR, HAUTEUR = 600, 700
LARGEUR_TOTALE = LARGEUR + 350
FPS = 60

NOIR       = (0, 0, 0)
BLANC      = (255, 255, 255)
ROUGE      = (220, 50, 50)
JAUNE      = (255, 200, 0)
GRIS_ROUTE = (50, 50, 50)

LARGEUR_ROUTE = 200
CENTRE_ROUTE  = LARGEUR // 2
BORD_GAUCHE   = CENTRE_ROUTE - LARGEUR_ROUTE // 2
BORD_DROIT    = CENTRE_ROUTE + LARGEUR_ROUTE // 2
NB_VOIES      = 3
LARGEUR_VOIE  = LARGEUR_ROUTE // NB_VOIES

MURS = [
    pygame.Rect(BORD_GAUCHE - 8, 0, 8, HAUTEUR),
    pygame.Rect(BORD_DROIT,      0, 8, HAUTEUR),
]

def rot(px, py, cx, cy, angle):
    rx = px*math.cos(math.radians(angle)) - py*math.sin(math.radians(angle))
    ry = px*math.sin(math.radians(angle)) + py*math.cos(math.radians(angle))
    return (int(cx+rx), int(cy+ry))

def creer_surface_voiture(w, h, c_corps, c_bord, c_vitre, c_roue):
    surf = pygame.Surface((w+12, h+12), pygame.SRCALPHA)
    cx, cy = (w+12)//2, (h+12)//2

    # Carrosserie
    carrosserie = [
        (cx-w//2+3, cy+h//2),
        (cx+w//2-3, cy+h//2),
        (cx+w//2,   cy+h//2-5),
        (cx+w//2,   cy-h//2+8),
        (cx+w//2-3, cy-h//2),
        (cx-w//2+3, cy-h//2),
        (cx-w//2,   cy-h//2+8),
        (cx-w//2,   cy+h//2-5),
    ]
    pygame.draw.polygon(surf, c_corps, carrosserie)
    pygame.draw.polygon(surf, c_bord,  carrosserie, 2)

    # Toit
    toit = [
        (cx-w//2+5, cy+h//2-12),
        (cx+w//2-5, cy+h//2-12),
        (cx+w//2-4, cy-h//2+12),
        (cx-w//2+4, cy-h//2+12),
    ]
    pygame.draw.polygon(surf, c_corps, toit)

    # Pare-brise avant (haut = devant)
    pba = [
        (cx-w//2+5, cy-h//2+4),
        (cx+w//2-5, cy-h//2+4),
        (cx+w//2-5, cy-h//2+13),
        (cx-w//2+5, cy-h//2+13),
    ]
    pygame.draw.polygon(surf, c_vitre, pba)

    # Lunette arrière (bas = arrière)
    pba2 = [
        (cx-w//2+7, cy+h//2-4),
        (cx+w//2-7, cy+h//2-4),
        (cx+w//2-7, cy+h//2-11),
        (cx-w//2+7, cy+h//2-11),
    ]
    pygame.draw.polygon(surf, c_vitre, pba2)

    # Roues
    for rpx, rpy in [
        (cx-w//2-1, cy-h//2+9),
        (cx+w//2+1, cy-h//2+9),
        (cx-w//2-1, cy+h//2-9),
        (cx+w//2+1, cy+h//2-9),
    ]:
        pygame.draw.circle(surf, c_roue,       (rpx, rpy), 5)
        pygame.draw.circle(surf, (70,70,70),   (rpx, rpy), 5, 1)
        pygame.draw.circle(surf, (130,130,130),(rpx, rpy), 2)

    # Phares avant (haut)
    for px in [cx-w//2+6, cx+w//2-6]:
        pygame.draw.circle(surf, (255,255,180), (px, cy-h//2+2), 3)

    # Feux arrière (bas)
    for px in [cx-w//2+6, cx+w//2-6]:
        pygame.draw.circle(surf, (255,50,50), (px, cy+h//2-2), 3)

    return surf


class Voiture:
    def __init__(self, x=None, y=None):
        self.x = float(x if x else CENTRE_ROUTE)
        self.y = float(y if y else HAUTEUR - 100)
        self.angle = 0
        self.vitesse = 4
        self.largeur = 24
        self.hauteur = 40
        self.longueur_capteur = 180
        self.distances = [1.0] * 7
        self.points_capteurs = []
        self.vivante = True
        self._surf_cache = {}

    def _get_surf(self, c_corps, c_bord, c_vitre, c_roue):
        key = (c_corps, c_bord)
        if key not in self._surf_cache:
            self._surf_cache[key] = creer_surface_voiture(
                self.largeur, self.hauteur,
                c_corps, c_bord, c_vitre, c_roue)
        return self._surf_cache[key]

    def get_coins(self):
        pts = [
            (-self.largeur//2, -self.hauteur//2),
            ( self.largeur//2, -self.hauteur//2),
            ( self.largeur//2,  self.hauteur//2),
            (-self.largeur//2,  self.hauteur//2),
        ]
        coins = []
        for px, py in pts:
            rx = px*math.cos(math.radians(self.angle)) - py*math.sin(math.radians(self.angle))
            ry = px*math.sin(math.radians(self.angle)) + py*math.cos(math.radians(self.angle))
            coins.append((self.x+rx, self.y+ry))
        return coins

    def verifier_collision(self, obstacles=[]):
        coins = self.get_coins()
        for i in range(len(coins)):
            x1, y1 = coins[i]
            x2, y2 = coins[(i+1) % len(coins)]
            for mur in MURS:
                if mur.clipline(x1, y1, x2, y2):
                    self.vivante = False
                    return
            for obs in obstacles:
                if obs.clipline(x1, y1, x2, y2):
                    self.vivante = False
                    return
        if self.x < BORD_GAUCHE or self.x > BORD_DROIT:
            self.vivante = False

    def calculer_capteurs(self, obstacles=[]):
        angles_capteurs = [-90, -60, -30, 0, 30, 60, 90]
        self.distances = []
        self.points_capteurs = []
        for a in angles_capteurs:
            angle_rad = math.radians(self.angle + a + 90)
            dist = self.longueur_capteur
            px = self.x + math.cos(angle_rad) * dist
            py = self.y - math.sin(angle_rad) * dist
            for mur in MURS:
                result = mur.clipline(self.x, self.y, px, py)
                if result:
                    x1, y1 = result[0]
                    d = math.hypot(x1-self.x, y1-self.y)
                    if d < dist:
                        dist = d
                        px, py = x1, y1
            for obs in obstacles:
                result = obs.clipline(self.x, self.y, px, py)
                if result:
                    x1, y1 = result[0]
                    d = math.hypot(x1-self.x, y1-self.y)
                    if d < dist:
                        dist = d
                        px, py = x1, y1
            self.distances.append(round(dist / self.longueur_capteur, 3))
            self.points_capteurs.append((px, py))

    def update(self, touches):
        if not self.vivante:
            return
        if touches[pygame.K_LEFT]:
            self.angle -= 2
        if touches[pygame.K_RIGHT]:
            self.angle += 2
        if touches[pygame.K_UP]:
            self.x += math.cos(math.radians(self.angle)) * self.vitesse
            self.y += math.sin(math.radians(self.angle)) * self.vitesse
        if touches[pygame.K_DOWN]:
            self.x -= math.cos(math.radians(self.angle)) * self.vitesse
            self.y -= math.sin(math.radians(self.angle)) * self.vitesse
        self.calculer_capteurs()
        self.verifier_collision()

    def dessiner(self, ecran, meilleure=True):
        if not self.vivante:
            c_corps = (70,70,70)
            c_bord  = (110,110,110)
            c_vitre = (90,90,90)
            c_roue  = (50,50,50)
        elif meilleure:
            c_corps = (30,120,255)
            c_bord  = (255,255,255)
            c_vitre = (150,210,255)
            c_roue  = (20,20,20)
        else:
            c_corps = (220,50,50)
            c_bord  = (255,200,0)
            c_vitre = (255,220,150)
            c_roue  = (20,20,20)

        # Capteurs
        for i, pt in enumerate(self.points_capteurs):
            d = self.distances[i]
            couleur = (int(255*(1-d)), int(255*d), 50)
            pygame.draw.line(ecran, couleur,
                             (int(self.x), int(self.y)),
                             (int(pt[0]), int(pt[1])), 1)
            pygame.draw.circle(ecran, couleur,
                               (int(pt[0]), int(pt[1])), 3)

        # Voiture avec rotation correcte
        surf = self._get_surf(c_corps, c_bord, c_vitre, c_roue)
        surf_rot = pygame.transform.rotate(surf, -self.angle)
        rect = surf_rot.get_rect(center=(int(self.x), int(self.y)))
        ecran.blit(surf_rot, rect)


def dessiner_route(ecran, offset=0):
    ecran.fill((18, 18, 18))
    pygame.draw.rect(ecran, GRIS_ROUTE,
                     (BORD_GAUCHE, 0, LARGEUR_ROUTE, HAUTEUR))
    pygame.draw.rect(ecran, (220,180,0),
                     (BORD_GAUCHE-5, 0, 5, HAUTEUR))
    pygame.draw.rect(ecran, (220,180,0),
                     (BORD_DROIT, 0, 5, HAUTEUR))
    for voie in range(1, NB_VOIES):
        x_ligne = BORD_GAUCHE + voie * LARGEUR_VOIE
        y = (-offset % 40)
        while y < HAUTEUR:
            pygame.draw.rect(ecran, (75,75,75),
                             (x_ligne-1, y, 2, 22))
            y += 40


def dessiner_hud(ecran, voiture):
    font = pygame.font.SysFont("consolas", 13)
    for i, d in enumerate(voiture.distances):
        couleur = (int(255*(1-d)), int(255*d), 50)
        txt = font.render(f"C{i+1}: {d:.2f}", True, couleur)
        ecran.blit(txt, (8, 8 + i*18))


def main():
    pygame.init()
    ecran = pygame.display.set_mode((LARGEUR, HAUTEUR))
    pygame.display.set_caption("Voiture Autonome")
    horloge = pygame.time.Clock()
    voiture = Voiture()
    offset = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return
                if event.key == pygame.K_r:
                    voiture = Voiture()
                    offset = 0

        touches = pygame.key.get_pressed()
        voiture.update(touches)
        offset += voiture.vitesse

        dessiner_route(ecran, offset)
        voiture.dessiner(ecran)
        dessiner_hud(ecran, voiture)
        pygame.display.flip()
        horloge.tick(FPS)


if __name__ == "__main__":
    main()