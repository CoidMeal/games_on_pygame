import pygame
from random import randint
cup=(300,100)
cleft=(150,200)
cbot=(300,300)
cright=(450,200)
class bplayers(pygame.sprite.Sprite):
    left_blue=0
    right_blue=0
    top_blue=0
    bottom_blue=0
    #d = √((x₂ - x₁)² + (y₂ - y₁)²)
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((Side,Side))
        self.image.fill(BLUE_TEAM_COLOR) 
        self.rect = self.image.get_rect(center=(xsb,ys))
    
    
    def update(self, *args):                            
        
        self.x,self.y=rand_pos_x(),rand_pos_y()
        self.rect.center=(self.x,self.y)
        if self.x<W/2:bplayers.left_blue+=(((self.x-cleft[0])**2+(self.y-cleft[1])**2)**0.5)**-1            
        else:bplayers.right_blue+=(((self.x-cright[0])**2+(self.y-cright[1])**2)**0.5)**-1                    
        if self.y<H/2:bplayers.top_blue+=(((self.x-cup[0])**2+(self.y-cup[1])**2)**0.5)**-1           
        else:bplayers.bottom_blue+=(((self.x-cbot[0])**2+(self.y-cbot[1])**2)**0.5)**-1
class rplayers(pygame.sprite.Sprite):
    left_red=0
    right_red=0
    top_red=0
    bottom_red=0
    
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.hero = pygame.Surface((Side,Side))
        self.hero.fill(RED_TEAM_COLOR) 
        self.rect = self.hero.get_rect(center=(xsr,ys))
    
    def update(self, *args):                            
        
        self.x,self.y=rand_pos_x(),rand_pos_y()
        self.rect.center=(self.x,self.y)
        if self.x<W/2:rplayers.left_red+=(((self.x-cleft[0])**2+(self.y-cleft[1])**2)**0.5)**-1            
        else:rplayers.right_red+=(((self.x-cright[0])**2+(self.y-cright[1])**2)**0.5)**-1                    
        if self.y<H/2:rplayers.top_red+=(((self.x-cup[0])**2+(self.y-cup[1])**2)**0.5)**-1           
        else:rplayers.bottom_red+=(((self.x-cbot[0])**2+(self.y-cbot[1])**2)**0.5)**-1
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
BROWN=(168,71,10)
YELLOW=(252,186,3)
DARK_BLUE=(63,57,150)
BLACK = (0,0,0)

BLUE_TEAM_COLOR=BLUE
RED_TEAM_COLOR=RED
STADION_COLOR=GREEN
SCREEN_COLOR=GREEN

clock= pygame.time.Clock()

blue_t=pygame.sprite.Group()
b1=bplayers()
b2=bplayers()
b3=bplayers()
b4=bplayers()
b5=bplayers()
blue_t.add(b1,b2,b3,b4,b5)

r1=rplayers()
r2=rplayers()
r3=rplayers()
r4=rplayers()
r5=rplayers()

def rand_pos_x():
    a=randint(Half_Side,Xboard)
    return a
def rand_pos_y():
    a=randint(Half_Side,Yboard)
    return a
def pisdavsem():
    bplayers.bottom_blue=0
    bplayers.left_blue=0
    bplayers.right_blue=0
    bplayers.top_blue=0
    b1.update()
    b2.update()
    b3.update()
    b4.update()
    b5.update()             
        
    rplayers.bottom_red=0
    rplayers.top_red=0
    rplayers.left_red=0
    rplayers.right_red=0
    r1.update()
    r2.update()
    r3.update()
    r4.update()
    r5.update()
while True:
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()
        elif event.type==pygame.MOUSEBUTTONDOWN:
            print(event.button)
            if event.button==1:
                pass
            elif event.button==3:
                pass
        elif event.type == pygame.KEYDOWN:           
            if event.key == pygame.K_SPACE:                
                
                SCREEN_COLOR=STADION_COLOR
                pisdavsem()
            elif event.key == pygame.K_LEFT and bplayers.left_blue>rplayers.left_red:SCREEN_COLOR=BLUE_TEAM_COLOR 
            elif event.key == pygame.K_LEFT and bplayers.left_blue<rplayers.left_red:SCREEN_COLOR=RED_TEAM_COLOR            
            elif event.key == pygame.K_LEFT and bplayers.left_blue==rplayers.left_red:SCREEN_COLOR=BLACK

            elif event.key == pygame.K_RIGHT and bplayers.right_blue>rplayers.right_red:SCREEN_COLOR=BLUE_TEAM_COLOR 
            elif event.key == pygame.K_RIGHT and bplayers.right_blue<rplayers.right_red: SCREEN_COLOR=RED_TEAM_COLOR
            elif event.key == pygame.K_RIGHT and bplayers.right_blue==rplayers.right_red:SCREEN_COLOR=BLACK

            elif event.key == pygame.K_UP and bplayers.top_blue>rplayers.top_red:SCREEN_COLOR=BLUE_TEAM_COLOR 
            elif event.key == pygame.K_UP and bplayers.top_blue<rplayers.top_red: SCREEN_COLOR=RED_TEAM_COLOR
            elif event.key == pygame.K_UP and bplayers.top_blue==rplayers.top_red:SCREEN_COLOR=BLACK

            elif event.key == pygame.K_DOWN and bplayers.bottom_blue>rplayers.bottom_red:SCREEN_COLOR=BLUE_TEAM_COLOR 
            elif event.key == pygame.K_DOWN and bplayers.bottom_blue<rplayers.bottom_red: SCREEN_COLOR=RED_TEAM_COLOR
            elif event.key == pygame.K_DOWN and bplayers.bottom_blue==rplayers.bottom_red:SCREEN_COLOR=BLACK
            
            elif event.key == pygame.K_1:
                STADION_COLOR=YELLOW
                
                BLUE_TEAM_COLOR=DARK_BLUE
                RED_TEAM_COLOR=BROWN
                del b1,b2,b3,b4,b5
    
                del r1,r2,r3,r4,r5
                b1=bplayers()
                b2=bplayers()
                b3=bplayers()
                b4=bplayers()
                b5=bplayers()
                r1=rplayers()
                r2=rplayers()
                r3=rplayers()
                r4=rplayers()
                r5=rplayers()  
            elif event.key == pygame.K_2:
                STADION_COLOR=WHITE
                BLUE_TEAM_COLOR=DARK_BLUE
                RED_TEAM_COLOR=BROWN
                del b1,b2,b3,b4,b5
    
                del r1,r2,r3,r4,r5
                b1=bplayers()
                b2=bplayers()
                b3=bplayers()
                b4=bplayers()
                b5=bplayers()
                r1=rplayers()
                r2=rplayers()
                r3=rplayers()
                r4=rplayers()
                r5=rplayers()
            elif event.key == pygame.K_3:
                STADION_COLOR=GREEN
                BLUE_TEAM_COLOR=WHITE
                RED_TEAM_COLOR=YELLOW
                del b1,b2,b3,b4,b5
    
                del r1,r2,r3,r4,r5
                b1=bplayers()
                b2=bplayers()
                b3=bplayers()
                b4=bplayers()
                b5=bplayers()
                r1=rplayers()
                r2=rplayers()
                r3=rplayers()
                r4=rplayers()
                r5=rplayers()
            elif event.key == pygame.K_4:
                STADION_COLOR=GREEN
                BLUE_TEAM_COLOR=BLUE
                RED_TEAM_COLOR=RED
                del b1,b2,b3,b4,b5
    
                del r1,r2,r3,r4,r5
                b1=bplayers()
                b2=bplayers()
                b3=bplayers()
                b4=bplayers()
                b5=bplayers()
                r1=rplayers()
                r2=rplayers()
                r3=rplayers()
                r4=rplayers()
                r5=rplayers()
            elif event.key == pygame.K_5:
                print(bplayers.left_blue,bplayers.top_blue,bplayers.right_blue,bplayers.bottom_blue)
                print(rplayers.left_red,rplayers.top_red,rplayers.right_red,rplayers.bottom_red)
            elif event.key == pygame.K_6:SCREEN_COLOR=(100,100,100)
    sc.fill(SCREEN_COLOR)    
    blue_t.draw(sc)

    sc.blit(r1.hero,r1.rect)
    sc.blit(r2.hero,r2.rect)
    sc.blit(r3.hero,r3.rect)
    sc.blit(r4.hero,r4.rect)
    sc.blit(r5.hero,r5.rect)
    
    pygame.display.update()                        
    clock.tick(2)        