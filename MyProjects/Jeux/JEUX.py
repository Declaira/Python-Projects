import Puissance_4_ULTIMATE
import Snake
import Démineur
import pygame
import sys




def main():
    BLACK = (0, 0, 0)
    GRAY = (150,150,150)
    WHITE = (255,255,255)
    GREEN = (0, 255, 0)
    BLUE = (63,72,204)
    WIDTH = 1200
    HEIGHT = 750
    screen = pygame.display.set_mode((WIDTH,HEIGHT))
    jeux=pygame.image.load('jeu.png').convert()
    background=pygame.image.load('background.png')
    pygame.display.set_icon(jeux)
    pygame.display.set_caption('Jeux',)
    pygame.init()
    bg = [255, 255, 255]
    font = pygame.font.Font('freesansbold.ttf', 32)
    #text = font.render('À quel jeu voulez-vous jouer ?', BLACK, BLACK)
    #textRect = text.get_rect()
    #textRect.center = (WIDTH//2, HEIGHT//2)
    button = font.render('Puissance 4',BLACK,True,BLUE)
    Rect=button.get_rect()
    Rect.center = (300,250)
    button1 = font.render('Snake',BLACK,True,GREEN)
    Rect1=button1.get_rect()
    Rect1.center = (875,250)
    button2 = font.render('Démineur',BLACK,True,GRAY)
    Rect2=button1.get_rect()
    Rect2.center = (550,250)
    run = True
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos  # gets mouse position

                # checks if mouse position is over the button

                if Rect.collidepoint(mouse_pos):           
                    jeu = 0
                    run = False
                if Rect1.collidepoint(mouse_pos):
                    jeu = 1
                    run = False
                if Rect2.collidepoint(mouse_pos):
                    jeu = 2
                    run = False

        screen.blit(background,(0,0))
        #screen.blit(text, textRect)
        screen.blit(button,Rect)
        screen.blit(button1,Rect1)
        screen.blit(button2,Rect2)
        pygame.display.update()

    if jeu == 0:
        Puissance_4_ULTIMATE.main()
    elif jeu == 1:
        Snake.main()
    elif jeu == 2:
        Démineur.main()
if __name__ == "__main__":
    main()
