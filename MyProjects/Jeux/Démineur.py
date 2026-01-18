import pygame
import sys
import random as rd
import JEUX
import time

def main():
    lightgray = (200,200,200)
    darkgray = (100,100,100)
    black=(0,0,0)
    white = (255,255,255)
    gray = (150,150,150)
    blue = (0,0,255)
    red = (255,0,0)
    orange = (255,150,0)
    yellow = (255,255,0)
    brown = (200,100,0)
    darkred=(120,67,21)
    (width, height) = (960, 640)
    screen = pygame.display.set_mode((1280, height))
    bombicon=pygame.image.load('bombicon.png')
    pygame.display.set_icon(bombicon)
    pygame.display.set_caption('Démineur')
    pygame.init()
    screen.fill(lightgray)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('cambria math', 32)
    input_box = pygame.Rect(100, 100, 140, 50)
    input_box1 = pygame.Rect(100, 100, 140, 50)
    text1 = font.render('Choix des paramètres', black, black)
    text1Rect = text1.get_rect()
    text1Rect.center = (1125, 100)
    text2 = font.render('de la partie', black, black)
    text2Rect = text2.get_rect()
    text2Rect.center = (1125, 150)
    screen.blit(text1,text1Rect)
    screen.blit(text2,text2Rect)
    text3 = font.render('Difficulté :', black, black)
    text3Rect = text3.get_rect()
    text3Rect.center = (1125, 250)
    text4 = font.render('Nb de mines', black, black)
    text4Rect = text4.get_rect()
    text4Rect.center = (1075, 400)
    run=True
    button = font.render('Confirmer',black, True,gray)
    Rect=button.get_rect()
    Rect.center = (1125,500)
    color_inactive = pygame.Color('gray')
    color_active = pygame.Color('black')
    color = color_inactive
    active = False
    error = False
    difficulty=['    débutant','intermédiaire','       expert',64,40,32,'20','50','100']
    d=0
    square_size=difficulty[d+3]
    text=difficulty[d+6]
    for col in range(width//square_size):
        for line in range(height//square_size):
            pygame.draw.rect(screen, darkgray , (square_size*col, square_size*line, square_size, square_size),1)
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if active:
                    if event.key == pygame.K_RETURN:
                        if int(text) <= (width//square_size*height//square_size)//2:
                            run = False
                        else:
                            error=True
                            
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        text += event.unicode
            if event.type == pygame.MOUSEBUTTONDOWN:
                # If the user clicked on the input_box rect.
                if input_box.collidepoint(event.pos):
                    # Toggle the active variable.
                    active = not active
                else:
                    active = False
                    # Change the current color of the input box.
                color = color_active if active else color_inactive
                # checks if mouse position is over the button
                if input_box1.collidepoint(event.pos):
                    error = False
                    d=(d+1)%3
                    square_size=difficulty[d+3]
                    text=difficulty[d+6]
                    screen.fill(lightgray)
                    for col in range(width//square_size):
                        for line in range(height//square_size):
                            pygame.draw.rect(screen, darkgray , (square_size*col, square_size*line, square_size, square_size),1)
                if Rect.collidepoint(event.pos):
                    test=True
                    try:
                        int(text)
                    except ValueError:
                        test=False
                    if test:
                        if int(text) <= (width//square_size*height//square_size)//2:
                            run = False
                        else:
                            error=1
                    else:
                        error=2
        pygame.draw.rect(screen, white, (960, 0, 400, 640))
        screen.blit(text1, text1Rect)
        screen.blit(text2, text2Rect)
        screen.blit(button,Rect)
        screen.blit(text3,text3Rect)
        screen.blit(text4,text4Rect)
        if error ==1:
            text5 = font.render('Erreur sur le nombre', black, black)
            text5Rect = text5.get_rect()
            text5Rect.center = (1125, 550)
            text6 = font.render('de mines (<='+str((width//square_size*height//square_size)//2)+')', black, black)
            text6Rect = text6.get_rect()
            text6Rect.center = (1125,600)
            screen.blit(text5,text5Rect)
            screen.blit(text6,text6Rect)
        elif error == 2:
            text5 = font.render('Erreur, le nombre de', black, black)
            text5Rect = text5.get_rect()
            text5Rect.center = (1120, 550)
            text6 = font.render("mines n'est pas entier", black, black)
            text6Rect = text6.get_rect()
            text6Rect.center = (1120,600)
            screen.blit(text5,text5Rect)
            screen.blit(text6,text6Rect)
        txt_surface = font.render(text, True, color)
        txt_surface1 = font.render(difficulty[d], True, color_active)
        # Resize the box if the text is too long.
        w = max(45, txt_surface.get_width()+10)
        input_box.w = w
        input_box.center=(1220,400)
        input_box1.w = 200
        input_box1.h= 100
        input_box1.center=(1125,270)
        pygame.draw.rect(screen, color, input_box, 2)
        pygame.draw.rect(screen, color_active, input_box1, 2)
        # Blit the text.
        screen.blit(txt_surface, (input_box.x+5, input_box.y+5))
        screen.blit(txt_surface1, (input_box1.x+5, input_box1.y+50))
        pygame.display.update()
    
    class case:
        def __init__(self,x,y,discovered,neighbor):
            self.x=x
            self.y=y
            self.discovered=discovered
            self.neighbor= neighbor   

        def clicked(self,screen,box,f,square_size):
            if self.discovered==True or self.discovered=='flag' :
                return False
            self.discovered=True
            if self.neighbor == 'bomb':
                pygame.draw.rect(screen, red , (square_size*self.x+1, square_size*self.y+1, square_size-2, square_size-2))
                return True
            n_neighbor = self.neighbor[-1]
            pygame.draw.rect(screen, darkgray , (square_size*self.x, square_size*self.y, square_size, square_size),1)
            pygame.draw.rect(screen, white , (square_size*self.x+1, square_size*self.y+1, square_size-2, square_size-2))
            
            if n_neighbor == 0:
                V=[]
                for n in self.neighbor[:-1]:
                    V.append(box[n[1]][n[0]])
                for v in V:
                    v.clicked(screen,box,f,square_size)
    
            if n_neighbor == 1:
                pygame.draw.circle(screen, red, (square_size*self.x + square_size // 2, square_size*self.y + square_size // 2), square_size // 7)
            if n_neighbor == 2:
                pygame.draw.circle(screen, orange, (square_size*self.x + square_size // 2, square_size*self.y + square_size // 4), square_size // 8)
                pygame.draw.circle(screen, orange, (square_size*self.x + square_size // 2, square_size*self.y + 3*(square_size // 4)), square_size // 8)
            if n_neighbor == 3:
                pygame.draw.circle(screen, yellow, (square_size*self.x + square_size // 2, square_size*self.y + square_size // 4), square_size // 8)
                pygame.draw.circle(screen, yellow, (square_size*self.x + square_size // 4, square_size*self.y + 3*(square_size // 4)), square_size // 8)
                pygame.draw.circle(screen, yellow, (square_size*self.x + 3*(square_size // 4), square_size*self.y + 3*(square_size // 4)), square_size // 8)
            if n_neighbor == 4:
                pygame.draw.circle(screen, brown, (square_size*self.x + square_size // 4, square_size*self.y + square_size // 4), square_size // 8)
                pygame.draw.circle(screen, brown, (square_size*self.x + square_size // 4, square_size*self.y + 3*(square_size // 4)), square_size // 8)
                pygame.draw.circle(screen, brown, (square_size*self.x + 3*(square_size // 4), square_size*self.y + square_size // 4), square_size // 8)
                pygame.draw.circle(screen, brown, (square_size*self.x + 3*(square_size // 4), square_size*self.y + 3*(square_size // 4)), square_size // 8)
            if n_neighbor == 5:
                pygame.draw.circle(screen, blue, (square_size*self.x + square_size // 2, square_size*self.y + square_size // 5), square_size // 8)
                pygame.draw.circle(screen, blue, (square_size*self.x + square_size // 4, square_size*self.y + 3*(square_size // 7)), square_size // 8)
                pygame.draw.circle(screen, blue, (square_size*self.x + 3*(square_size // 4),square_size*self.y +3*(square_size // 7)), square_size // 8)
                pygame.draw.circle(screen, blue, (square_size*self.x + square_size // 3, square_size*self.y +3*(square_size // 4)), square_size // 8)
                pygame.draw.circle(screen, blue, (square_size*self.x +2*(square_size // 3),square_size*self.y  +3*(square_size // 4)), square_size // 8)
            if n_neighbor == 6:
                pygame.draw.circle(screen, darkred, (square_size*self.x +  square_size // 2,square_size*self.y + square_size // 6), square_size // 8)
                pygame.draw.circle(screen, darkred, (square_size*self.x + square_size // 4,square_size*self.y + 2*(square_size // 6)), square_size // 8)
                pygame.draw.circle(screen, darkred, (square_size*self.x + 3*(square_size // 4),square_size*self.y + 2*(square_size // 6)), square_size // 8)
                pygame.draw.circle(screen, darkred, (square_size*self.x + square_size // 4,square_size*self.y + 4*(square_size // 6)), square_size // 8)
                pygame.draw.circle(screen, darkred, (square_size*self.x + 3*(square_size // 4),square_size*self.y + 4*(square_size // 6)), square_size // 8)
                pygame.draw.circle(screen, darkred, (square_size*self.x +  square_size // 2,square_size*self.y + 5*(square_size // 6)), square_size // 8)
            pygame.display.update()
            f[0]-=1
            return False
        def flag(self,screen,flag,F,square_size,L=[]):
            if self.discovered=='flag':
                self.discovered='no'
                pygame.draw.rect(screen, darkgray , (square_size*self.x, square_size*self.y, square_size, square_size),1)
                pygame.draw.rect(screen, lightgray , (square_size*self.x+2, square_size*self.y+2, square_size-4, square_size-4))
                F[0]+=1
                if self.neighbor!='bomb':
                    for i in range(len(L)):
                        if L[i]==(self.x,self.y,False):
                            L.pop(i)
                            break
                else:
                    L+=[(self.x,self.y,True)]
            elif self.discovered=='no':
                if F[0]==0:
                    return False
                self.discovered='flag'
                screen.blit(flag,(self.x*square_size,self.y*square_size))
                pygame.display.update()
                F[0]-=1
                if self.neighbor!='bomb':
                    L+=[(self.x,self.y,False)]
                else:
                    for i in range(len(L)):
                        if L[i]==(self.x,self.y,True):
                            L.pop(i)
                            break
                return False

    def main_over(Temps,Resultat,square_size,L=[]):
        pygame.draw.rect(screen, white, (960, 0, 400, 600))
        font = pygame.font.SysFont('cambria math', 32)
        if Resultat:
            text = font.render('VICTOIRE', black, True,yellow)
        else:
            text = font.render('GAME OVER', black, True,red)
            for l in L:
                if l[2]:
                    screen.blit(bomb,(l[0]*square_size+square_size//16+1,l[1]*square_size+square_size//16+1))
                else:
                    d=square_size//1.17
                    pygame.draw.rect(screen, lightgray , (square_size*l[0]+2, square_size*l[1]+2, square_size-4, square_size-4))
                    screen.blit(bomb,(l[0]*square_size+square_size//16+1,l[1]*square_size+square_size//16+1))
                    pygame.draw.line(screen,red,(l[0]*square_size+square_size//16+1,l[1]*square_size+square_size//16+1),(l[0]*square_size+square_size//16+d,l[1]*square_size+square_size//16+d),square_size//8)
                    pygame.draw.line(screen,red,(l[0]*square_size+square_size//16+d,l[1]*square_size+square_size//16+1),(l[0]*square_size+square_size//16+1,l[1]*square_size+square_size//16+d),square_size//8)
            pygame.display.update()
        textRect = text.get_rect()
        textRect.center = (1125, 100)
        text1 = font.render('Votre temps :', black, black)
        text1Rect = text1.get_rect()
        text1Rect.center = (1125, 200)
        text2 = font.render(str(Temps//60)+' secondes', black, black)
        text2Rect = text2.get_rect()
        text2Rect.center = (1125, 230)
        screen.blit(text1,text1Rect)
        screen.blit(text2,text2Rect)
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
    def neighborhood(w,h,c,l):
            n=[]
            v=[[c-1,l-1],[c,l-1],[c+1,l-1],[c-1,l],[c+1,l],[c+1,l+1],[c,l+1],[c-1,l+1]]
            for i in range(8):
                if c == 0:
                    if v[i][0] == c-1 :
                        v[i] =['non','non']
                elif c == w-1:
                    if v[i][0] == c+1 :
                        v[i]=['non','non']
                if l == 0:
                    if v[i][1] == l-1 :
                        v[i]=['non','non']
                elif l == h-1:
                    if v[i][1] == l+1 :
                        v[i] =['non','non']
                if v[i]!=['non','non']:
                    n.append(v[i])
            n.append(0)
            return n  
    def main_game(square_size,n_bomb):
        
        pygame.draw.rect(screen, white, (960, 0, 400, 600))
        running = True
        box=[[case(col,line,'no',neighborhood(width//square_size,height//square_size,col,line)) for col in range(width//square_size)] for line in range(height//square_size)]
        for col in range(width//square_size):
            for line in range(height//square_size):
                pygame.draw.rect(screen, darkgray , (square_size*col, square_size*line, square_size, square_size),1)
        finished=[height//square_size*width//square_size-n_bomb]
        Time = 0
        F=[n_bomb]
        L=[[(i,j) for i in range(height//square_size)] for j in range(width//square_size)]
        r=[]
        for l in L:
            r+=l
        L=r
        L_bomb=[[0]*n_bomb,[0]*n_bomb]
        L=rd.sample(L,n_bomb)
        
        for i in range(n_bomb):
            L_bomb[0][i]=L[i][0]
            L_bomb[1][i]=L[i][1]
            L[i]=(L[i][1],L[i][0],True)
        for i in range(len(L_bomb[0])):
            for n in box[L_bomb[0][i]][L_bomb[1][i]].neighbor[:-1]:
                if type(box[n[1]][n[0]].neighbor[-1])== int:
                    box[n[1]][n[0]].neighbor[-1]+=1
            box[L_bomb[0][i]][L_bomb[1][i]].neighbor='bomb'
        text = font.render('Votre temps', black, black)
        textRect = text.get_rect()
        textRect.center = (1125, 100)
        text2 = font.render('Nombre de bombes', black, black)
        text2Rect = text2.get_rect()
        text2Rect.center = (1125, 175)
        screen.blit(text,textRect)
        text3= font.render('restantes :' + str(F[0]), black, black)
        text3Rect = text3.get_rect()
        text3Rect.center = (1125, 200)
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if event.key == pygame.K_RETURN:
                        main_game(square_size,n_bomb)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    click=pygame.mouse.get_pressed(num_buttons=3)
                    mouseX = event.pos[0]
                    mouseY = event.pos[1]
                    if mouseX <= 960:
                        col = mouseX // square_size
                        line = mouseY // square_size
                        if click[0]:
                            if box[line][col].clicked(screen,box,finished,square_size):
                                main_over(Time,False,square_size,L)
                        elif click[2]:
                             box[line][col].flag(screen,flag,F,square_size,L)
                        if finished[0]==0:
                            for l in L:
                                 box[l[1]][l[0]].flag(screen,flag,F,square_size)
                            running=False
                                
            Time += 1
            clock.tick(60)
            pygame.draw.rect(screen,white, (960, 0, 1500, height))
            texts = font.render(str(Time//60), black, black)
            textsRect = texts.get_rect()
            textsRect.center = (1125, 125)
            text3= font.render('restantes :' + str(F[0]), black, black)
            text3Rect = text3.get_rect()
            text3Rect.center = (1125, 200)
            screen.blit(texts,textsRect)
            screen.blit(text,textRect)
            screen.blit(text2,text2Rect)
            screen.blit(text3,text3Rect)
            pygame.display.flip()
        main_over(Time,True,square_size)
    bomb='bomb'+str(d)+'.png'
    bomb=pygame.image.load(bomb)
    flag='flag'+str(d)+'.png'
    flag = pygame.image.load(flag)
    n_bomb = int(text)
    main_game(square_size,n_bomb)
                      
if __name__ == "__main__":
    main()