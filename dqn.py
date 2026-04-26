import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import deque

class ReseauDQN(nn.Module):
    def __init__(self, nb_entrees, nb_actions):
        super(ReseauDQN, self).__init__()
        self.reseau = nn.Sequential(
            nn.Linear(nb_entrees, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, nb_actions)
        )

    def forward(self, x):
        return self.reseau(x)

class Memoire:
    def __init__(self, capacite=100000):
        self.memoire = deque(maxlen=capacite)

    def ajouter(self, etat, action, recompense, etat_suivant, termine):
        self.memoire.append((etat, action, recompense, etat_suivant, termine))

    def echantillon(self, taille):
        return random.sample(self.memoire, taille)

    def __len__(self):
        return len(self.memoire)

class AgentDQN:
    def __init__(self):
        self.nb_actions = 3        # gauche, milieu, droite
        self.nb_entrees = 10       # 7 capteurs + voie + position + cible
        self.gamma = 0.99
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.99995
        self.lr = 0.0005
        self.batch_size = 128
        self.pas_total = 0

        self.modele = ReseauDQN(self.nb_entrees, self.nb_actions)
        self.modele_cible = ReseauDQN(self.nb_entrees, self.nb_actions)
        self.modele_cible.load_state_dict(self.modele.state_dict())

        self.optimiseur = optim.Adam(self.modele.parameters(), lr=self.lr)
        self.memoire = Memoire()
        self.pertes = []

    def choisir_action(self, etat):
        if random.random() < self.epsilon:
            return random.randint(0, self.nb_actions - 1)
        etat_tensor = torch.FloatTensor(etat).unsqueeze(0)
        with torch.no_grad():
            valeurs = self.modele(etat_tensor)
        return valeurs.argmax().item()

    def apprendre(self):
        if len(self.memoire) < self.batch_size:
            return

        batch = self.memoire.echantillon(self.batch_size)
        etats, actions, recompenses, etats_suivants, termines = zip(*batch)

        etats          = torch.FloatTensor(np.array(etats))
        actions        = torch.LongTensor(actions)
        recompenses    = torch.FloatTensor(recompenses)
        etats_suivants = torch.FloatTensor(np.array(etats_suivants))
        termines       = torch.FloatTensor(termines)

        q_actuels = self.modele(etats).gather(1, actions.unsqueeze(1))

        with torch.no_grad():
            q_suivants = self.modele_cible(etats_suivants).max(1)[0]
        q_cibles = recompenses + self.gamma * q_suivants * (1 - termines)

        perte = nn.SmoothL1Loss()(q_actuels.squeeze(), q_cibles)
        self.pertes.append(perte.item())

        self.optimiseur.zero_grad()
        perte.backward()
        torch.nn.utils.clip_grad_norm_(self.modele.parameters(), 1.0)
        self.optimiseur.step()

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        self.pas_total += 1

    def mettre_a_jour_cible(self):
        self.modele_cible.load_state_dict(self.modele.state_dict())

    def sauvegarder(self, chemin="modele.pth"):
        torch.save(self.modele.state_dict(), chemin)
        print(f"Modele sauvegarde : {chemin}")

    def charger(self, chemin="modele.pth"):
        self.modele.load_state_dict(torch.load(chemin))
        print(f"Modele charge : {chemin}")