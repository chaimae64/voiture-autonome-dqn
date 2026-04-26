import pygame
import math
import numpy as np
import matplotlib.pyplot as plt
import os
from simulation import (Voiture, dessiner_route, dessiner_hud,
                        LARGEUR, HAUTEUR, LARGEUR_TOTALE,
                        BLANC, BORD_GAUCHE, NB_VOIES, LARGEUR_VOIE)
from dqn import AgentDQN
from visualisation import dessiner_panneau_reseau
from trafic import creer_trafic

VITESSE_AVANCE = 3

def get_centre_voie(voie):
    return BORD_GAUCHE + voie * LARGEUR_VOIE + LARGEUR_VOIE // 2

def calculer_recompense(voiture, voie_actuelle, dist_voie,
                        action, voie_precedente):
    if not voiture.vivante:
        return -500

    recompense = 3.0

    # Bonus centrage dans la voie
    if dist_voie < 3:
        recompense += 4.0
    elif dist_voie < 8:
        recompense += 1.0

    # Capteur avant — le plus important
    capteur_avant = voiture.distances[3]
    if capteur_avant > 0.85:
        recompense += 8.0
    elif capteur_avant > 0.65:
        recompense += 3.0
    elif capteur_avant < 0.35:
        recompense -= 20.0
    elif capteur_avant < 0.50:
        recompense -= 8.0

    # Pénalité obstacles latéraux
    min_dist = min(voiture.distances)
    if min_dist < 0.10:
        recompense -= 15.0
    elif min_dist < 0.20:
        recompense -= 5.0

    # Pénalité changement de voie inutile
    if action != voie_precedente and capteur_avant > 0.7:
        recompense -= 8.0

    # Bonus rester dans sa voie quand c'est libre
    if action == voie_precedente and capteur_avant > 0.7:
        recompense += 4.0

    # Bonus survie
    recompense += 1.0

    return recompense

def construire_etat(voiture, voie_actuelle, voie_cible):
    return voiture.distances[:] + [
        voie_actuelle / (NB_VOIES - 1),
        (voiture.x - get_centre_voie(voie_actuelle)) / (LARGEUR_VOIE / 2),
        voie_cible / (NB_VOIES - 1),
    ]

def main():
    pygame.init()
    ecran = pygame.display.set_mode((LARGEUR_TOTALE, HAUTEUR))
    pygame.display.set_caption("Entrainement DQN — Voiture Autonome")
    horloge = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 15)

    if os.path.exists("modele.pth"):
        os.remove("modele.pth")
        print("Ancien modele supprime - nouvel entrainement")

    agent = AgentDQN()
    nb_episodes    = 2000
    scores         = []
    meilleur_score = 0
    mise_a_jour_cible = 10
    offset = 0

    for episode in range(nb_episodes):
        voiture = Voiture()
        voiture.angle = 0
        trafic = creer_trafic(6)
        voie_actuelle  = 1
        voie_cible     = 1
        voie_precedente = 1
        voiture.x      = float(get_centre_voie(voie_actuelle))
        cooldown       = 0

        obstacles = [v.get_rect() for v in trafic]
        voiture.calculer_capteurs(obstacles)
        etat   = construire_etat(voiture, voie_actuelle, voie_cible)
        score  = 0
        etapes = 0
        action = 1  # action initiale = voie milieu
        en_cours = True

        while en_cours:
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

            # Décision de voie
            voie_precedente = voie_actuelle
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

            # Avancer
            voiture.y -= VITESSE_AVANCE
            if voiture.y < 50:
                voiture.y = float(HAUTEUR - 100)
                voiture.vivante = True

            voiture.calculer_capteurs(obstacles)
            voiture.verifier_collision(obstacles)

            dist_voie  = abs(voiture.x - get_centre_voie(voie_actuelle))
            recompense = calculer_recompense(voiture, voie_actuelle,
                                            dist_voie, action,
                                            voie_precedente)
            score  += recompense
            etapes += 1
            offset += VITESSE_AVANCE

            etat_suivant = construire_etat(voiture, voie_actuelle, voie_cible)
            termine      = not voiture.vivante or etapes > 8000

            agent.memoire.ajouter(etat, action, recompense,
                                  etat_suivant, float(termine))
            agent.apprendre()
            etat = etat_suivant

            if episode % 10 == 0:
                dessiner_route(ecran, offset)
                for v in trafic:
                    v.dessiner(ecran)
                voiture.dessiner(ecran)
                dessiner_hud(ecran, voiture)
                infos = [
                    f"Episode : {episode+1}/{nb_episodes}",
                    f"Score   : {score:.0f}",
                    f"Epsilon : {agent.epsilon:.3f}",
                    f"Memoire : {len(agent.memoire)}",
                    f"Meilleur: {meilleur_score:.0f}",
                    f"Voie    : {voie_actuelle+1}/{NB_VOIES}",
                ]
                for i, txt in enumerate(infos):
                    surf = font.render(txt, True, BLANC)
                    ecran.blit(surf, (LARGEUR - 210, 10 + i*22))
                dessiner_panneau_reseau(ecran, agent, LARGEUR)
                pygame.display.flip()
                horloge.tick(30)

            if termine:
                en_cours = False

        scores.append(score)
        if score > meilleur_score:
            meilleur_score = score
            agent.sauvegarder()

        if (episode + 1) % mise_a_jour_cible == 0:
            agent.mettre_a_jour_cible()
            print(f"Episode {episode+1} | Score: {score:.0f} | "
                  f"Epsilon: {agent.epsilon:.3f} | "
                  f"Meilleur: {meilleur_score:.0f}")

    plt.figure(figsize=(10, 5))
    plt.plot(scores, alpha=0.4, color="steelblue", label="Score brut")
    moyennes = [np.mean(scores[max(0,i-20):i+1]) for i in range(len(scores))]
    plt.plot(moyennes, color="red", linewidth=2, label="Moyenne 20 ep.")
    plt.xlabel("Episode")
    plt.ylabel("Score")
    plt.title("Courbe d'apprentissage DQN — Voiture Autonome")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.savefig("courbe_apprentissage.png")
    plt.show()
    print("Entrainement termine ! Courbe sauvegardee.")

if __name__ == "__main__":
    main()