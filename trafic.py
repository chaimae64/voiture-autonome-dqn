import pygame
import random
from simulation import (BORD_GAUCHE, LARGEUR_VOIE, HAUTEUR,
                        NB_VOIES, creer_surface_voiture)

COULEURS_TRAFIC = [
    ((200,60,60),  (255,255,255), (150,210,255), (20,20,20)),
    ((60,180,60),  (255,255,255), (150,210,255), (20,20,20)),
    ((60,100,220), (255,255,255), (150,210,255), (20,20,20)),
    ((200,160,40), (255,255,255), (150,210,255), (20,20,20)),
    ((160,60,200), (255,255,255), (150,210,255), (20,20,20)),
]

ESPACEMENT_MIN = 160

class VoitureTrafic:
    def __init__(self, voie, y):
        self.largeur = 24
        self.hauteur = 40
        self.voie    = voie
        self.x       = float(BORD_GAUCHE + voie*LARGEUR_VOIE + LARGEUR_VOIE//2)
        self.y       = float(y)
        self.vitesse = random.uniform(1.5, 2.5)
        self.couleurs = random.choice(COULEURS_TRAFIC)
        self.angle   = 180
        self._surf   = creer_surface_voiture(
            self.largeur, self.hauteur, *self.couleurs)

    def update(self, toutes_voitures, y_ia):
        self.y += self.vitesse

        # Ralentir si trop proche de la voiture devant
        for v in toutes_voitures:
            if v is not self and v.voie == self.voie:
                dist = v.y - self.y
                if 0 < dist < ESPACEMENT_MIN:
                    self.vitesse = max(0.5, v.vitesse - 0.2)
                    return
        if self.vitesse < 1.5:
            self.vitesse = random.uniform(1.5, 2.5)

        if self.y > HAUTEUR + 80:
            self._repositionner(toutes_voitures, y_ia)

    def _repositionner(self, toutes_voitures, y_ia):
        # Compter voitures devant la voiture IA par voie
        voies_bloquees = set()
        for v in toutes_voitures:
            if v is not self and v.y < y_ia - 20:
                voies_bloquees.add(v.voie)

        # Toujours garder au moins une voie libre
        voies_libres = [i for i in range(NB_VOIES)
                        if i not in voies_bloquees]

        if not voies_libres:
            voies_libres = list(range(NB_VOIES))

        # 60% du temps bloquer la voie milieu pour forcer l'apprentissage
        voies_bloquables = [v for v in range(NB_VOIES)
                           if v not in voies_libres or len(voies_libres) > 1]
        if 1 in voies_bloquables and random.random() < 0.6:
            self.voie = 1
        else:
            self.voie = random.choice(voies_bloquables
                                      if voies_bloquables else voies_libres)

        self.x = float(BORD_GAUCHE + self.voie*LARGEUR_VOIE + LARGEUR_VOIE//2)

        # Position y bien espacée
        min_y = -80
        for v in toutes_voitures:
            if v is not self and v.voie == self.voie and v.y < 0:
                min_y = min(min_y, v.y - ESPACEMENT_MIN)

        self.y        = float(min_y - random.randint(20, 60))
        self.vitesse  = random.uniform(1.5, 2.5)
        self.couleurs = random.choice(COULEURS_TRAFIC)
        self._surf    = creer_surface_voiture(
            self.largeur, self.hauteur, *self.couleurs)

    def dessiner(self, ecran):
        surf_rot = pygame.transform.rotate(self._surf, -self.angle)
        rect = surf_rot.get_rect(center=(int(self.x), int(self.y)))
        ecran.blit(surf_rot, rect)

    def get_rect(self):
        return pygame.Rect(
            int(self.x - self.largeur//2),
            int(self.y - self.hauteur//2),
            self.largeur, self.hauteur
        )


def creer_trafic(nb=6):
    voitures = []
    voies_utilisees = []
    
    for i in range(nb):
        # Choisir une voie aléatoire
        voie = random.randint(0, NB_VOIES - 1)
        
        # Y aléatoire bien espacé
        y_min = -100 - i * 120
        y_max = y_min - 80
        y = random.randint(y_max, y_min)
        
        voitures.append(VoitureTrafic(voie, y))
    
    # Garantir qu'au moins une voie est libre au départ
    voies_presentes = set(v.voie for v in voitures[:3])
    if len(voies_presentes) == NB_VOIES:
        # Toutes les voies bloquées — libérer une au hasard
        voiture_a_changer = random.choice(voitures[:3])
        voies_libres = [i for i in range(NB_VOIES) 
                       if i not in voies_presentes - {voiture_a_changer.voie}]
        voiture_a_changer.voie = random.choice(voies_libres)
        voiture_a_changer.x = float(BORD_GAUCHE + voiture_a_changer.voie 
                                    * LARGEUR_VOIE + LARGEUR_VOIE // 2)
    
    return voitures