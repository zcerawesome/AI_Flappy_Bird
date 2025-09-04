import pygame, random, time
from pygame.locals import *
import math

import cupy as cp
import python_network as nk

#VARIABLES
SCREEN_WIDHT = 400
SCREEN_HEIGHT = 600
SPEED = 20
GRAVITY = 2.5
GAME_SPEED = 15

GROUND_WIDHT = 2 * SCREEN_WIDHT
GROUND_HEIGHT= 100

PIPE_WIDHT = 80
PIPE_HEIGHT = 500

PIPE_GAP = 150
BIRD_GAP = 126

wing = 'assets/audio/wing.wav'
hit = 'assets/audio/hit.wav'

pygame.mixer.init()


class Bird(pygame.sprite.Sprite):

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

        self.images =  [pygame.image.load('assets/sprites/bluebird-upflap.png').convert_alpha(),
                        pygame.image.load('assets/sprites/bluebird-midflap.png').convert_alpha(),
                        pygame.image.load('assets/sprites/bluebird-downflap.png').convert_alpha()]

        self.speed = SPEED

        self.current_image = 0
        self.image = pygame.image.load('assets/sprites/bluebird-upflap.png').convert_alpha()
        self.mask = pygame.mask.from_surface(self.image)

        self.rect = self.image.get_rect()
        self.rect[0] = SCREEN_WIDHT / 6
        self.rect[1] = SCREEN_HEIGHT / 2

    def update(self):
        self.current_image = (self.current_image + 1) % 3
        self.image = self.images[self.current_image]
        self.speed += GRAVITY

        #UPDATE HEIGHT
        self.rect[1] += self.speed

    def bump(self):
        self.speed = -SPEED

    def begin(self):
        self.current_image = (self.current_image + 1) % 3
        self.image = self.images[self.current_image]




class Pipe(pygame.sprite.Sprite):

    def __init__(self, inverted, xpos, ysize):
        pygame.sprite.Sprite.__init__(self)

        self. image = pygame.image.load('assets/sprites/pipe-green.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (PIPE_WIDHT, PIPE_HEIGHT))


        self.rect = self.image.get_rect()
        self.rect[0] = xpos

        if inverted:
            self.image = pygame.transform.flip(self.image, False, True)
            self.rect[1] = - (self.rect[3] - ysize)
        else:
            self.rect[1] = SCREEN_HEIGHT - ysize

        self.ysize = ysize
        self.mask = pygame.mask.from_surface(self.image)


    def update(self):
        self.rect[0] -= GAME_SPEED

        

class Ground(pygame.sprite.Sprite):
    
    def __init__(self, xpos):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('assets/sprites/base.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (GROUND_WIDHT, GROUND_HEIGHT))

        self.mask = pygame.mask.from_surface(self.image)

        self.rect = self.image.get_rect()
        self.rect[0] = xpos
        self.rect[1] = SCREEN_HEIGHT - GROUND_HEIGHT
    def update(self):
        self.rect[0] -= GAME_SPEED

def is_off_screen(sprite):
    return sprite.rect[0] < -(sprite.rect[2])

def get_random_pipes(xpos):
    size = random.randint(100, 300)
    pipe = Pipe(False, xpos, size)
    pipe_inverted = Pipe(True, xpos, SCREEN_HEIGHT - size - PIPE_GAP)
    return pipe, pipe_inverted

screen = None

def init_screen():
    global screen
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDHT, SCREEN_HEIGHT))
    pygame.display.set_caption('Flappy Bird')

def start(auto_script:nk.Network, training=True):
    Episode = 0
    total_episode = int(input("Enter total episodes to go: "))
    while Episode < total_episode:
        print(Episode)
        Episode += 1
        BACKGROUND = pygame.image.load('assets/sprites/background-day.png')
        BACKGROUND = pygame.transform.scale(BACKGROUND, (SCREEN_WIDHT, SCREEN_HEIGHT))
        BEGIN_IMAGE = pygame.image.load('assets/sprites/message.png').convert_alpha()

        bird_group = pygame.sprite.Group()
        bird = Bird()
        bird_group.add(bird)

        ground_group = pygame.sprite.Group()

        for i in range (2):
            ground = Ground(GROUND_WIDHT * i)
            ground_group.add(ground)

        pipe_group = pygame.sprite.Group()
        for i in range (2):
            pipes = get_random_pipes(SCREEN_WIDHT * i + 400)
            pipe_group.add(pipes[0])
            pipe_group.add(pipes[1])


        clock = pygame.time.Clock()


        def main_menu():
                #     Reward_list[-1] = -150
            begin = True 
            while begin:

                clock.tick(15)

                for event in pygame.event.get():
                    if event.type == QUIT:
                        pygame.quit()
                    if event.type == KEYDOWN:
                        if event.key == K_SPACE or event.key == K_UP:
                            bird.bump()
                            begin = False

                screen.blit(BACKGROUND, (0, 0))
                screen.blit(BEGIN_IMAGE, (120, 150))

                if is_off_screen(ground_group.sprites()[0]):
                    ground_group.remove(ground_group.sprites()[0])

                    new_ground = Ground(GROUND_WIDHT - 20)
                    ground_group.add(new_ground)

                bird.begin()
                ground_group.update()

                bird_group.draw(screen)
                ground_group.draw(screen)

                pygame.display.update()

        def run_game():
            X_list = []
            Y_list = []
            Reward_list = []
            Reward_multiplier = 0.99
            while True:
                clock.tick(20)
                pipes = pipe_group.sprites()
                pipe_gap_y = (pipes[0].rect[1] - BIRD_GAP /2 - PIPE_GAP + BIRD_GAP)
                parameters = cp.array([bird.rect[1] / SCREEN_HEIGHT, -bird.speed/ SCREEN_WIDHT, (pipes[0].rect[0] - bird.rect[0])/ SCREEN_WIDHT, (pipe_gap_y - bird.rect[1])/ SCREEN_HEIGHT]).reshape(-1,1)
                X_list.append(parameters)
                data = auto_script.forward(parameters)
                if training:
                    Y_list.append(int(data[-1][0][0] > 0.5))
                    if Y_list[-1] == 1:
                        bird.bump()
                for event in pygame.event.get():
                    if event.type == QUIT:
                        pygame.quit()
                    if event.type == KEYDOWN:
                        if event.key == K_ESCAPE:
                            exit(0)
                        if event.key == K_SPACE or event.key == K_UP:
                            bird.bump()
                # bird.rect[1] = pipe_gap_y
                screen.blit(BACKGROUND, (0, 0))
                
                if is_off_screen(ground_group.sprites()[0]):
                    ground_group.remove(ground_group.sprites()[0])

                    new_ground = Ground(GROUND_WIDHT - 20)
                    ground_group.add(new_ground)

                appended = False
                if is_off_screen(pipe_group.sprites()[0]):
                    pipe_group.remove(pipe_group.sprites()[0])
                    pipe_group.remove(pipe_group.sprites()[0])

                    pipes = get_random_pipes(SCREEN_WIDHT * 2)

                    pipe_group.add(pipes[0])
                    pipe_group.add(pipes[1])
                    if training:
                        Reward_list.append(10.0)
                        appended = True

                bird_group.update()
                ground_group.update()
                pipe_group.update()

                bird_group.draw(screen)
                pipe_group.draw(screen)
                ground_group.draw(screen)

                pygame.display.update()

                if (pygame.sprite.groupcollide(bird_group, ground_group, False, False, pygame.sprite.collide_mask) or
                        pygame.sprite.groupcollide(bird_group, pipe_group, False, False, pygame.sprite.collide_mask)) or bird.rect[1] < 10:
                    # time.sleep(1)
                    if training:
                        Reward_list.append(-100.0)
                    break
                elif not appended and training:
                    Reward_list.append(0.99)
                if training:
                    dis = abs(pipe_gap_y - bird.rect[1]) / SCREEN_HEIGHT
                    if dis != 0:
                        Reward_list[-1] /= dis
                    if dis > 0.1:
                        Reward_list[-1] *= -dis * dis * SCREEN_HEIGHT
                    if Reward_list[-1] < -100.0:
                        Reward_list[-1] = -100.0 - dis * SCREEN_HEIGHT
                    Reward_list[-1] *= Reward_multiplier
                    Reward_multiplier *= 0.99
                # print(Reward_list[-1])
                # print(dis)
            if training:
                X_list = cp.array(X_list).T[0]
                Y_list = cp.array(Y_list).reshape(1, -1)
                Reward_list = cp.array(Reward_list).reshape(1, -1)
                forward = auto_script.forward(X_list)
                back_prop = auto_script.backward_prop_policy(forward, X_list, Y_list, Reward_list)
                auto_script.update_params(back_prop, 0.01)
            return
        run_game()
    continuing = input("Do you want to continue? (Y/n) ")
    if continuing == 'y' or continuing == 'Y':
        start(auto_script)
        return
    save_model = input('Save model? (Y/n)')
    if(save_model != 'n'):
        auto_script.save_model('model.pkl')
    return

if __name__ == "__main__":
    auto_script = nk.Network()
    auto_script.add_layer(4, 0, 0)
    auto_script.add_layer(16, nk.ReLu, nk.ReLu_derive)
    auto_script.add_layer(8, nk.ReLu, nk.ReLu_derive)
    auto_script.add_layer(1, nk.sigmoid, 0)

    auto_script.apply_randomization(1, nk.uniform_rand, -1.22, 1.22)
    auto_script.apply_randomization(2, nk.uniform_rand, -0.61, 0.61)
    limit = cp.sqrt(6 / (8 + 1))
    auto_script.apply_randomization(3, nk.uniform_rand, -limit, limit)
    # nk.test()
    random.seed(0)
    init_screen()
    # auto_script.load_model('model.pkl')
    start(auto_script)