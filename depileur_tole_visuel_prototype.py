# -*- coding: utf-8 -*-
# =============================================================================
# SAE 4.1 - Cartouches de gaz / Partie Informatique
# Depileur automatique de toles : SIMULATION VISUELLE (Tkinter)
#
# Cette version reprend exactement la logique de commande du programme
# "depileur_tole.py" (detection, prise par le vide, transfert, depose,
# comptage) mais l'affiche graphiquement : on voit le verin descendre,
# saisir une tole par les ventouses, remonter, la transferer puis la
# deposer sur la zone d'alimentation (998 mm). Un bandeau affiche l'etat,
# la pression de vide et le compteur de toles.
#
# Bibliotheque : Tkinter (incluse de base avec Python -> aucune installation).
# Lancement : python depileur_tole_visuel.py
# =============================================================================

import tkinter as tk   # interface graphique standard de Python
import random          # simulation du bruit de mesure et des defauts de prise

# -----------------------------------------------------------------------------
# 1) PARAMETRES DU SYSTEME
# -----------------------------------------------------------------------------

LOT_TOLES      = 250     # nombre total de toles a transferer (cahier des charges)
SEUIL_VIDE_KPA = 35      # vide correct si pression < 35 kPa (sinon prise ratee)
NB_ESSAIS      = 3       # nombre d'essais de prise avant alarme
VITESSE        = 6       # pixels par image : regle la vitesse de l'animation
PERIODE_MS     = 16      # periode de rafraichissement (~60 images/seconde)

# Couleurs (charte simple)
C_FOND     = "#1e2430"
C_TOLE     = "#9fb6c9"
C_TOLE_BRD = "#5d7488"
C_VERIN    = "#2E75B6"
C_VENTOUSE = "#E08A00"
C_DEPOSE   = "#3a4759"
C_OK       = "#4ec9b0"
C_ALARME   = "#e06c5a"
C_TEXTE    = "#e6eaf0"

# Geometrie de la scene (en pixels)
SOL_Y        = 540       # niveau du sol
PILE_X       = 230       # centre horizontal de la pile
PILE_LARG    = 230       # largeur d'une tole a l'ecran
PILE_TOP_MAX = 150       # hauteur (y) du sommet de la pile quand elle est pleine
DEPOSE_X     = 700       # centre horizontal de la zone de depose
DEPOSE_Y     = 360       # hauteur (y) de la surface de depose (= 998 mm reels)
Y_HAUT       = 110       # position haute du verin (apres remontee)


# -----------------------------------------------------------------------------
# 2) SIMULATION DES CAPTEURS (identique a la version non graphique)
# -----------------------------------------------------------------------------

def lire_capteur_inductif(toles_restantes):
    """Capteur inductif : True si une tole metallique reste au sommet."""
    return toles_restantes > 0

def lire_pression_vide(prise_reelle):
    """Capteur de pression : vide etabli (basse pression) si la prise est bonne,
    sinon pression proche de l'atmospherique. Un bruit aleatoire est ajoute."""
    if prise_reelle:
        return round(random.uniform(15, 30), 1)   # vide correct
    else:
        return round(random.uniform(80, 100), 1)  # fuite : pas de prise


# -----------------------------------------------------------------------------
# 3) CLASSE PRINCIPALE : fenetre, dessin et automate (machine a etats)
# -----------------------------------------------------------------------------

class Simulateur:
    def __init__(self, racine):
        self.racine = racine
        racine.title("SAE 4.1 - Depileur de toles (simulation visuelle)")

        # Zone de dessin
        self.cv = tk.Canvas(racine, width=920, height=580,
                            bg=C_FOND, highlightthickness=0)
        self.cv.pack()

        # Etat du systeme
        self.toles_deposees = 0          # compteur de toles correctement deposees
        self.essais_restants = NB_ESSAIS # essais de prise pour la tole en cours
        self.etat = "DETECTER"           # etat courant de l'automate
        self.message = "Demarrage..."    # texte d'etat affiche
        self.pression = 0.0              # derniere pression de vide lue
        self.tole_saisie = False         # une tole est-elle tenue par les ventouses ?
        self.couleur_msg = C_TEXTE

        # Position du verin/prehenseur (centre x, bas du prehenseur y)
        self.gx = PILE_X
        self.gy = Y_HAUT

        random.seed(1)                   # resultats reproductibles
        self.boucle()                    # lance l'animation

    # --- Outils geometriques --------------------------------------------------

    def sommet_pile(self):
        """Renvoie la hauteur (y) du sommet de la pile selon le nombre restant."""
        restantes = LOT_TOLES - self.toles_deposees
        # plus il reste de toles, plus la pile est haute (petit y)
        hauteur = (restantes / LOT_TOLES) * (SOL_Y - PILE_TOP_MAX)
        return SOL_Y - hauteur

    # --- Dessin de la scene ---------------------------------------------------

    def dessiner(self):
        self.cv.delete("all")

        # Sol
        self.cv.create_line(40, SOL_Y, 880, SOL_Y, fill="#3a4759", width=3)

        # Pile de toles restantes (rectangle hachure)
        y_top = self.sommet_pile()
        if self.toles_deposees < LOT_TOLES:
            self.cv.create_rectangle(PILE_X - PILE_LARG/2, y_top,
                                     PILE_X + PILE_LARG/2, SOL_Y,
                                     fill=C_TOLE, outline=C_TOLE_BRD)
            # quelques traits horizontaux pour figurer l'empilement
            y = y_top
            while y < SOL_Y - 4:
                self.cv.create_line(PILE_X - PILE_LARG/2, y,
                                    PILE_X + PILE_LARG/2, y, fill=C_TOLE_BRD)
                y += 7
        self.cv.create_text(PILE_X, SOL_Y + 18, fill=C_TEXTE,
                            text="Pile (capteur inductif)", font=("Arial", 10))

        # Zone de depose
        self.cv.create_rectangle(DEPOSE_X - PILE_LARG/2, DEPOSE_Y,
                                 DEPOSE_X + PILE_LARG/2, DEPOSE_Y + 14,
                                 fill=C_DEPOSE, outline="#566375")
        # toles deja deposees (petite pile qui grandit)
        for i in range(min(self.toles_deposees, 18)):
            yy = DEPOSE_Y - 3 - i * 3
            self.cv.create_rectangle(DEPOSE_X - PILE_LARG/2 + 6, yy,
                                     DEPOSE_X + PILE_LARG/2 - 6, yy + 3,
                                     fill=C_TOLE, outline=C_TOLE_BRD)
        self.cv.create_text(DEPOSE_X, DEPOSE_Y + 34, fill=C_TEXTE,
                            text="Zone de depose (998 mm)", font=("Arial", 10))
        self.cv.create_line(DEPOSE_X - PILE_LARG/2, DEPOSE_Y,
                            DEPOSE_X + PILE_LARG/2, DEPOSE_Y, fill="#566375", dash=(3, 3))

        # Prehenseur : traverse + verin + 4 ventouses
        bras_haut = 70
        self.cv.create_line(self.gx, bras_haut, self.gx, self.gy - 18,
                            fill=C_VERIN, width=8)                       # verin
        self.cv.create_rectangle(self.gx - PILE_LARG/2, self.gy - 18,
                                 self.gx + PILE_LARG/2, self.gy - 6,
                                 fill=C_VERIN, outline="#1f5285")        # traverse
        for dx in (-0.36, -0.12, 0.12, 0.36):                           # 4 ventouses
            vx = self.gx + dx * PILE_LARG
            self.cv.create_oval(vx - 7, self.gy - 6, vx + 7, self.gy + 6,
                                fill=C_VENTOUSE, outline="#8a5400")

        # Tole en cours de manipulation (suspendue sous les ventouses)
        if self.tole_saisie:
            self.cv.create_rectangle(self.gx - PILE_LARG/2, self.gy + 6,
                                     self.gx + PILE_LARG/2, self.gy + 12,
                                     fill=C_TOLE, outline=C_TOLE_BRD)

        # Bandeau d'information (HUD)
        self.cv.create_rectangle(0, 0, 920, 52, fill="#161b24", outline="")
        self.cv.create_text(16, 16, anchor="w", fill=self.couleur_msg,
                            text="Etat : " + self.message, font=("Arial", 12, "bold"))
        self.cv.create_text(16, 38, anchor="w", fill=C_TEXTE,
                            text="Vide mesure : {:.1f} kPa  (seuil {} kPa)".format(
                                self.pression, SEUIL_VIDE_KPA), font=("Arial", 11))
        self.cv.create_text(904, 16, anchor="e", fill=C_OK,
                            text="Toles deposees : {} / {}".format(
                                self.toles_deposees, LOT_TOLES), font=("Arial", 12, "bold"))
        self.cv.create_text(904, 38, anchor="e", fill=C_TEXTE,
                            text="Restantes : {}".format(LOT_TOLES - self.toles_deposees),
                            font=("Arial", 11))

    # --- Automate : une etape par image ---------------------------------------

    def etape_automate(self):
        """Fait avancer la machine a etats. Chaque etat deplace le verin ou
        declenche une action, puis passe a l'etat suivant."""

        # Fin de production
        if self.toles_deposees >= LOT_TOLES:
            self.etat = "FINI"
            self.message = "Production terminee : {} toles deposees.".format(LOT_TOLES)
            self.couleur_msg = C_OK
            return

        if self.etat == "DETECTER":
            restantes = LOT_TOLES - self.toles_deposees
            if lire_capteur_inductif(restantes):
                self.message = "Tole detectee : descente du verin"
                self.couleur_msg = C_TEXTE
                self.etat = "DESCENDRE"
            else:
                self.etat = "FINI"

        elif self.etat == "DESCENDRE":
            # descendre jusqu'au sommet de la pile (fin de course bas)
            cible = self.sommet_pile() - 12
            if self.gy < cible:
                self.gy = min(self.gy + VITESSE, cible)
            else:
                self.message = "Activation du vide (ventouses)"
                self.essais_restants = NB_ESSAIS
                self.etat = "SAISIR"

        elif self.etat == "SAISIR":
            # un essai de prise par image
            prise_reelle = random.random() > 0.10      # 9 chances sur 10
            self.pression = lire_pression_vide(prise_reelle)
            if self.pression < SEUIL_VIDE_KPA:
                self.tole_saisie = True
                self.message = "Prise confirmee : remontee"
                self.couleur_msg = C_OK
                self.etat = "REMONTER"
            else:
                self.essais_restants -= 1
                self.message = "Vide insuffisant, nouvel essai ({} restants)".format(
                    self.essais_restants)
                self.couleur_msg = C_ALARME
                if self.essais_restants <= 0:
                    self.message = "ALARME : prise impossible -> reprise"
                    self.etat = "DESCENDRE"      # on retente le cycle

        elif self.etat == "REMONTER":
            if self.gy > Y_HAUT:
                self.gy = max(self.gy - VITESSE, Y_HAUT)
            else:
                self.message = "Transfert vers la zone de depose"
                self.couleur_msg = C_TEXTE
                self.etat = "TRANSFERER"

        elif self.etat == "TRANSFERER":
            if self.gx < DEPOSE_X:
                self.gx = min(self.gx + VITESSE, DEPOSE_X)
            else:
                self.etat = "DEPOSER"

        elif self.etat == "DEPOSER":
            # descendre jusqu'a la surface de depose
            cible = DEPOSE_Y - 18
            if self.gy < cible:
                self.gy = min(self.gy + VITESSE, cible)
            else:
                self.tole_saisie = False           # coupure du vide -> relachement
                self.toles_deposees += 1
                self.message = "Tole n{} deposee".format(self.toles_deposees)
                self.couleur_msg = C_OK
                self.etat = "RETOUR"

        elif self.etat == "RETOUR":
            # remonter puis revenir au-dessus de la pile
            if self.gy > Y_HAUT:
                self.gy = max(self.gy - VITESSE, Y_HAUT)
            elif self.gx > PILE_X:
                self.gx = max(self.gx - VITESSE, PILE_X)
            else:
                self.etat = "DETECTER"             # nouveau cycle

    # --- Boucle d'animation ---------------------------------------------------

    def boucle(self):
        self.etape_automate()
        self.dessiner()
        if self.etat != "FINI":
            self.racine.after(PERIODE_MS, self.boucle)   # rappel periodique
        else:
            self.dessiner()


# -----------------------------------------------------------------------------
# 4) POINT D'ENTREE
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    racine = tk.Tk()
    app = Simulateur(racine)
    racine.mainloop()
