import sys
from random import randint
import pygame

GRID_SIZE = 4

SCREEN_SIZE = 400
TILE_SIZE = SCREEN_SIZE / GRID_SIZE

# противоположные, потому что чтобы сдвинуть вправо, нужно переставить 
# ту что СЛЕВА от нуля
DIRECTIONS = {
    'RIGHT': (0, -1),  ##     (y, x) => self.field[y][x]
    'LEFT' : (0, 1),   ##
    'UP'   : (1, 0),
    'DOWN' : (-1, 0)
    }
# print(DIRECTIONS['DOWN'][1])

KEY_MAPPING = {
    (pygame.K_w, pygame.K_UP) : 'UP',
    (pygame.K_s, pygame.K_DOWN) : 'DOWN', 
    (pygame.K_a, pygame.K_LEFT) : 'LEFT', 
    (pygame.K_d, pygame.K_RIGHT) : 'RIGHT', 
    }

ANIMATION_TIME = 500  # miliseconds


COLORS = {
    'red' : (204, 21, 18),
    'gray': (55, 52, 53),
    'white': (254, 254, 254), 
    'black': (1, 1, 1)
    }


class Model:
    def __init__(self):
        self.field = []
        self.create_field()
        self.zero_pos = None
        self.update_zero()
        print(f' в ините {self.zero_pos = }')
        self.done = False
        self.observer: View = None
    
    def set_observer(self, obs):
        self.observer = obs

    def get_field(self):
        return self.field

    def create_field(self):
        added = []
        for _ in range(GRID_SIZE):
            row = []
            for _ in range(GRID_SIZE):
                item = randint(0, 15)
                while item in added:
                    item = randint(0, 15)
                row.append(item)
                added.append(item)
            self.field.append(row)
    
    def update_zero(self):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.field[y][x] == 0:
                    self.zero_pos = (y, x)
                
    def get_key_pressed(self, pressed):
        if pressed == pygame.K_q:
            self.done = True
        for keys in KEY_MAPPING:
            if pressed in keys:
                self.move(KEY_MAPPING[keys])
                
    def move(self, direct: str):
        try: # to_move_pos - взяли того, кого будем передвигать на 0 позицию
            to_move_pos = tuple([self.zero_pos[i] + DIRECTIONS[direct][i] for i in (0, 1)])
            if -1 in to_move_pos: return
            value = self.field[to_move_pos[0]][to_move_pos[1]]
            self.field[self.zero_pos[0]][self.zero_pos[1]] = value
            self.field[to_move_pos[0]][to_move_pos[1]] = 0


        except IndexError:
            return
        self.observer.add_animation(to_move_pos, self.zero_pos)
        self.observer.add_anim(self.zero_pos, to_move_pos)
        self.update_zero()
        self.observer.print_field()


class AnimationTile:
    def __init__(self, from_pos, to_pos):
        self.from_pos = from_pos
        self.to_pos = to_pos
        self.anim_direction = tuple([self.to_pos[i] - self.from_pos[i] for i in (0, 1)])
        self.cur_pos = [self.to_pos[i] * TILE_SIZE for i in (0, 1)]
        self.end_pos = [self.from_pos[i] * TILE_SIZE for i in (0, 1)]
        self.to_add = [self.anim_direction[i] * TILE_SIZE * 0.05 for i in (0, 1)]
                                                          # ^^^^ коефициент приращения

        self.timer = 0
        self.end_anim = False
    
    def update_pos(self, now):
        if now - self.timer >= 1000.0/ANIMATION_TIME:
            self.timer = now
            self.cur_pos = [self.cur_pos[i] - self.to_add[i] for i in (0, 1)]
        
        index_not_zero = 1 if self.anim_direction.index(0) == 0 else 0
        if self.end_pos[index_not_zero] - 10 < self.cur_pos[index_not_zero] < self.end_pos[index_not_zero] + 10:
            self.cur_pos = self.end_pos
            self.end_anim = True
    
    def get_cur_pos(self):
        return reversed(self.cur_pos)

class View:
    def __init__(self):
        self.model = Model()
        self.model.set_observer(self)
        self.screen = pygame.display.get_surface()
        self.my_field = None
        self.done = False
        self.animate_now = False
        self.on_animation = {}
    
    def add_anim(self, some, some_other):
        self.on_animation[some] = AnimationTile(some, some_other)

    def add_animation(self, pos, end_pos):
        pass        
    
    def update_my_field(self):
        self.my_field = self.model.get_field()
    
    def print_field(self):
        print('\n\n\n')
        for i in self.model.get_field():
            for value in i:
                print("%3d" % value, end='')
            print()
    
    def event_loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.done = True
            elif event.type == pygame.KEYDOWN:
                self.model.get_key_pressed(event.key)

    def update(self):
        now = pygame.time.get_ticks()
        for i in self.on_animation:
            if not self.on_animation[i].end_anim:
                self.on_animation[i].update_pos(now)
    
    def draw_cell(self, pos):
        if pos in self.on_animation:
            cur_pos = self.on_animation[pos].get_cur_pos()
        else: 
            cur_pos = (pos[1] * TILE_SIZE, pos[0] * TILE_SIZE)
        rect = pygame.Rect(*cur_pos, TILE_SIZE, TILE_SIZE)
        surf = pygame.Surface((int(rect.width), int(rect.height)))
        surf.set_colorkey((0, 0, 0))
        
        value = self.model.get_field()[pos[0]][pos[1]]

        if not value:
            return
        else:
            color = pygame.Color('lightblue') # в другом порядке бо draw ставит сначала x а массив - сначал y
        
        text: pygame.Surface = FONT.render(str(value), True, COLORS['red'])
        text_rect = text.get_rect()
        text_rect.center = (rect.width/2-text.get_width()/2, rect.height/2-text.get_height()/2)
        
        pygame.draw.rect(surf, pygame.Color('skyblue'), (2, 2, TILE_SIZE-4, TILE_SIZE-4), 0, 15)
        surf.blit(text, text_rect.center)
        self.screen.blit(surf, rect)

    def draw(self):
        self.screen.fill(COLORS['gray'])
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.draw_cell((y, x))

    def main_loop(self):
        self.print_field()
        # self.update_my_field()
        while not self.done:
            self.event_loop()
            self.update()
            self.draw()
            pygame.display.update()


# class Control:
#     def __init__(self):
#         self.fps = 60.0
#         self.states = 


def main():
    global FONT
    pygame.init()
    pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    FONT = pygame.font.Font(None, 50)
    view = View()
    view.main_loop()
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
