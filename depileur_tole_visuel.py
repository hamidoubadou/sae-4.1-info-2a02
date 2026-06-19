# -*- coding: utf-8 -*-
# =============================================================================
# SAE 4.1 - Cartouches de gaz / Partie Informatique
# Depileur automatique de toles : SIMULATION VISUELLE (Tkinter)
#
# Cycle reel (concept GSAG) reproduit a l'ecran :
#   1) un chariot elevateur electrique maintient la pile a hauteur constante
#   2) le verin pneumatique descend l'ensemble de prehension
#   3) les ventouses saisissent la tole (controle du vide)
#   4) le verin remonte
#   5) le verin ROTATIF tourne le systeme de 180 degres (transfert)
#   6) le verin descend et les ventouses lachent la tole (depose a 998 mm)
#   7) le verin remonte
#   8) le verin rotatif tourne de 180 degres en sens inverse (retour)
#
# Bibliotheque : Tkinter (incluse de base avec Python -> aucune installation).
# Lancement : python depileur_tole_visuel.py
# =============================================================================

import tkinter as tk   # interface graphique standard de Python
import random          # simulation du bruit de mesure et des defauts de prise
import math            # pour calculer la position lors de la rotation

# -----------------------------------------------------------------------------
# 1) PARAMETRES DU SYSTEME
# -----------------------------------------------------------------------------

LOT_TOLES      = 250     # nombre total de toles a transferer (cahier des charges)
SEUIL_VIDE_KPA = 35      # vide correct si pression < 35 kPa (sinon prise ratee)
NB_ESSAIS      = 3       # nombre d'essais de prise avant alarme
V_VERT         = 6       # vitesse de descente/montee (pixels/image)
V_ROT          = 4       # vitesse de rotation (degres/image)
PERIODE_MS     = 16      # periode de rafraichissement (~60 images/seconde)

# Couleurs
C_FOND="#1e2430"; C_TOLE="#9fb6c9"; C_TOLE_BRD="#5d7488"; C_VERIN="#2E75B6"
C_ROTATIF="#1F4E79"; C_VENTOUSE="#E08A00"; C_DEPOSE="#3a4759"
C_OK="#4ec9b0"; C_ALARME="#e06c5a"; C_TEXTE="#e6eaf0"

# Geometrie de la scene (en pixels)
SOL_Y      = 540        # niveau du sol
PILE_X     = 250        # centre de la pile (poste de prise, a gauche)
DEPOSE_X   = 670        # centre de la zone de depose (a droite)
CENTRE_X   = (PILE_X + DEPOSE_X) // 2     # axe du verin rotatif
RAYON      = (DEPOSE_X - PILE_X) // 2     # bras (prehension excentree)
LARG       = 220        # largeur de la plaque / des toles a l'ecran
GANTRY_Y   = 60         # hauteur du profile superieur (gantry)
HY_HAUT    = 135        # position haute de la tete (verin pneumatique sorti)
PILE_TOP_Y = 380        # sommet de la pile (maintenu constant par le chariot)
DEPOSE_Y   = 360        # surface de depose (= 998 mm reels)


# -----------------------------------------------------------------------------
# 2) SIMULATION DES CAPTEURS
# -----------------------------------------------------------------------------

def lire_capteur_inductif(toles_restantes):
    """Capteur inductif : True si une tole metallique reste au sommet."""
    return toles_restantes > 0

def lire_pression_vide(prise_reelle):
    """Capteur de pression : vide etabli (basse pression) si la prise est bonne,
    sinon pression proche de l'atmospherique. Bruit aleatoire ajoute."""
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
        self.cv = tk.Canvas(racine, width=920, height=580,
                            bg=C_FOND, highlightthickness=0)
        self.cv.pack()

        # Etat du systeme
        self.toles_deposees = 0          # compteur de toles deposees
        self.essais_restants = NB_ESSAIS
        self.etat = "DETECTER"           # etat courant de l'automate
        self.message = "Demarrage..."
        self.pression = 0.0
        self.tole_saisie = False         # une tole est-elle tenue ?
        self.couleur_msg = C_TEXTE

        self.hy = HY_HAUT                # hauteur de la tete (verin pneumatique)
        self.theta = 180.0              # angle du bras rotatif (180 deg = a gauche)

        random.seed(1)
        self.boucle()

    # --- Position horizontale de la plaque selon l'angle de rotation ----------

    def plaque_x(self):
        """La plaque est excentree d'un rayon par rapport a l'axe rotatif.
        theta = 180 deg -> au-dessus de la pile ; theta = 0 deg -> depose."""
        return CENTRE_X + RAYON * math.cos(math.radians(self.theta))

    # --- Dessin de la scene ---------------------------------------------------

    def dessiner(self):
        self.cv.delete("all")
        self.cv.create_line(40, SOL_Y, 880, SOL_Y, fill="#3a4759", width=3)

        # Profile superieur (gantry) + axe du verin rotatif
        self.cv.create_rectangle(70, GANTRY_Y - 10, 850, GANTRY_Y + 6,
                                 fill=C_DEPOSE, outline="#566375")

        # Pile maintenue a hauteur constante par le chariot elevateur
        if self.toles_deposees < LOT_TOLES:
            self.cv.create_rectangle(PILE_X - LARG/2, PILE_TOP_Y,
                                     PILE_X + LARG/2, SOL_Y,
                                     fill=C_TOLE, outline=C_TOLE_BRD)
            y = PILE_TOP_Y
            while y < SOL_Y - 4:
                self.cv.create_line(PILE_X - LARG/2, y, PILE_X + LARG/2, y,
                                    fill=C_TOLE_BRD); y += 7
        self.cv.create_text(PILE_X, SOL_Y + 18, fill=C_TEXTE,
                            text="Pile - chariot elevateur (hauteur constante)",
                            font=("Arial", 10))

        # Zone de depose + toles deja deposees
        self.cv.create_rectangle(DEPOSE_X - LARG/2, DEPOSE_Y,
                                 DEPOSE_X + LARG/2, DEPOSE_Y + 14,
                                 fill=C_DEPOSE, outline="#566375")
        for i in range(min(self.toles_deposees, 16)):
            yy = DEPOSE_Y - 3 - i * 3
            self.cv.create_rectangle(DEPOSE_X - LARG/2 + 6, yy,
                                     DEPOSE_X + LARG/2 - 6, yy + 3,
                                     fill=C_TOLE, outline=C_TOLE_BRD)
        self.cv.create_text(DEPOSE_X, DEPOSE_Y + 34, fill=C_TEXTE,
                            text="Zone de depose (998 mm)", font=("Arial", 10))

        # Fleche de rotation 180 deg autour de l'axe rotatif
        self.cv.create_arc(CENTRE_X - 40, GANTRY_Y + 20, CENTRE_X + 40, GANTRY_Y + 70,
                           start=0, extent=180, style="arc", outline=C_VENTOUSE, width=2)
        self.cv.create_text(CENTRE_X, GANTRY_Y + 80, fill=C_VENTOUSE,
                            text="rotatif 180 deg", font=("Arial", 9))

        # Tete mobile : verin pneumatique (axe) + bras rotatif + plaque
        gx = self.plaque_x()
        self.cv.create_line(CENTRE_X, GANTRY_Y + 6, CENTRE_X, self.hy,
                            fill=C_VERIN, width=10)                  # verin pneumatique
        self.cv.create_rectangle(CENTRE_X - 16, self.hy - 8, CENTRE_X + 16, self.hy + 8,
                                 fill=C_ROTATIF, outline="#10325a")  # bloc rotatif (hub)
        self.cv.create_line(CENTRE_X, self.hy, gx, self.hy,
                            fill=C_ROTATIF, width=6)                 # bras excentre
        self.cv.create_rectangle(gx - LARG/2, self.hy - 6, gx + LARG/2, self.hy + 6,
                                 fill=C_VERIN, outline="#1f5285")    # plaque de prehension
        for dx in (-0.36, -0.12, 0.12, 0.36):                       # 4 ventouses
            vx = gx + dx * LARG
            self.cv.create_oval(vx - 7, self.hy + 6, vx + 7, self.hy + 18,
                                fill=C_VENTOUSE, outline="#8a5400")

        # Tole en cours de manipulation
        if self.tole_saisie:
            self.cv.create_rectangle(gx - LARG/2, self.hy + 18, gx + LARG/2, self.hy + 24,
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
        if self.toles_deposees >= LOT_TOLES:
            self.etat = "FINI"
            self.message = "Production terminee : {} toles deposees.".format(LOT_TOLES)
            self.couleur_msg = C_OK
            return

        if self.etat == "DETECTER":
            if lire_capteur_inductif(LOT_TOLES - self.toles_deposees):
                self.message = "Tole detectee : descente du verin"
                self.couleur_msg = C_TEXTE
                self.etat = "DESCENDRE"
            else:
                self.etat = "FINI"

        elif self.etat == "DESCENDRE":
            cible = PILE_TOP_Y - 18           # descendre jusqu'au sommet de la pile
            if self.hy < cible:
                self.hy = min(self.hy + V_VERT, cible)
            else:
                self.message = "Activation du vide (ventouses)"
                self.essais_restants = NB_ESSAIS
                self.etat = "SAISIR"

        elif self.etat == "SAISIR":
            prise_reelle = random.random() > 0.10       # 9 chances sur 10
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
                    self.etat = "DESCENDRE"

        elif self.etat == "REMONTER":
            if self.hy > HY_HAUT:
                self.hy = max(self.hy - V_VERT, HY_HAUT)
            else:
                self.message = "Rotation 180 deg (verin rotatif)"
                self.couleur_msg = C_TEXTE
                self.etat = "ROT_ALLER"

        elif self.etat == "ROT_ALLER":
            if self.theta > 0:                # rotation 180 deg -> 0 deg (vers depose)
                self.theta = max(self.theta - V_ROT, 0)
            else:
                self.etat = "DESCENDRE2"

        elif self.etat == "DESCENDRE2":
            cible = DEPOSE_Y - 18
            if self.hy < cible:
                self.hy = min(self.hy + V_VERT, cible)
            else:
                self.tole_saisie = False      # coupure du vide -> lacher
                self.toles_deposees += 1
                self.message = "Tole n{} deposee".format(self.toles_deposees)
                self.couleur_msg = C_OK
                self.etat = "REMONTER2"

        elif self.etat == "REMONTER2":
            if self.hy > HY_HAUT:
                self.hy = max(self.hy - V_VERT, HY_HAUT)
            else:
                self.message = "Rotation retour 180 deg"
                self.couleur_msg = C_TEXTE
                self.etat = "ROT_RETOUR"

        elif self.etat == "ROT_RETOUR":
            if self.theta < 180:              # retour 0 deg -> 180 deg (vers pile)
                self.theta = min(self.theta + V_ROT, 180)
            else:
                self.etat = "DETECTER"        # nouveau cycle

    # --- Boucle d'animation ---------------------------------------------------

    def boucle(self):
        self.etape_automate()
        self.dessiner()
        if self.etat != "FINI":
            self.racine.after(PERIODE_MS, self.boucle)


# -----------------------------------------------------------------------------
# 4) POINT D'ENTREE
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    racine = tk.Tk()
    app = Simulateur(racine)
    racine.mainloop()
