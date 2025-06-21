import pygame
from random import randint

pygame.init()

W = 600
H = 400
Side=20
Half_Side=Side//2
Yboard=H-Side
Xboard=W-Side
xsb=W/4*3
xsr=W/4
ys=H-50
sc = pygame.display.set_mode((W,H))

WHITE = (255,255,255)
BLUE = (0,255,255)
RED = (139,0,0)
GREEN = (34,139,34)
BLACK = (0,0,0)
SCREEN_COLOR=GREEN
clock= pygame.time.Clock()
FPS = 60


hero = pygame.Surface((Side,Side))
hero.fill(BLUE) 
rect = hero.get_rect(center=(xsb,ys))

hero2 = pygame.Surface((Side,Side))
hero2.fill(BLUE) 
rect2 = hero2.get_rect(center=(xsb,ys))

hero3 = pygame.Surface((Side,Side))
hero3.fill(BLUE) 
rect3 = hero3.get_rect(center=(xsb,ys))


hero4 = pygame.Surface((Side,Side))
hero4.fill(RED) 
rect4 = hero4.get_rect(center=(xsr,ys))

hero5 = pygame.Surface((Side,Side))
hero5.fill(RED) 
rect5 = hero5.get_rect(center=(xsr,ys))

hero6 = pygame.Surface((Side,Side))
hero6.fill(RED) 
rect6 = hero6.get_rect(center=(xsr,ys))


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:                
                SCREEN_COLOR=GREEN
                x,y = randint(Half_Side,Xboard),randint(Half_Side,Yboard)
                x2,y2 = randint(Half_Side,Xboard),randint(Half_Side,Yboard)
                x3,y3 = randint(Half_Side,Xboard),randint(Half_Side,Yboard)
                x4,y4 = randint(Half_Side,Xboard),randint(Half_Side,Yboard)
                x5,y5 = randint(Half_Side,Xboard),randint(Half_Side,Yboard)
                x6,y6 = randint(Half_Side,Xboard),randint(Half_Side,Yboard)
                rect.center=(x,y)
                rect2.center=(x2,y2)
                rect3.center=(x3,y3)
                rect4.center=(x4,y4)
                rect5.center=(x5,y5)
                rect6.center=(x6,y6)
                left_blue=0
                left_red=0
                top_blue=0
                top_red=0
                right_blue=0
                right_red=0
                bottom_blue=0
                bottom_red=0
                if x<W/2:left_blue+=1 
                else: right_blue+=1
                if x2<W/2:left_blue+=1 
                else: right_blue+=1
                if x3<W/2:left_blue+=1 
                else: right_blue+=1
                if y<H/2:top_blue+=1
                else: bottom_blue+=1
                if y2<H/2:top_blue+=1
                else: bottom_blue+=1
                if y3<H/2:top_blue+=1
                else: bottom_blue+=1
                
                if x4<W/2:left_red+=1 
                else: right_red+=1
                if x5<W/2:left_red+=1 
                else: right_red+=1
                if x6<W/2:left_red+=1 
                else: right_red+=1
                if y4<H/2:top_red+=1
                else:bottom_red+=1
                if y5<H/2:top_red+=1
                else:bottom_red+=1
                if y6<H/2:top_red+=1
                else:bottom_red+=1

                

            elif event.key == pygame.K_LEFT and left_blue>left_red:SCREEN_COLOR=BLUE 
            elif event.key == pygame.K_LEFT and left_blue<left_red: SCREEN_COLOR=RED
            elif event.key == pygame.K_LEFT and left_blue==left_red:SCREEN_COLOR=BLACK

            elif event.key == pygame.K_RIGHT and right_blue>right_red:SCREEN_COLOR=BLUE 
            elif event.key == pygame.K_RIGHT and right_blue<right_red: SCREEN_COLOR=RED
            elif event.key == pygame.K_RIGHT and right_blue==right_red:SCREEN_COLOR=BLACK

            elif event.key == pygame.K_UP and top_blue>top_red:SCREEN_COLOR=BLUE 
            elif event.key == pygame.K_UP and top_blue<top_red: SCREEN_COLOR=RED
            elif event.key == pygame.K_UP and top_blue==top_red:SCREEN_COLOR=BLACK

            elif event.key == pygame.K_DOWN and bottom_blue>bottom_red:SCREEN_COLOR=BLUE 
            elif event.key == pygame.K_DOWN and bottom_blue<bottom_red: SCREEN_COLOR=RED
            elif event.key == pygame.K_DOWN and bottom_blue==bottom_red:SCREEN_COLOR=BLACK


    sc.fill(SCREEN_COLOR)
    sc.blit(hero,rect)
    sc.blit(hero2,rect2)
    sc.blit(hero3,rect3)
    sc.blit(hero4,rect4)
    sc.blit(hero5,rect5)
    sc.blit(hero6,rect6)
    pygame.display.update()                        
    clock.tick(3)        
