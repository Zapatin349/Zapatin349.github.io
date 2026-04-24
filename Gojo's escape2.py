# =============================================================================
# GOJO'S ESCAPE
# =============================================================================

# =============================================================================
# CONTROLS
# AWSD (recomendable) i les fletxes del teclat per desplaçarte.
# Tecla F per activar Infinit (escud).
# Q per teletransportarte a l'esquerra del mapa  i E per anar a la dreta.
# Tecla Espai per disparar Vermells.
# =============================================================================

import random
import pygame
import time
from pygame.locals import *


# =============================================================================
# CLASSES SECUNDÀRIES (Bala i Explosió)
# =============================================================================
class Bala:
    def __init__(self, imatge, x, y):
        self.imatge = imatge
        # La bala apareix just a la punta de la nau (midbottom des del top de la nau)
        self.rect = self.imatge.get_rect(midbottom=(x, y))
        self.velocitat = 15 # Velocitat de la bala

    def moure(self):
        self.rect.y -= self.velocitat

    def fora_pantalla(self):
        return self.rect.bottom < 0


class Explosio:
    def __init__(self, imatge, x, y):
        self.imatge = imatge
        self.rect = self.imatge.get_rect(center=(x, y))
        self.temps_creacio = pygame.time.get_ticks()
        self.duracio = 300  # Mil·lisegons que durarà el Black Flash a la pantalla

    def ha_acabat(self, temps_actual):
        return temps_actual - self.temps_creacio > self.duracio


# =============================================================================
# CLASSE METEOR
# =============================================================================
class Meteor:
    def __init__(self, imatge, velocitat, pos_x, pos_y):
        self.imatge = imatge
        self.velocitat = velocitat
        self.x = pos_x
        self.y = pos_y
        self.img_meteor = pygame.image.load(self.imatge)
        self.rect_meteor = self.img_meteor.get_rect(midbottom=(self.x, self.y))

    def reiniciar(self):
        self.x = random.randint(30, 610)
        self.y = -64
        self.velocitat = random.randint(2, 10)

    def moure(self):
        self.y += self.velocitat
        self.rect_meteor = self.img_meteor.get_rect(midbottom=(self.x, self.y))

    def ha_sortit_per_baix(self):
        return self.y >= 480

    def puntuar_i_reiniciar(self):
        if self.ha_sortit_per_baix():
            self.reiniciar()
            return 5
        return 0


# =============================================================================
# CLASSE NAU
# =============================================================================
class Nau:
    def __init__(self, imatge, velocitat, pos_x, pos_y, vides, imatge_vida):
        self.imatge = imatge
        self.velocitat = velocitat
        self.x = pos_x
        self.y = pos_y
        self.img = pygame.image.load(self.imatge)
        self.img_vida = pygame.image.load(imatge_vida)
        self.rect = self.img.get_rect(midbottom=(self.x, self.y))
        self.vides = vides
        self.vides_originals = vides

    def reiniciar(self):
        self.x = 300
        self.y = 460
        self.rect = self.img.get_rect(midbottom=(self.x, self.y))
        self.vides = self.vides_originals

    def moure(self, pantalla_rect):
        keys = pygame.key.get_pressed()
        if keys[K_a] or keys[K_LEFT]:
            self.rect.x -= self.velocitat
        if keys[K_d] or keys[K_RIGHT]:
            self.rect.x += self.velocitat
        if keys[K_w] or keys[K_UP]:
            self.rect.y -= self.velocitat
        if keys[K_s] or keys[K_DOWN]:
            self.rect.y += self.velocitat

        self.rect.clamp_ip(pantalla_rect)

    def restar_vida(self):
        self.vides -= 1

    def esta_viva(self):
        return self.vides > 0


# =============================================================================
# CLASSE JOC
# =============================================================================
class Joc:
    PANTALLA_INICI = "inici"
    PANTALLA_JOC = "joc"
    PANTALLA_GAME_OVER = "game_over"

    def __init__(self, ample, alt, fps, nombre_meteors):
        pygame.init()
        self.ample = ample
        self.alt = alt
        self.fps = fps
        self.numero_meteors = nombre_meteors

        self.pantalla = pygame.display.set_mode((self.ample, self.alt))
        pygame.display.set_caption("Satoru Gojo - Buit Infinit")
        self.rellotge = pygame.time.Clock()

        self.meteors = []
        self.bales = []
        self.explosions = []
        self.punts = 0

        # --- ASSETS GRÀFICS I SONORS ---
        imatge_fons_original = pygame.image.load('Assets/Vacio infinito.png')
        self.fons_joc = pygame.transform.scale(imatge_fons_original, (self.ample, self.alt))

        self.so_explosio = pygame.mixer.Sound('Assets/Explosio.mp3')
        self.so_teleport = pygame.mixer.Sound('Assets/TELEPORT.mp3')
        self.so_infinito = pygame.mixer.Sound('Assets/infinito.mp3')

        # Nous assets de tret i Black Flash
        self.img_bala = pygame.image.load('Assets/VIDA2.png')
        self.so_disparo = pygame.mixer.Sound('Assets/DISPARO.mp3')
        self.img_black_flash = pygame.image.load('Assets/Black_ flash_ impact.png')
        self.so_black_flash = pygame.mixer.Sound('Assets/Black Flash.mp3')

        self.img_infinito = pygame.image.load('Assets/Infinito.png')
        self.img_inici = pygame.image.load('Assets/PANTALLA DE INICI.png')
        self.img_game_over = pygame.image.load('Assets/GAME_OVER.png')

        self.nau = Nau('Assets/Gokumonkyo.png', velocitat=5, pos_x=300, pos_y=450,
                       vides=3, imatge_vida='Assets/VIDA1.png')

        # --- VARIABLES D'HABILITATS ---
        self.infinito_activo = False
        self.temps_ultim_infinito = -90000
        self.temps_ultim_tp_q = -5000
        self.temps_ultim_tp_e = -5000
        self.temps_ultim_disparo = 0  # Per controlar la cadència de foc

        self.pantalla_activa = self.PANTALLA_INICI

    # -------------------------------------------------------------------------
    # GESTIÓ DE PANTALLES
    # -------------------------------------------------------------------------
    def iniciar_joc(self):
        while True:
            if self.pantalla_activa == self.PANTALLA_INICI:
                self.mostrar_pantalla_inici()
            elif self.pantalla_activa == self.PANTALLA_JOC:
                self.preparar_partida()
                self.mostrar_pantalla_joc()
            elif self.pantalla_activa == self.PANTALLA_GAME_OVER:
                self.mostrar_pantalla_game_over()

    def mostrar_pantalla_inici(self):
        pygame.mixer.music.load('Assets/Pantalla_de_inici.mp3')
        pygame.mixer.music.play(-1)

        en_espera = True
        while en_espera:
            self.pantalla.blit(self.img_inici, (0, 40))
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                # Usem RETURN (Enter) per no confondre amb l'Espai de disparar
                if event.type == pygame.KEYDOWN and event.key == K_RETURN:
                    self.pantalla_activa = self.PANTALLA_JOC
                    en_espera = False

            self.rellotge.tick(self.fps)

    def mostrar_pantalla_game_over(self):
        self.so_infinito.stop()
        pygame.mixer.music.load('Assets/GAME_OVER.mp3')
        pygame.mixer.music.play(0)
        pygame.mixer.music.fadeout(5000)

        en_espera = True
        while en_espera:
            self.pantalla.blit(self.img_game_over, (0, 40))
            self._dibuixar_text(f"Puntuació final: {self.punts}", mida=40, color=(255, 255, 255),
                                x=self.ample // 2, y=400, centrat=True)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN:
                    self.pantalla_activa = self.PANTALLA_INICI
                    en_espera = False

            self.rellotge.tick(self.fps)

    def mostrar_pantalla_joc(self):
        pygame.mixer.music.load('Assets/MUSICA_DE_PARTIDA.mp3')
        pygame.mixer.music.play(-1)

        while self.pantalla_activa == self.PANTALLA_JOC:
            self._gestionar_events()

            self.pantalla.blit(self.fons_joc, (0, 0))
            self._gestionar_habilitats()

            self.nau.moure(self.pantalla.get_rect())
            self._moure_meteors()
            self._moure_bales_i_explosions()  # Nova funció
            self._control_colisions()

            self._dibuixar_meteors()
            self._dibuixar_bales_i_explosions()  # Nova funció
            self._dibuixar_nau()
            self._dibuixar_vides()
            self._dibuixar_interficie_habilitats()

            if not self.nau.esta_viva():
                self.pantalla_activa = self.PANTALLA_GAME_OVER

            pygame.display.update()
            self.rellotge.tick(self.fps)

    # -------------------------------------------------------------------------
    # PREPARACIÓ DE LA PARTIDA
    # -------------------------------------------------------------------------
    def preparar_partida(self):
        self.meteors.clear()
        self.bales.clear()
        self.explosions.clear()
        self.so_infinito.stop()

        self.infinito_activo = False
        self.temps_ultim_infinito = -90000
        self.temps_ultim_tp_q = -5000
        self.temps_ultim_tp_e = -5000
        self.temps_ultim_disparo = 0

        for i in range(self.numero_meteors):
            meteor_nou = Meteor('Assets/Meteoro.png', velocitat=0, pos_x=0, pos_y=0)
            meteor_nou.reiniciar()
            self.meteors.append(meteor_nou)

        self.nau.reiniciar()
        self.punts = 0

    # -------------------------------------------------------------------------
    # LÒGICA DEL JOC
    # -------------------------------------------------------------------------
    def _gestionar_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

    def _gestionar_habilitats(self):
        temps_actual = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()

        # 1. INFINIT (Tecla I)
        if keys[K_f] and not self.infinito_activo and (temps_actual - self.temps_ultim_infinito >= 90000):
            self.infinito_activo = True
            self.temps_ultim_infinito = temps_actual
            self.so_infinito.play(-1)

        if self.infinito_activo and (temps_actual - self.temps_ultim_infinito >= 10000):
            self.infinito_activo = False
            self.so_infinito.stop()

        # 2. TELETRANSPORT DRETA (Tecla E)
        if keys[K_e] and temps_actual - self.temps_ultim_tp_e >= 5000:
            self.nau.rect.right = self.ample
            self.temps_ultim_tp_e = temps_actual
            self.so_teleport.play()

        # 3. TELETRANSPORT ESQUERRA (Tecla Q)
        if keys[K_q] and temps_actual - self.temps_ultim_tp_q >= 5000:
            self.nau.rect.left = 0
            self.temps_ultim_tp_q = temps_actual
            self.so_teleport.play()

        # 4. DISPARAR (Tecla ESPAI)
        # S'ha afegit un límit de temps (250ms) per no disparar 60 bales per segon
        if keys[K_SPACE] and temps_actual - self.temps_ultim_disparo >= 250:
            nova_bala = Bala(self.img_bala, self.nau.rect.centerx, self.nau.rect.top)
            self.bales.append(nova_bala)
            self.so_disparo.play()
            self.temps_ultim_disparo = temps_actual

    def _moure_meteors(self):
        for meteor in self.meteors:
            meteor.moure()
            self.punts += meteor.puntuar_i_reiniciar()

    def _moure_bales_i_explosions(self):
        # Moure bales i eliminar les que surten de la pantalla
        for bala in self.bales[:]:
            bala.moure()
            if bala.fora_pantalla():
                self.bales.remove(bala)

        # Eliminar explosions que ja han superat el seu temps
        temps_actual = pygame.time.get_ticks()
        for exp in self.explosions[:]:
            if exp.ha_acabat(temps_actual):
                self.explosions.remove(exp)

    def _control_colisions(self):
        # 1. Col·lisions Nau - Meteorit
        for meteor in self.meteors:
            if meteor.rect_meteor.colliderect(self.nau.rect):
                if self.infinito_activo:
                    self.punts += 10
                    meteor.reiniciar()
                else:
                    self.so_explosio.play()
                    meteor.reiniciar()
                    self.nau.restar_vida()

                    # 2. Col·lisions Bala - Meteorit
        for bala in self.bales[:]:
            for meteor in self.meteors:
                if bala.rect.colliderect(meteor.rect_meteor):
                    # Guanyar punts i so de Black Flash
                    self.punts += 10
                    self.so_black_flash.play()

                    # Crear l'explosió on estava el meteorit
                    nova_exp = Explosio(self.img_black_flash, meteor.rect_meteor.centerx, meteor.rect_meteor.centery)
                    self.explosions.append(nova_exp)

                    # Eliminar la bala i reiniciar el meteorit
                    if bala in self.bales:
                        self.bales.remove(bala)
                    meteor.reiniciar()
                    break  # Passem a la següent bala

    # -------------------------------------------------------------------------
    # DIBUIX DELS ELEMENTS
    # -------------------------------------------------------------------------
    def _dibuixar_meteors(self):
        for meteor in self.meteors:
            self.pantalla.blit(meteor.img_meteor, meteor.rect_meteor)

    def _dibuixar_bales_i_explosions(self):
        for bala in self.bales:
            self.pantalla.blit(bala.imatge, bala.rect)
        for exp in self.explosions:
            self.pantalla.blit(exp.imatge, exp.rect)

    def _dibuixar_nau(self):
        self.pantalla.blit(self.nau.img, self.nau.rect)
        if self.infinito_activo:
            rect_infinito = self.img_infinito.get_rect(center=self.nau.rect.center)
            self.pantalla.blit(self.img_infinito, rect_infinito)

    def _dibuixar_vides(self):
        posicions_x = [580, 540, 500]
        for i in range(self.nau.vides):
            if i < len(posicions_x):
                self.pantalla.blit(self.nau.img_vida, (posicions_x[i], 20))

    def _dibuixar_interficie_habilitats(self):
        self._dibuixar_text(str(self.punts), mida=32, color=(255, 255, 255), x=150, y=30)
        temps_actual = pygame.time.get_ticks()

        if temps_actual - self.temps_ultim_tp_q >= 5000:
            self._dibuixar_text("TP Esq (Q): Llest", mida=24, color=(0, 255, 255), x=10, y=10)
        else:
            segons = 5 - ((temps_actual - self.temps_ultim_tp_q) // 1000)
            self._dibuixar_text(f"TP Esq (Q): {segons}s", mida=24, color=(150, 150, 150), x=10, y=10)

        if temps_actual - self.temps_ultim_tp_e >= 5000:
            self._dibuixar_text("TP Dret (E): Llest", mida=24, color=(0, 255, 255), x=10, y=35)
        else:
            segons = 5 - ((temps_actual - self.temps_ultim_tp_e) // 1000)
            self._dibuixar_text(f"TP Dret (E): {segons}s", mida=24, color=(150, 150, 150), x=10, y=35)

        if self.infinito_activo:
            self._dibuixar_text("INFINIT ACTIU!", mida=24, color=(255, 0, 255), x=10, y=60)
        elif temps_actual - self.temps_ultim_infinito >= 90000:
            self._dibuixar_text("Infinit: Llest (F)", mida=24, color=(255, 255, 255), x=10, y=60)
        else:
            segons = 90 - ((temps_actual - self.temps_ultim_infinito) // 1000)
            self._dibuixar_text(f"Infinit: {segons}s", mida=24, color=(255, 100, 100), x=10, y=60)

    def _dibuixar_text(self, text, mida, color, x, y, centrat=False):
        font = pygame.font.SysFont(None, mida)
        imatge_text = font.render(text, True, color)

        if centrat:
            rect_text = imatge_text.get_rect(center=(x, y))
            self.pantalla.blit(imatge_text, rect_text)
        else:
            self.pantalla.blit(imatge_text, (x, y))


# =============================================================================
# INICI DEL PROGRAMA
# =============================================================================
partida = Joc(
    ample=640,
    alt=480,
    fps=60,
    nombre_meteors=50
)
partida.iniciar_joc()