import pygame
import sys
import random as rd
import JEUX
import time

def main():
    background_colour = (255,255,255)
    darkgreen = (0,150,0)
    lightgreen = (50,200,50)
    black=(0,0,0)
    gray = (150,150,150)
    blue = (0,0,255)
    red = (255,0,0)
    green=[lightgreen,darkgreen]
    (width, height) = (950, 650)
    square_size = 50
    screen = pygame.display.set_mode((1300, height))
    snake=pygame.image.load('apple.png')
    pygame.display.set_icon(snake)
    pygame.display.set_caption('Snake')
    pygame.init()
    screen.fill(background_colour)
    clock = pygame.time.Clock()
    
    for col in range(width//square_size):
        for line in range(height//square_size):
            pygame.draw.rect(screen, green[(col+line)%2], (square_size*col, square_size*line, square_size, square_size))
    class Snake:
        def __init__(self,S,direction):
            self.S=S
            self.direction = direction
        def inclusion(self):
            a,b=rd.randint(0,18),rd.randint(0,12)
            s = [self.S[i][:2] for i in range(len(self.S))]
            if [a,b] in s:
                a,b=Snake.inclusion()
            return a,b
        def Dico(self):
            head0=pygame.image.load('head0.png')
            head1=pygame.image.load('head1.png')
            tail0=pygame.image.load('tail0.png')
            tail1=pygame.image.load('tail1.png')
            H,T={},{}
            for arrow in ['up','right','down','left']:
                H[arrow]=[head0,head1]
                head0=pygame.transform.rotate(head0,-90)
                head1=pygame.transform.rotate(head1,-90)
                T[arrow]=[tail0,tail1]
                tail0=pygame.transform.rotate(tail0,-90)
                tail1=pygame.transform.rotate(tail1,-90)
            return H,T
        def move(self,screen,fruit):
            square_size=50
            blue = (0,0,255)
            green=[(50,200,50),(0,150,0)]
            n=len(self.S)-1
            if self.direction=='start':
                return 'start'
            for i in range(n,-1,-1):
                if i == len(self.S)-1:
                    grow=self.S[i].copy()
                    pygame.draw.rect(screen, green[(self.S[i][0]+self.S[i][1])%2], (square_size*self.S[i][0], square_size*self.S[i][1], square_size, square_size))
                    self.S[i]=self.S[i-1].copy()
                    if self.S[i][2]==self.S[i-2][2]:
                        screen.blit(T[self.S[i][2]][(self.S[i][0]+self.S[i][1])%2],(square_size*self.S[i][0],square_size*self.S[i][1]))
                    else:
                        screen.blit(T[self.S[i-2][2]][(self.S[i][0]+self.S[i][1])%2],(square_size*self.S[i][0],square_size*self.S[i][1]))
                elif i !=0:
                    self.S[i]=self.S[i-1].copy()   
                    pygame.draw.rect(screen, blue, (square_size*self.S[i][0], square_size*self.S[i][1], square_size, square_size))
                else:
                    if self.direction == "up":
                        self.S[i][1]-=1
                        self.S[i][2]="up"
                    if self.direction == "down":
                        self.S[i][1]+=1
                        self.S[i][2]="down"
                    if self.direction == "right":
                        self.S[i][0]+=1
                        self.S[i][2]="right"
                    if self.direction == "left":
                        self.S[i][0]-=1
                        self.S[i][2]="left"
                    if self.S[i][0] in [-1,19] or self.S[i][1] in [-1,13] or self.S[i][:2] in  [self.S[i][:2] for i in range(1,len(self.S)-1)]:
                        return "end"
                    if self.S[i][:2] == fruit:
                       screen.blit(H[self.direction][(self.S[i][0]+self.S[i][1])%2], (square_size*self.S[i][0], square_size*self.S[i][1], square_size, square_size))
                       screen.blit(T[self.S[n][2]][(grow[0]+grow[1])%2], (square_size*grow[0], square_size*grow[1], square_size, square_size))
                       pygame.draw.rect(screen, blue, (square_size*self.S[n][0],square_size*self.S[n][1], square_size, square_size))
                       self.S.append(grow)
                       return 'eat'
                    screen.blit(H[self.direction][(self.S[i][0]+self.S[i][1])%2],(square_size*self.S[i][0],square_size*self.S[i][1]))
            pygame.display.update()
    Snake=Snake([[9,5,'up'],[9,6,'up'],[9,7,'up']],'start') 
    H,T=Snake.Dico()
    screen.blit(H['up'][(Snake.S[0][0]+Snake.S[0][1])%2],(square_size*Snake.S[0][0],square_size*Snake.S[0][1]))
    pygame.draw.rect(screen, blue, (square_size*Snake.S[1][0], square_size*Snake.S[1][1], square_size, square_size))
    screen.blit(T['up'][(Snake.S[2][0]+Snake.S[2][1])%2],(square_size*Snake.S[2][0],square_size*Snake.S[2][1]))
    pygame.display.update()
    def main_over(score):
        pygame.draw.rect(screen, (255,255,255), (950, 0, 400, 600))
        font = pygame.font.SysFont('cambria math', 32)
        text = font.render('GAME OVER', black, True,red)
        textRect = text.get_rect()
        textRect.center = (1125, 100)
        f=open('score.txt','r')
        highscore=f.read()
        f.close()
        if score>= int(highscore):
            f=open('score.txt','w')
            f.write(str(score))
            f.close()
            text1 = font.render('Nouveau record', black, black)
            text1Rect = text1.get_rect()
            text1Rect.center = (1125, 200)
            texts = font.render('Avec un score de '+str(score), black, black)
            textsRect = texts.get_rect()
            textsRect.center = (1125, 250)
            screen.blit(texts,textsRect)
        else:
            text1 = font.render('Votre score :  '+str(score), black, black)
            text1Rect = text1.get_rect()
            text1Rect.center = (1125, 200)
            texts = font.render('Le highscore : '+str(highscore), black, black)
            textsRect = texts.get_rect()
            textsRect.center = (1125, 250)

        screen.blit(text1,text1Rect)
        screen.blit(texts,textsRect)
        run=True
        button = font.render('Rejouer',black, True,gray)
        Rect=button.get_rect()
        Rect.center = (1125,400)
        button1 = font.render('Menu',black, True,gray)
        Rect1=button1.get_rect()
        Rect1.center = (1125,500)
        while run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if event.key == pygame.K_RETURN:
                        main()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos  # gets mouse position
    
                    # checks if mouse position is over the button
    
                    if Rect.collidepoint(mouse_pos):           
                        main()
                    if Rect1.collidepoint(mouse_pos):
                        run = False
    
            screen.blit(text, textRect)
            screen.blit(button,Rect)
            screen.blit(button1,Rect1)
            pygame.display.update()
        JEUX.main()
        
      
    running = True
    score = 0

    apple0=pygame.image.load('apple0.png')
    apple1=pygame.image.load('apple1.png')
    apple=[apple0,apple1]
    x,y=Snake.inclusion()
    screen.blit(apple[(x+y)%2],(square_size*x,square_size*y))
    font = pygame.font.SysFont('cambria math', 32)
    text = font.render('Utiliser les flèches', black, black)
    textRect = text.get_rect()
    textRect.center = (1125, 100)
    text1 = font.render('pour jouer !', black, black)
    text1Rect = text1.get_rect()
    text1Rect.center = (1125, 125)
    text2 = font.render('⇧', black, black)
    text2Rect = text2.get_rect()
    text2Rect.center = (1125, 175)
    screen.blit(text,textRect)
    text3= font.render('⇦ ⇩ ⇨', black, black)
    text3Rect = text3.get_rect()
    text3Rect.center = (1125, 200)
    screen.blit(text,textRect)
    screen.blit(text1,text1Rect)
    screen.blit(text2,text2Rect)
    screen.blit(text3,text3Rect)
    pygame.display.update()
    while running:
        state = Snake.move(screen,[x,y])
        if state == 'end':
            running = False
        elif state == 'eat':
            score+=100
            x,y=Snake.inclusion()  
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_UP:
                    Snake.direction='up'
                if event.key == pygame.K_DOWN:
                    Snake.direction='down'
                if event.key == pygame.K_RIGHT:
                    Snake.direction='right'        
                if event.key == pygame.K_LEFT:
                    Snake.direction='left'
        screen.blit(apple[(x+y)%2],(square_size*x,square_size*y))
        pygame.display.update()
        clock.tick(10)
        if state!='start':
            score +=1
        pygame.draw.rect(screen, (255,255,255), (950, 275, 400, 50))
        texts = font.render('Votre Score : '+str(score), black, black)
        textsRect = texts.get_rect()
        textsRect.center = (1125, 300)
        screen.blit(texts,textsRect)
    main_over(score)
                      
if __name__ == "__main__":
    main()