import pygame
import sys
import time
import random
import JEUX

# Fonction principale du jeu
def main():
    BLACK = (0, 0, 0)
    GRAY = (150,150,150)
    WHITE = (255,255,255)
    RED = (255, 0, 0)
    YELLOW = (255, 255, 0)
    BLUE = (63,72,204)
    ROWS = 6
    COLS = 7
    SQUARE_SIZE = 100
    WIDTH = (COLS+5) * SQUARE_SIZE
    HEIGHT = ROWS * SQUARE_SIZE
    screen = pygame.display.set_mode((WIDTH,HEIGHT))
    pion=pygame.image.load('pion_py.png').convert()
    pygame.display.set_icon(pion)
    pygame.display.set_caption('Puissance 4',)
    pygame.init()
    clock = pygame.time.Clock()
    fps = 60
    bg = [255, 255, 255]
    screen.fill(bg)
    def draw_board(board):
        for row in range(ROWS):
            for col in range(COLS):
                pygame.draw.rect(screen, BLUE, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
                if board[row][col] == 0:
                    pygame.draw.circle(screen, WHITE, (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2), SQUARE_SIZE // 2 - 5)
                elif board[row][col] == 1:
                    pygame.draw.circle(screen, RED, (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2), SQUARE_SIZE // 2 - 5)
                elif board[row][col] == 2:
                    pygame.draw.circle(screen, YELLOW, (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2), SQUARE_SIZE // 2 - 5)
    board = [[0] * COLS for _ in range(ROWS)]
    draw_board(board)
    pygame.display.update()

    font = pygame.font.Font('freesansbold.ttf', 32)
    text = font.render(' Voulez-vous jouer', BLACK, BLACK)
    textRect = text.get_rect()
    textRect.center = (950, 200)
    text1 = font.render('en solo ou en duo ?', BLACK, BLACK)
    text1Rect = text.get_rect()
    text1Rect.center = (950, 250)
    solobutton = font.render('SOLO',BLACK,True,GRAY)
    soloRect=solobutton.get_rect()
    soloRect.center = (850 , 400)
    duobutton = font.render('DUO',BLACK,True,GRAY)
    duoRect=duobutton.get_rect()
    duoRect.center = (1050 , 400)

    bot='bot'
    run=True
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

                if soloRect.collidepoint(mouse_pos):           
                    bot = True
                    run = False
                if duoRect.collidepoint(mouse_pos):
                    bot = False
                    run=False

        screen.blit(text, textRect)
        screen.blit(text1, text1Rect)
        screen.blit(solobutton,soloRect)
        screen.blit(duobutton,duoRect)
        pygame.display.update()
        clock.tick(fps)
    screen.fill(bg)
    draw_board(board)
    pygame.display.update()

    screen.fill(bg)
    turn = random.randint(1,2)

    #Fonction de création du dictionnaire des alignements possibles
    def dico(n,m):       
        l=[[(0,0,0),(0,1,0),(0,2,0),(0,3,0),(0,4,0),(0,5,0),(0,6,0)],[(1,0,0),(1,1,0),(1,2,0),(1,3,0),(1,4,0),(1,5,0),(1,6,0)],[(2,0,0),(2,1,0),(2,2,0),(2,3,0),(2,4,0),(2,5,0),(2,6,0)],[(3,0,0),(3,1,0),(3,2,0),(3,3,0),(3,4,0),(3,5,0),(3,6,0)],[(4,0,0),(4,1,0),(4,2,0),(4,3,0),(4,4,0),(4,5,0),(4,6,0)],[(5,0,0),(5,1,0),(5,2,0),(5,3,0),(5,4,0),(5,5,0),(5,6,0)]]
        c=[[(0,0,0),(1,0,0),(2,0,0),(3,0,0),(4,0,0),(5,0,0)],[(0,1,0),(1,1,0),(2,1,0),(3,1,0),(4,1,0),(5,1,0)],[(0,2,0),(1,2,0),(2,2,0),(3,2,0),(4,2,0),(5,2,0)],[(0,3,0),(1,3,0),(2,3,0),(3,3,0),(4,3,0),(5,3,0)],[(0,4,0),(1,4,0),(2,4,0),(3,4,0),(4,4,0),(5,4,0)],[(0,5,0),(1,5,0),(2,5,0),(3,5,0),(4,5,0),(5,5,0)],[(0,6,0),(1,6,0),(2,6,0),(3,6,0),(4,6,0),(5,6,0)]]
        d=[[(2,0,0),(3,1,0),(4,2,0),(5,3,0)],[(1,0,0),(2,1,0),(3,2,0),(4,3,0),(5,4,0)],[(0,0,0),(1,1,0),(2,2,0),(3,3,0),(4,4,0),(5,5,0)],[(0,3,0),(1,2,0),(2,1,0),(3,0,0)],[(0,4,0),(1,3,0),(2,2,0),(3,1,0),(4,0,0)],[(0,5,0),(1,4,0),(2,3,0),(3,2,0),(4,1,0),(5,0,0)],[(0,6,0),(1,5,0),(2,4,0),(3,3,0),(4,2,0),(5,1,0)],[(1,6,0),(2,5,0),(3,4,0),(4,3,0),(5,2,0)],[(2,6,0),(3,5,0),(4,4,0),(5,3,0)],[(0,1,0),(1,2,0),(2,3,0),(3,4,0),(4,5,0),(5,6,0)],[(0,2,0),(1,3,0),(2,4,0),(3,5,0),(4,6,0)],[(0,3,0),(1,4,0),(2,5,0),(3,6,0)]]
        D,s={},0
        for i in range(n):
            for j in range(m):
                s=i+j
                D[(i,j)]=[l[i],c[j]]
                if s>2 and s<9:
                    D[(i,j)].append(d[i+j])
                if i == j:
                    D[(i,j)].append(d[2])
                elif s%2==0:
                    if i>j:
                        D[(i,j)].append(d[0])
                    else:
                        D[(i,j)].append(d[10])
                elif i>j:
                    D[(i,j)].append(d[1])
        D[(0,3)].append(d[11])
        D[(1,4)].append(d[11])
        D[(2,5)].append(d[11])
        D[(3,6)].append(d[11])
        D[(0,1)].append(d[9])
        D[(1,2)].append(d[9])
        D[(2,3)].append(d[9])
        D[(3,4)].append(d[9])
        D[(4,5)].append(d[9])
        D[(5,6)].append(d[9])
        return D  
    def verif4(L,color): #Vérifie s'il y a puissance 4
        s=0
        for x in L:
            if x[2]==color:
                s+=1
            else:
                s=0
            if s==4:
                return True
        return False            
    def verif3(L,color):
        s=0
        for x in L:
            if x[2]==color:
                s+=1
            else:
                s=0
            if s==3:
                return True
        return False   
    def changement_note(row,col,note,valeur):
        note[row][col]='plein'
        v=[[row-1,col-1],[row,col-1],[row+1,col-1],[row-1,col],[row+1,col+1],[row,col+1],[row-1,col+1]]
        for i in range(7):
            if row == 0:
                if v[i][0] == row-1 :
                    v[i] =['non','non']
            elif row == 5:
                if v[i][0] == row+1 :
                    v[i]=['non','non']
            if col == 0:
                if v[i][1] == col-1 :
                    v[i]=['non','non']
            elif col == 6:
                if v[i][1] == col+1 :
                    v[i] =['non','non']
            if v[i]!=['non','non'] and note[v[i][0]][v[i][1]]!='plein':
                note[v[i][0]][v[i][1]]+=valeur
        return note       
    #Fonction renvoyant le tableau avec une pièce en plus et s'il y a un puissance 4
    def placer(color,D,row,col,dispo):
        if (row,col)==('x','y'):
            return False
        for i in range(len(D[(row,col)])):
            for j in range(len(D[(row,col)][i])):
                if D[(row,col)][i][j]==(row,col,0):
                    D[(row,col)][i][j]=(row,col,color)
            if verif4(D[(row,col)][i],color):
                return True
        if row==0:
            dispo[col]="plein"
    def placer_bot(color,color_bot,D,row,col,dispo,note):
        if (row,col)==('x','y'):
            return False
        if color == color_bot:
            changement_note(row,col,note,2)
        else:
            changement_note(row,col,note,1)
        for i in range(len(D[(row,col)])):
            for j in range(len(D[(row,col)][i])):
                if D[(row,col)][i][j]==(row,col,0):
                    D[(row,col)][i][j]=(row,col,color)
            if verif4(D[(row,col)][i],color):
                return True
        dispo[col]-=1
        if row==0:
            dispo[col]="plein"           
    def placer_virtuel(color,color1,d,row,col,note):
        if (row,col)==('x','y'):
            return False
        if color == color1:
            for i in range(len(d[(row,col)])):
                for j in range(len(d[(row,col)][i])):
                    if d[(row,col)][i][j]==(row,col,0):
                        d[(row,col)][i][j]=(row,col,color)
                        if verif4(d[(row,col)][i],color):
                            return True
                        if verif3(d[(row,col)][i],color):
                            note[row][col]=200
        else:
            for i in range(len(d[(row,col)])):
                for j in range(len(d[(row,col)][i])):
                    if d[(row,col)][i][j]==(row,col,color1):
                        d[(row,col)][i][j]=(row,col,color)
                        if verif4(d[(row,col)][i],color):
                            return True
                    if d[(row,col)][i][j]==(row,col,0):
                        d[(row,col)][i][j]=(row,col,color)
                        if verif4(d[(row,col)][i],color):
                            return True
        return False
    def copydico(d):
        c={}
        for j in d:
            c[j]=[]
            for k in d[j]:
                c[j].append(k.copy())
        return c 
    def bestnote(rate):
        L=[]
        n = len(rate)
        m = max(rate)
        for i in range(n):
            if rate[i] == m:
                L.append(i)
        j = random.randint(0,len(L)-1)
        return L[j] 
    
    def rating(couleur,D,dispo,note):
        couleur_adv = "jaunes"
        if couleur == couleur_adv:
            couleur_adv = "rouges"
        n=len(dispo)
        rate=[0]*n
        for col in range(n):  
            dis=dispo.copy()
            row=dis[col]
            if row == 'plein':
                rate[col]=-1000
                continue
            else:
                rate[col]=note[row][col] 
            d=copydico(D)
            if placer_virtuel(couleur,couleur,d,row,col,note):
                return col
            if placer_virtuel(couleur_adv,couleur,d,row,col,note):
                rate[col]=1000
            if dis[col]!=0:
                if placer_virtuel(couleur_adv,couleur,d,row-1,col,note):
                    rate[col]=-500
        return bestnote(rate)

    def main3(resultat,board,vainqueur):
        bg = [255, 255, 255]
        font = pygame.font.Font('freesansbold.ttf', 32)
        if resultat == 0:
            text = font.render('Égalité !', BLACK,True,GRAY)
            textRect = text.get_rect()
            revenge = font.render('.', WHITE,WHITE)
        else:
            revenge = font.render('Revanche !', BLACK,True,GRAY)
        if resultat == 1:  
            if vainqueur[resultat] == 'x rouges':
                text = font.render('Les rouges ont gagné !', BLACK,True,RED)
            else:
                text = font.render(vainqueur[resultat]+' a gagné !', BLACK,True,RED)
            textRect = text.get_rect()
        if resultat == 2:
            if vainqueur[resultat] == 'x jaunes':
                text = font.render('Les jaunes ont gagné !', BLACK,True,YELLOW)
            else:
                text = font.render(vainqueur[resultat]+' a gagné !', BLACK,True,YELLOW)
            textRect = text.get_rect()
        if resultat == 3:
            text = font.render('Vous avez gagné !', BLACK,True,GRAY)
            textRect = text.get_rect()
        if resultat == 4:
            text = font.render('Vous avez perdu...', BLACK,True,GRAY)
            textRect = text.get_rect()
        textRect.center = (950,200)
        text2 = font.render("Voulez-vous rejouer ?", BLACK, BLACK)
        textRect2 = text2.get_rect()
        textRect2.center = (950,250)
        yesbutton = font.render('OUI',BLACK,True,GRAY)
        yesRect=yesbutton.get_rect()
        yesRect.center = (900,400)
        nobutton = font.render('NON',BLACK,True,GRAY)
        noRect=nobutton.get_rect()
        noRect.center = (1000,400)
        
        revengeRect = revenge.get_rect()
        revengeRect.center = (950,450)
        
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
    
                    if yesRect.collidepoint(mouse_pos): 
                        if resultat == 1:
                            if vainqueur[resultat] == "x rouges":
                                main2(random.randint(1,2),"au"+vainqueur[1],"au"+vainqueur[2],[[0] * COLS for _ in range(ROWS)])
                            else:
                                main2(random.randint(1,2),"à "+vainqueur[1],"à "+vainqueur[2],[[0] * COLS for _ in range(ROWS)])                            
                        if resultat == 2:
                            if vainqueur[resultat] == "x jaunes":
                                main2(random.randint(1,2),"au"+vainqueur[1],"au"+vainqueur[2],[[0] * COLS for _ in range(ROWS)])
                            else:
                                main2(random.randint(1,2),"à "+vainqueur[1],"à "+vainqueur[2],[[0] * COLS for _ in range(ROWS)])
                        run = False
                    if noRect.collidepoint(mouse_pos):
                        JEUX.main()   
                    if revengeRect.collidepoint(mouse_pos) :
                        if resultat == 1:
                            if vainqueur[resultat] == "x rouges":
                                main2(2,"au"+vainqueur[1],"au"+vainqueur[2],[[0] * COLS for _ in range(ROWS)])
                            else:
                                main2(2,"à "+vainqueur[1],"à "+vainqueur[2],[[0] * COLS for _ in range(ROWS)])                            
                        if resultat == 2:
                            if vainqueur[resultat] == "x jaunes":
                                main2(1,"au"+vainqueur[1],"au"+vainqueur[2],[[0] * COLS for _ in range(ROWS)])
                            else:
                                main2(1,"à "+vainqueur[1],"à "+vainqueur[2],[[0] * COLS for _ in range(ROWS)])
                        main_bot2(vainqueur[0],vainqueur[1],[[0] * COLS for _ in range(ROWS)])
            screen.fill(bg)
            screen.blit(text, textRect)
            screen.blit(text2, textRect2)
            screen.blit(yesbutton,yesRect)
            screen.blit(nobutton,noRect)
            draw_board(board)
            screen.blit(revenge,revengeRect)
            pygame.display.update()
    
        if vainqueur[0]==0:
            main2(random.randint(1,2),vainqueur[1],vainqueur[2],[[0] * COLS for _ in range(ROWS)])
        else:
            main_bot2(random.randint(1,2),vainqueur[1],[[0] * COLS for _ in range(ROWS)])
    def main1(turn):
        input_box = pygame.Rect(100, 100, 140, 36)
        input_box1 = pygame.Rect(100, 200, 140, 36)
        text3 = font.render('Choisissez vos couleurs', BLACK, BLACK)
        textRect3 = text3.get_rect()
        textRect3.center = (950, 200)
        text4 = font.render('Les jaunes', BLACK ,True,YELLOW)
        textRect4 = text4.get_rect()
        textRect4.center = (825, 300)
        text5 = font.render('Les rouges', BLACK ,True,RED)
        textRect5 = text5.get_rect()
        textRect5.center = (1075, 300)
        text6 = font.render('Confirmer', BLACK, True,GRAY)
        textRect6 = text6.get_rect()
        textRect6.center = (950, 500)
        text7 = font.render('Passer', BLACK, True,GRAY)
        textRect7 = text7.get_rect()
        textRect7.center = (950, 100)
        color_inactive = pygame.Color('gray')
        color_active = pygame.Color('black')
        color1 = color_inactive
        color2 = color_inactive
        active = False
        text = ''
        text1 = ''
        active1 = False
        done = False
    
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # If the user clicked on the input_box rect.
                    if input_box.collidepoint(event.pos):
                        # Toggle the active variable.
                        active = not active
                    else:
                        active = False
                    if input_box1.collidepoint(event.pos):
                        # Toggle the active variable.
                        active1 = not active1
                    else:
                        active1 = False
                    if textRect7.collidepoint(event.pos):
                        text = 'aux jaunes'
                        text1 = 'aux rouges'
                        done = True
                    if textRect6.collidepoint(event.pos): 
                        text= 'à '+text
                        text1= 'à '+text1
                        done = True
                    # Change the current color of the input box.
                    color1 = color_active if active else color_inactive
                    color2 = color_active if active1 else color_inactive
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if active:
                        if event.key == pygame.K_RETURN:
                            print(text)
                        elif event.key == pygame.K_BACKSPACE:
                            text = text[:-1]
                        else:
                            text += event.unicode
                    if active1:
                        if event.key == pygame.K_RETURN:
                            print(text1)
                        elif event.key == pygame.K_BACKSPACE:
                            text1 = text1[:-1]
                        else:
                            text1 += event.unicode
    
            screen.fill((255,255,255))
            # Render the current text.
            txt_surface = font.render(text, True, color1)
            txt_surface1 = font.render(text1, True, color2)
            # Resize the box if the text is too long.
            width = max(200, txt_surface.get_width()+10)
            input_box.w = width
            input_box1.w = width
            input_box.center=(825,400)
            input_box1.center=(1075,400)
            # Blit the text.
            screen.blit(txt_surface, (input_box.x+5, input_box.y+5))
            screen.blit(txt_surface1, (input_box1.x+5, input_box1.y+5))
            screen.blit(text3, textRect3)
            screen.blit(text4, textRect4)
            screen.blit(text5, textRect5)
            screen.blit(text6, textRect6)
            screen.blit(text7, textRect7)
            # Blit the input_box rect.
            pygame.draw.rect(screen, color1, input_box, 2)
            pygame.draw.rect(screen, color2, input_box1, 2)
    
            draw_board(board)
            pygame.display.update()
        main2(turn,text1,text,board)
    def main2(turn,jaune,rouge,board):
        color = ['blancs','jaunes','rouges']
        Joueur=[0,jaune,rouge]
        D=dico(ROWS,COLS)
        if turn == 2:
            text = font.render("C'est "+Joueur[turn], BLACK, True,YELLOW)
            text1 = font.render('de jouer !', BLACK,True,YELLOW)
        else:
            text = font.render("C'est "+Joueur[turn], BLACK, True,RED)
            text1 = font.render('de jouer !', BLACK,True,RED)
        textRect = text.get_rect()
        textRect.center = (950, 300)
        text1Rect = text.get_rect()
        text1Rect.center = (950+len(Joueur[turn])*2, 350)
        dispo=[5]*COLS
        D=dico(ROWS,COLS)
        r,c='x','y'
        while dispo !=["plein","plein","plein","plein","plein","plein","plein"]:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouseX = event.pos[0]
                    if mouseX <= 700:
                        col = mouseX // SQUARE_SIZE
                        for row in range(ROWS - 1, -1, -1):
                            if board[row][col] == 0:
                                board[row][col] = turn
                                r,c=row,col
                                if turn == 1:
                                    turn = 2
                                    screen.fill([255,255,255])
                                    text = font.render("C'est "+Joueur[turn], BLACK, True,YELLOW)
                                    text1 = font.render('de jouer !', BLACK,True,YELLOW)
                                    text1Rect.center = (950+len(Joueur[turn]), 350)
                                    break
                                else:
                                    turn = 1
                                    text = font.render("C'est "+Joueur[turn], BLACK, True,RED)
                                    text1 = font.render('de jouer !', BLACK,True,RED)
                                    text1Rect.center = (950+len(Joueur[turn]), 350)
                                    break
              
            screen.fill((255,255,255))
            screen.blit(text, textRect)
            screen.blit(text1, text1Rect)
            draw_board(board)
            pygame.display.update()
            if placer(color[turn],D,r,c,dispo):
                Joueur = [0,Joueur[1][2:],Joueur[2][2:]]
                main3(abs(turn**2-3),board,Joueur)
        main3(0,board,Joueur)
    def main_bot(turn):        
        color = ['blancs','jaunes','rouges']
        text = font.render(' Voulez-vous jouer', BLACK, BLACK)
        textRect = text.get_rect()
        textRect.center = (950, 200)
        text1 = font.render('les rouges ou les jaunes ?', BLACK, BLACK)
        text1Rect = text.get_rect()
        text1Rect.center = (900, 250)
        redbutton = font.render('Les rouges',BLACK,True,RED)
        redRect=redbutton.get_rect()
        redRect.center = (850 , 400)
        yebutton = font.render('Les jaunes',BLACK,True,YELLOW)
        yeRect=yebutton.get_rect()
        yeRect.center = (1050 , 400)
        run = True
        color_bot = 0
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
                    mouse_pos = event.pos # gets mouse position                
                    # checks if mouse position is over the button 
                    if redRect.collidepoint(mouse_pos):           
                        color_bot = 2
                        run = False
                    if yeRect.collidepoint(mouse_pos):
                        color_bot = 1
                        run=False
    
            screen.blit(text, textRect)
            screen.blit(text1, text1Rect)
            screen.blit(redbutton,redRect)
            screen.blit(yebutton,yeRect)
            draw_board(board)
            pygame.display.update()
            clock.tick(fps)
        main_bot2(random.randint(1, 2),color_bot,board)
    def main_bot2(turn,color_bot,board):
        note=[[3,4,5,7,5,4,3],
          [4,6,7,10,7,6,4],
          [5,7,10,12,10,7,5],
          [5,7,10,12,10,7,5],
          [4,6,7,10,7,6,4],
          [3,4,12,14,12,4,3]]
        color = ['blancs','jaunes','rouges']  
        indice_adv = color_bot
        color_adv=color[indice_adv]
        indice_bot=abs(indice_adv**2-3)
        color_bot=color[indice_bot]
        r,c='x','y'
        text = font.render("C'est aux "+color_adv, BLACK, BLACK)
        textRect = text.get_rect()
        textRect.center = (950, 300)
        text1 = font.render('           de jouer !', BLACK, BLACK)
        text1Rect = text.get_rect()
        text1Rect.center = (900, 350)
        dispo=[5]*COLS
        D=dico(ROWS,COLS)
        if turn == indice_bot:
            board[5][3]  = indice_adv      
            placer_bot(color_bot,color_bot,D,5,3,dispo,note)
            draw_board(board)
            pygame.display.update()
        
        while dispo !=["plein","plein","plein","plein","plein","plein","plein"]:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouseX = event.pos[0]
                    if mouseX <= 700:
                        col = mouseX // SQUARE_SIZE
                        for row in range(ROWS - 1, -1, -1):
                            if board[row][col] == 0:
                                board[row][col] = indice_bot
                                r,c=row,col
                                draw_board(board)
                                pygame.display.update()
                                if placer_bot(color_adv,color_bot,D,r,c,dispo,note):
                                    main3(3,board,[indice_bot,indice_adv]) 
                                if dispo ==["plein","plein","plein","plein","plein","plein","plein"]:
                                    break
                                c=rating(color_bot,D,dispo,note)
                                r=dispo[c]
                                time.sleep(0.5)
                                board[r][c] = indice_adv
                                draw_board(board)
                                pygame.display.update()
                                if placer_bot(color_bot,color_bot,D,r,c,dispo,note):
                                    main3(4,board,[indice_adv,indice_adv])
                                break
            screen.fill([255,255,255])
            if color_adv == "rouges":
                text = font.render("C'est à vous ", BLACK, True,RED)
            if color_adv == "jaunes":
                text = font.render("C'est à vous ", BLACK, True,YELLOW)
            textRect = text.get_rect()
            textRect.center = (950, 300)
                            
            screen.blit(text, textRect)
            screen.blit(text1, text1Rect)
            draw_board(board)
            pygame.display.update()
        main3(0,board,[1,indice_adv])
    if bot:
        main_bot(turn)
    else:
        main1(turn)
     
# Exécution du jeu
if __name__ == "__main__":
    main()