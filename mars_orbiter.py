import os
import math
import random
import pygame as pg
from time import *

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
LT_BLUE = (173, 216, 230)
win = False
timeinit = 0
class Satellite(pg.sprite.Sprite):
    
    def __init__(self, background):
        super().__init__()
        self.background = background
        self.image_sat = pg.image.load("satellite.png").convert()
        self.image_crash = pg.image.load("satellite_crash_40x33.png").convert()
        self.image = self.image_sat
        self.rect = self.image.get_rect()
        self.image.set_colorkey(BLACK)  # sets transparent color
        self.x = random.randrange(315, 425)
        self.y = random.randrange(70, 180) 
        self.vx = random.choice([-3, 3])
        self.vy = 0
        self.heading = 0  # initializes dish orientation
        self.fuel = 100
        self.mass = 1
        self.distance = 0  # initializes distance between satellite & planet
        self.thrust = pg.mixer.Sound('thrust_audio.ogg')
        self.thrust.set_volume(0.07)  # valid values are 0-1

    def thruster(self, vx, vy):
        self.vx += vx
        self.vy += vy
        self.fuel -= 2
        self.thrust.play()     

    def check_keys(self):
        keys = pg.key.get_pressed()       
        # fire thrusters
        if keys[pg.K_RIGHT]:
            self.thruster(vx=0.05, vy=0)
        elif keys[pg.K_LEFT]:
            self.thruster(vx=-0.05, vy=0)
        elif keys[pg.K_UP]:
            self.thruster(vx=0, vy=-0.05)
        elif keys[pg.K_DOWN]:
            self.thruster(vx=0, vy=0.05)
            
    def locate(self, planet):
        px, py = planet.x, planet.y
        dist_x = self.x - px
        dist_y = self.y - py
        # get direction to planet to point dish
        planet_dir_radians = math.atan2(dist_x, dist_y)
        self.heading = planet_dir_radians * 180 / math.pi
        self.heading -= 90  # sprite is traveling tail-first       
        self.distance = math.hypot(dist_x, dist_y)

    def rotate(self):
        self.image = pg.transform.rotate(self.image_sat, self.heading)
        self.rect = self.image.get_rect()

    def path(self):
        last_center = (self.x, self.y)
        self.x += self.vx
        self.y += self.vy
        pg.draw.line(self.background, WHITE, last_center, (int(self.x), int(self.y)))

    def update(self):
        self.check_keys()
        self.rotate()
        self.path()
        self.rect.center = (int(self.x), int(self.y))
        # change image to fiery red if in atmosphere
        if self.vx == 0 and self.vy == 0:
            self.image = self.image_crash
            self.image.set_colorkey(BLACK)
            
class Planet(pg.sprite.Sprite):
    
    def __init__(self):
        super().__init__()
        self.image_mars = pg.image.load("mars1.jpg").convert()
        self.image_water = pg.image.load("mars_water.png").convert() 
        self.image_copy = pg.transform.scale(self.image_mars, (100, 100))
        self.image_copy.set_colorkey(BLACK) 
        self.rect = self.image_copy.get_rect()
        self.image = self.image_copy
        self.mass = 2000 
        self.x = 400 
        self.y = 320
        self.rect.center = (self.x, self.y)
        self.angle = math.degrees(0)
        self.rotate_by = math.degrees(0.01)

    def rotate(self):
        last_center = self.rect.center
        self.image = pg.transform.rotate(self.image_copy, self.angle)
        self.rect = self.image.get_rect()
        self.rect.center = last_center
        self.angle += self.rotate_by

    def gravity(self, satellite):
        G = 1.0  # gravitational constant for game
        dist_x = self.x - satellite.x
        dist_y = self.y - satellite.y
        distance = math.hypot(dist_x, dist_y)     
        # normalize to a unit vector
        dist_x /= distance
        dist_y /= distance
        # apply gravity
        force = G * (satellite.mass * self.mass) / (math.pow(distance, 2))
        satellite.vx += (dist_x * force)
        satellite.vy += (dist_y * force)
        
    def update(self):
        self.rotate()

def calc_eccentricity(dist_list):
    apoapsis = max(dist_list)
    periapsis = min(dist_list)
    eccentricity = (apoapsis - periapsis) / (apoapsis + periapsis)
    return eccentricity

def instruct_label(screen, text, color, x, y):
    instruct_font = pg.font.SysFont(None, 25)
    line_spacing = 22
    for index, line in enumerate(text):
        label = instruct_font.render(line, True, color, BLACK)
        screen.blit(label, (x, y + index * line_spacing))

def help_label(screen, text, color, x, y):
    instruct_font = pg.font.SysFont(None, 27)
    line_spacing = 32
    for index, line in enumerate(text):
        label = instruct_font.render(line, True, color, BLACK)
        screen.blit(label, (x, y + index * line_spacing))

def draw_text(screen, text, size, color, x, y):
    font = pg.font.SysFont(None, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    screen.blit(text_surface, text_rect)

def box_label(screen, text, dimensions):
    readout_font = pg.font.SysFont(None, 27)
    base = pg.Rect(dimensions)
    pg.draw.rect(screen, WHITE, base, 0)
    label = readout_font.render(text, True, BLACK)
    label_rect = label.get_rect(center=base.center)
    screen.blit(label, label_rect)

def warning_label(screen, text, dimensions):
    readout_font = pg.font.SysFont(None, 27)
    base = pg.Rect(dimensions)
    pg.draw.rect(screen, WHITE, base, 0)
    label = readout_font.render(text, True, RED)
    label_rect = label.get_rect(center=base.center)
    screen.blit(label, label_rect)

def mapping_on(planet):
    last_center = planet.rect.center
    planet.image_copy = pg.transform.scale(planet.image_water, (100, 100))
    planet.image_copy.set_colorkey(BLACK)
    planet.rect = planet.image_copy.get_rect()
    planet.rect.center = last_center

def mapping_off(planet):
    planet.image_copy = pg.transform.scale(planet.image_mars, (100, 100))
    planet.image_copy.set_colorkey(BLACK)

def start_screen():
    global screen
    pg.display.set_caption("Mars Orbiter")
    screen.fill(BLACK)
    background = pg.image.load("background.png").convert()
    screen.blit(background, (0, 0))
    draw_text(screen, 'Mars Orbiter Game', 60, WHITE, 400, 470)
    draw_text(screen, 'Created by Aditya Mittal and Aditi Mittal', 25, WHITE, 400, 550)
    draw_text(screen, 'Press H for help regarding how to play', 25, WHITE, 400, 580)
    draw_text(screen, 'Press any other key to play', 25, WHITE, 400, 610)
    image=pg.image.load("mgspatch.jpg").convert()
    image = pg.transform.scale(image, (400, 400))
    screen.blit(image,(200,30))
    pg.display.flip()
    wait_for_key()

def scores_screen():
    global running
    global score
    global screen
    lines = readscores("recentscores.txt", 10)
    pg.display.set_caption("Recent Scores")
    screen.fill(BLACK)
    background = pg.image.load("background.png").convert()
    screen.blit(background, (0, 0))
    draw_text(screen, 'Recent Scores', 50, WHITE, 400, 40)
    for i in range(len(lines)):
        line = lines[len(lines)-i-1]
        try:
            draw_text(screen, 'Score [%d] : '%(i+1)+str(round(float(line), 3)), 32, WHITE, 400, 550-50*(10-i-1))
        except ValueError:
            break
    draw_text(screen, 'Created by Aditya Mittal and Aditi Mittal', 25, WHITE, 400, 610)
    pg.display.flip()
    clock = pg.time.Clock()
    fps = 30
    while not running:
        clock.tick(fps)
        for event in pg.event.get():
            if event.type == pg.QUIT or event.type == pg.KEYDOWN and event.key == pg.K_x:
                running = True
    pg.display.flip()


def wait_for_key():
    global waiting
    global running
    global exit
    clock = pg.time.Clock()
    fps = 30
    waiting = True
    while waiting:
        clock.tick(fps)
        for event in pg.event.get():
            if event.type == pg.QUIT:
                waiting = False
                running = False
            elif event.type == pg.KEYDOWN and event.key == pg.K_h:
                help()
            elif event.type == pg.KEYUP:
                waiting = False
                running = True


def readscores(fname, N):
    assert N >= 0
    pos = N + 1
    lines = []
    try:
        with open(fname, 'x') as f:
            f.write(str(score) + '\n')
    except FileExistsError:
        with open(fname, 'a') as f:
            f.write(str(score) + '\n')
    with open(fname) as f:
        while len(lines) <= N:
            try:
                f.seek(-pos, 2)
            except IOError:
                f.seek(0)
                break
            finally:
                lines = list(f)
            pos *= 2
    return lines[-N:]

def readimgnames(fname, N):
    assert N >= 0
    pos = N + 1
    lines = []
    with open(fname) as f:
        while len(lines) <= N:
            try:
                f.seek(-pos, 2)
            except IOError:
                f.seek(0)
                break
            finally:
                lines = list(f)
            pos *= 2
    return lines[-N:]

def set_display():
    global screen
    pg.init()  # initialize pygame

    # set-up display
    os.environ['SDL_VIDEO_WINDOW_POS'] = '700, 100'  # set game window origin
    screen = pg.display.set_mode((800, 645), pg.FULLSCREEN)

instructtext = [[
        'The apoapsis is the highest point in an elliptical orbit',
        'i.e. The point where the body is farthest from planet',
        'The periapsis similarly is the lowest point in an elliptical orbit',
        'The apoapsis and periapsis are called apogee and perigee',
        'respectively if the body is orbiting Earth.',
        ],
        [
        'CASE 1 - To circularize an orbit by increasing radius of orbit',
        'This maneuver can be used to circularize a highly elliptical orbit',
        'in the case where the satellite is orbiting very closely to the planet.',
        'This is done by performing a prograde thrust at the apoapsis position.',
        'A prograde thrust can be achieved by increasing the velocity of the',
        'satellite in the direction in which it is currently moving.',
        ],
        [
        'CASE 2 - To circularize an orbit by decreasing the radius of orbit',
        'This maneuver is used to circularize a highly elliptical orbit',
        'in the case where the satellite is orbiting far away from the planet.',
        'This is done by performing a retrograde thrust at the periapsis position.',
        'A retrograde thrust can be achieved by decreasing the velocity of the',
        'satellite in the direction in which it is currently moving.',
        ],
        [
            'HOHMANN TRANSFER - To switch between two circular orbits',
            'The Hohmann Transfer is a conjunction of the previous two cases.',
            'To raise the orbit we provide two prograde thrusts at opposite points.',
            'Similarly to lower the orbit we provide two retrograde thrusts.',
            'The points of application of the thrusts can be seen in the figure above.',
        ],
        [
            'SINGLE TANGENT BURN - A faster but less fuel efficient method to switch orbits.',
            'This maneuver requires two impulses, just like the Hohmann Transfer',
            'The first impulse is tangential to the orbit and the second is nontangential.',
            'To lower an orbit the first thrust should be prograde and vice versa.',
            'For an elliptical orbit first thrust should be made at apoapsis and vice versa.',
        ],
        [
            'SPIRAL TRANSFER - It is the fastest and least fuel efficient method to switch orbits.',
            'Unlike the Hohmann Transfer and Single Tangent Burn this method requires continous',
            'low-thrust burns that are short and regularly spaced (see the figure above)',
            'To lower an orbit with spiral transfer method, all thrusts made should be retrograde.',
            'Whereas to raise an orbit all thrusts made should be prograde',
        ]
        ]

def help():
    global screen
    lines = readimgnames("imagenames.txt", 30)
    pg.display.set_caption("Help")
    for i in range(6):
        string = (lines[5*i]).replace('\n', '')
        posx = (lines[5*i+1]).replace('\n', '')
        posy = (lines[5*i+2]).replace('\n', '')
        screen.fill(BLACK)
        background = pg.image.load("background.png").convert()
        screen.blit(background, (0, 0))
        image = pg.image.load(string).convert()
        screen.blit(image, (int(posx), int(posy)))
        help_label(screen, instructtext[i], WHITE, int(lines[5*i+3]), int(lines[5*i+4]))
        pg.display.flip()
        sleep(10)
    wait_for_key()

def main():
    global win
    global fuel
    global distance
    global running
    global tick_count
    global screen
    pg.init()
    pg.display.set_caption("Mars Orbiter")
    background = pg.image.load("background.png").convert()
    space = 0
    checktime = pg.time.get_ticks()
    # enable sound mixer
    pg.mixer.init()

    intro_text = [
        ' The Mars Orbiter experienced an error during Orbit insertion.',
        ' Use thrusters to correct to a circular mapping orbit without',
        ' running out of propellant or burning up in the atmosphere.'
        ]
 
    instruct_text1 = [
        'Orbital altitude must be within 69-120 miles',
        'Orbital Eccentricity must be < 0.05',
        'Avoid top of atmosphere at 68 miles'    
        ]

    instruct_text2 = [
        'Left Arrow = Decrease Vx',
        'Right Arrow = Increase Vx',
        'Up Arrow = Decrease Vy',
        'Down Arrow = Increase Vy',
        'Space Bar = Clear Path',
        'F = Enter Full Screen',
        'X = Terminate the Mission'
        ]  

    # instantiate planet and satellite objects
    planet = Planet()
    planet_sprite = pg.sprite.Group(planet)
    sat = Satellite(background)    
    sat_sprite = pg.sprite.Group(sat)

    # for circular orbit verification
    dist_list = []  
    eccentricity = 1
    eccentricity_calc_interval = 5  # optimized for 120 mile altitude
    
    # time-keeping
    clock = pg.time.Clock()
    fps = 30
    tick_count = 0

    # for soil moisture mapping functionality
    mapping_enabled = False
    while running:
        clock.tick(fps)
        tick_count += 1
        dist_list.append(sat.distance)
        
        # get keyboard input
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_x):
                running = False
            elif event.type == pg.KEYDOWN and event.key == pg.K_f and space%2==1:
                screen = pg.display.set_mode((800, 645), pg.FULLSCREEN)  # enter full screen
                space += 1
            elif event.type == pg.KEYDOWN and event.key == pg.K_f and space%2==0:
                screen = pg.display.set_mode((800, 645))  # exit full screen
                space += 1
            elif event.type == pg.KEYDOWN and event.key == pg.K_h:
                help()
                checktime = pg.time.get_ticks()
            elif event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                background = pg.image.load("background.png").convert()
            elif event.type == pg.KEYUP:
                sat.thrust.stop()
                mapping_off(planet)
            elif mapping_enabled:
                if event.type == pg.KEYDOWN and event.key == pg.K_m:
                    mapping_on(planet)

        # get heading & distance to planet & apply gravity
        sat.locate(planet)  
        planet.gravity(sat)

        # calculate orbital eccentricity
        if tick_count % (eccentricity_calc_interval * fps) == 0:
            eccentricity = calc_eccentricity(dist_list)
            dist_list = []              

        # re-blit background for drawing command - prevents clearing path
        screen.blit(background, (0, 0))
        
        # Fuel/Altitude fail conditions
        if sat.fuel <= 0:
            instruct_label(screen, ['Fuel Depleted!'], RED, 335, 180)
            instruct_label(screen, ['Press X to terminate the mission'], RED, 272, 220)
            sat.fuel = 0
            sat.vx = 2


        elif sat.distance <= 68:
            instruct_label(screen, ['Atmospheric Entry!'], RED, 322, 180)
            instruct_label(screen, ['Press X to terminate the mission'], RED, 272, 220)
            sat.vx = 0
            sat.vy = 0

        if eccentricity < 0.05 and sat.distance >= 69 and sat.distance <= 120:
            map_instruct = ['Press & hold M to map soil moisture']
            instruct_label(screen, map_instruct, LT_BLUE, 250, 175)
            mapping_enabled = True
            if not win:
                timeinit = pg.time.get_ticks()
            win = True
            time = pg.time.get_ticks()
            if time - timeinit > 10000:
                running = False

        else:
            mapping_enabled = False
            win = False
        planet_sprite.update()
        planet_sprite.draw(screen)
        sat_sprite.update()
        sat_sprite.draw(screen)

        # display intro text for 15 seconds
        if pg.time.get_ticks()-checktime <= 15000:  # time in milliseconds
            instruct_label(screen, intro_text, GREEN, 145, 100)

        # display telemetry and instructions
        box_label(screen, 'Vx', (70, 20, 75, 20))
        box_label(screen, 'Vy', (150, 20, 80, 20))
        if sat.distance > 120:
            warning_label(screen, 'Altitude', (240, 20, 160, 20))
        else:
            box_label(screen, 'Altitude', (240, 20, 160, 20))
        if sat.fuel <= 0:
            warning_label(screen, 'Fuel', (410, 20, 160, 20))
        else:
            box_label(screen, 'Fuel', (410, 20, 160, 20))
        if eccentricity > 0.05:
            warning_label(screen, 'Eccentricity', (580, 20, 150, 20))
        else:
            box_label(screen, 'Eccentricity', (580, 20, 150, 20))
        
        box_label(screen, '{:.1f}'.format(sat.vx), (70, 50, 75, 20))
        box_label(screen, '{:.1f}'.format(sat.vy), (150, 50, 80, 20))
        box_label(screen, '{:.1f}'.format(sat.distance), (240, 50, 160, 20))
        box_label(screen, '{}'.format(sat.fuel), (410, 50, 160, 20))
        box_label(screen, '{:.8f}'.format(eccentricity), (580, 50, 150, 20))
          
        instruct_label(screen, instruct_text1, WHITE, 10, 575)
        instruct_label(screen, instruct_text2, WHITE, 570, 480)
      
        # add terminator & border
        pg.draw.rect(screen, WHITE, (1, 1, 798, 643), 1)

        pg.display.flip()
        fuel = sat.fuel
        distance = sat.distance
if __name__ == "__main__":
    set_display()
    start_screen()
    main()
    if win:
        score = (1/tick_count)*10000+distance+fuel
    else:
        score = 0
    scores_screen()
