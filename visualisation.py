import pygame
import math
import numpy as np

def dessiner_reseau(ecran, agent, x, y, largeur, hauteur):
    reseau = agent.modele.reseau
    couches_tailles = []
    poids_list = []

    for module in reseau:
        if hasattr(module, 'weight'):
            if not couches_tailles:
                couches_tailles.append(module.weight.shape[1])
            couches_tailles.append(module.weight.shape[0])
            poids_list.append(module.weight.detach().numpy())

    if not couches_tailles:
        return

    # Limiter l'affichage à max 8 neurones par couche cachée
    MAX_AFFICHAGE = 8
    couches_affichage = []
    for i, nb in enumerate(couches_tailles):
        if i == 0 or i == len(couches_tailles) - 1:
            couches_affichage.append(nb)
        else:
            couches_affichage.append(min(nb, MAX_AFFICHAGE))

    nb_couches = len(couches_affichage)
    positions = []

    for i, nb in enumerate(couches_affichage):
        col_x = x + int((i / (nb_couches - 1)) * largeur)
        col_pos = []
        for j in range(nb):
            neurone_y = y + int((j + 0.5) / nb * hauteur)
            col_pos.append((col_x, neurone_y))
        positions.append(col_pos)

    # Connexions entre couches
    for i in range(len(positions) - 1):
        w = poids_list[i]
        nb_src = len(positions[i])
        nb_dst = len(positions[i+1])
        for j, pos_src in enumerate(positions[i]):
            for k, pos_dst in enumerate(positions[i+1]):
                idx_src = int(j * couches_tailles[i] / nb_src)
                idx_dst = int(k * couches_tailles[i+1] / nb_dst)
                if idx_dst < w.shape[0] and idx_src < w.shape[1]:
                    valeur = float(w[idx_dst][idx_src])
                    valeur_norme = max(-1, min(1, valeur / 2))
                    alpha = int(abs(valeur_norme) * 200 + 30)
                    if valeur_norme > 0:
                        couleur = (0, min(255, alpha + 80), 0)
                    else:
                        couleur = (min(255, alpha + 80), 0, 0)
                    pygame.draw.line(ecran, couleur, pos_src, pos_dst, 1)

    # Neurones
    for i, col_pos in enumerate(positions):
        for j, (nx, ny) in enumerate(col_pos):
            if i == 0:
                couleur_fond = (255, 200, 0)
                rayon = 9
            elif i == len(positions) - 1:
                couleur_fond = (0, 180, 255)
                rayon = 10
            else:
                couleur_fond = (100, 100, 120)
                rayon = 6
            pygame.draw.circle(ecran, couleur_fond, (nx, ny), rayon)
            pygame.draw.circle(ecran, (220, 220, 220), (nx, ny), rayon, 1)

    # Labels couches
    font_small = pygame.font.SysFont("consolas", 11)
    labels_couches = ["Capteurs", "Couche 1", "Couche 2", "Actions"]
    for i, label in enumerate(labels_couches):
        col_x = x + int((i / (nb_couches - 1)) * largeur)
        surf = font_small.render(label, True, (140, 140, 160))
        ecran.blit(surf, (col_x - surf.get_width()//2, y + hauteur + 10))

    # Labels actions
    actions_labels = ["Gauche", "Droite", "Avant", "Arriere"]
    for k, (nx, ny) in enumerate(positions[-1]):
        surf = font_small.render(actions_labels[k], True, (0, 200, 255))
        ecran.blit(surf, (nx + 14, ny - 6))

    # Indicateur neurones cachés
    font_info = pygame.font.SysFont("consolas", 10)
    for i in range(1, len(couches_tailles) - 1):
        col_x = x + int((i / (nb_couches - 1)) * largeur)
        info = font_info.render(f"({couches_tailles[i]})", True, (100, 100, 120))
        ecran.blit(info, (col_x - info.get_width()//2, y - 18))


def dessiner_panneau_reseau(ecran, agent, largeur_sim):
    largeur_panneau = 320
    hauteur = ecran.get_height()

    pygame.draw.rect(ecran, (8, 8, 18),
                     (largeur_sim, 0, largeur_panneau, hauteur))
    pygame.draw.line(ecran, (50, 50, 70),
                     (largeur_sim, 0), (largeur_sim, hauteur), 2)

    font = pygame.font.SysFont("consolas", 13)
    titre = font.render("Reseau de neurones", True, (180, 180, 255))
    ecran.blit(titre, (largeur_sim + largeur_panneau//2 - titre.get_width()//2, 12))

    dessiner_reseau(ecran, agent,
                    largeur_sim + 20, 45,
                    largeur_panneau - 80, hauteur - 90)