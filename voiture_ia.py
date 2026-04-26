import pygame
import math
from simulation import (Voiture, dessiner_route, dessiner_hud,
                        LARGEUR, HAUTEUR, LARGEUR_TOTALE,
                        BLANC, BORD_GAUCHE, NB_VOIES, LARGEUR_VOIE)
from dqn import AgentDQN
from visualisation import dessiner_panneau_reseau
from trafic import creer_trafic

VITESSE_AVANCE = 3

def get_centre_voie(voie):
    return BORD_GAUCHE + voie * LARGEUR_VOIE + LARGEUR_VOIE // 2

def construire_etat(voiture, voie_actuelle, voie_cible):
    return voiture.distances[:] + [
        voie_actuelle / (NB_VOIES - 1),
        (voiture.x - get_centre_voie(voie_actuelle)) / (LARGEUR_VOIE / 2),
        voie_cible / (NB_VOIES - 1),
    ]

def main():
    pygame.init()
    ecran = pygame.display.set_mode((LARGEUR_TOTALE, HAUTEUR))
    pygame.display.set_caption("Voiture Autonome — Demo IA")
    horloge = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 16)

    agent = AgentDQN()
    agent.charger("modele.pth")
    agent.epsilon = 0.0

    trafic = creer_trafic(6)
    voiture = Voiture()
    voiture.angle = 0
    voie_actuelle = 1
    voie_cible    = 1
    voiture.x     = float(get_centre_voie(voie_actuelle))
    cooldown      = 0
    offset        = 0
    distance_totale = 0
    crashes       = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return

        for v in trafic:
            v.update(trafic, voiture.y)
        obstacles = [v.get_rect() for v in trafic]

        voiture.calculer_capteurs(obstacles)
        etat = construire_etat(voiture, voie_actuelle, voie_cible)

        if cooldown <= 0:
            action = agent.choisir_action(etat)
            nouvelle_voie = action  # 0=gauche 1=milieu 2=droite
            if nouvelle_voie != voie_cible:
                voie_cible = nouvelle_voie
                cooldown = 45
        else:
            cooldown -= 1

        # Mouvement fluide
        x_cible = float(get_centre_voie(voie_cible))
        dx = x_cible - voiture.x
        if abs(dx) > 0.5:
            voiture.x += dx * 0.08
        else:
            voiture.x = x_cible
            voie_actuelle = voie_cible

        voiture.y -= VITESSE_AVANCE
        if voiture.y < 50:
            voiture.y = float(HAUTEUR - 100)
            voiture.vivante = True

        voiture.calculer_capteurs(obstacles)
        voiture.verifier_collision(obstacles)

        if not voiture.vivante:
            crashes += 1
            voiture = Voiture()
            voiture.angle = 0
            voie_actuelle = 1
            voie_cible    = 1
            voiture.x     = float(get_centre_voie(voie_actuelle))
            cooldown      = 0
            voiture.calculer_capteurs(obstacles)

        distance_totale += VITESSE_AVANCE
        offset += VITESSE_AVANCE

        dessiner_route(ecran, offset)
        for v in trafic:
            v.dessiner(ecran)
        voiture.dessiner(ecran)
        dessiner_hud(ecran, voiture)

        stats = [
            f"MODE    : IA autonome",
            f"Distance: {int(distance_totale)}",
            f"Crashes : {crashes}",
            f"Voie    : {voie_actuelle+1}/{NB_VOIES}",
        ]
        for i, txt in enumerate(stats):
            surf = font.render(txt, True, BLANC)
            ecran.blit(surf, (LARGEUR - 210, 10 + i*22))

        dessiner_panneau_reseau(ecran, agent, LARGEUR)
        pygame.display.flip()
        horloge.tick(60)

if __name__ == "__main__":
    main()