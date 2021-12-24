import sys
from random import choice, randint
import pygame
from pygame.constants import MOUSEWHEEL
from pygame.surface import Surface
from textbox import TextBox
from datetime import date

CAPTION = 'something'

GRID_SIZE = 4

SCREEN_SIZE = 400
TILE_SIZE = SCREEN_SIZE / GRID_SIZE

FPS = 60

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
TILE_SPEED = 0.1


COLORS = {
    'red' : (204, 21, 18),
    'gray': (55, 52, 53),
    'white': (254, 254, 254), 
    'black': (1, 1, 1),
    'background' : (2, 2, 2)
    }


class _Scene(object):
    """Overly simplified Scene."""

    def __init__(self, next_state=None):
        self.next = next_state
        self.done = False
        self.start_time = None
        self.screen_copy = None

    def startup(self, now):
        """Set present time and take a snapshot of the display."""
        self.start_time = now
        self.screen_copy = pygame.display.get_surface().copy()

    def reset(self):  # эту хрень запихнем в инит(в сцене.. например игры), и и тогда все 
                        # что по логике в инит пишем тут, для того чтобы можно было вызывать 
                        # "инит" неограниченое кол-во раз
        """Prepare for next time scene has control."""
        self.done = False
        self.start_time = None
        self.screen_copy = None
    
    def set_next_state(self, next_state: str):
        """needs for multiple next states"""
        self.next = next_state
    
    def dead(self):
        """for buttons"""
        self.done = True

    def get_event(self, event):
        """Overload in child."""
        pass

    def update(self, now):
        """If the start time has not been set run necessary startup."""
        if not self.start_time:
            self.startup(now)
    
    def draw(self, surface):
        """Overload in child."""
        pass

class Model:
    def __init__(self):
        self.done = False

        self.field = []
        self.win_pos = None
        self.create_field()
        self.zero_pos = None
        self.update_zero()
        self.observer = None

        self.scrumble()
    
    def set_observer(self, obs):
        self.observer = obs

    def get_field(self):
        return self.field

    def create_field(self):
        self.field = [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 0]]
        self.win_pos = [i[:] for i in self.field]
    
    def scrumble(self):
        dirs = list(KEY_MAPPING.values())
        for _ in range(100):
            self.move(choice(dirs))
    
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
        
        if self.observer: self.observer.add_anim(self.zero_pos, to_move_pos)
        self.update_zero()
        
        if self.observer: self.observer.print_field()
    
    def check_win(self):  
        if self.field == self.win_pos:
            return True


class AnimationTile:
    def __init__(self, from_pos, to_pos):
        self.from_pos = from_pos
        self.to_pos = to_pos
        self.anim_direction = tuple([self.to_pos[i] - self.from_pos[i] for i in (0, 1)])
        self.cur_pos = [self.to_pos[i] * TILE_SIZE for i in (0, 1)]
        self.end_pos = [self.from_pos[i] * TILE_SIZE for i in (0, 1)]
        self.to_add = [self.anim_direction[i] * TILE_SIZE * TILE_SPEED for i in (0, 1)]

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


class Game(_Scene):
    def __init__(self):
        self.next_states = ['WIN', 'CHOICE']
        _Scene.__init__(self, self.next_states[1])
        self.reset()
    
    def reset(self):
        _Scene.reset(self)
        self.model = Model()
        self.model.set_observer(self)
        self.screen = pygame.display.get_surface()
        self.my_field = None
        self.animate_now = False
        self.on_animation = {}
        self.end_timer = 0
        self.game_time = 0

        self.temporary_flag = False

    def add_anim(self, some, some_other):
        self.on_animation[some] = AnimationTile(some, some_other)
    
    def update_my_field(self):
        self.my_field = self.model.get_field()
    
    def print_field(self):
        print('\n\n\n\n')
        for i in self.model.get_field():
            for value in i:
                print("%3d" % value, end='')
            print()
    
    def start_end_timer(self, now):
        if now - self.end_timer >= 1000.0/5:
            if self.end_timer != 0: 
                self.done = True
                self.game_time = now - self.start_time
                ChoiceScreen.score = now - self.start_time
                ChoiceScreen.generate_text(ChoiceScreen)
            self.end_timer = now

    def get_event(self, event):
        if event.type == pygame.QUIT:
            self.done = True
        elif event.type == pygame.KEYDOWN:
            self.model.get_key_pressed(event.key)
            if event.key == pygame.K_r:
                self.temporary_flag = True

    def update(self, now):
        _Scene.update(self, now)
        for i in self.on_animation:
            if not self.on_animation[i].end_anim:
                self.on_animation[i].update_pos(now)
        if self.model.check_win() or self.temporary_flag:
            self.start_end_timer(now)


    def draw_cell(self, pos, screen):
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
    
                    # в другом порядке бо draw ставит сначала x а массив - сначал y
        text = FONT.render(str(value), True, COLORS['red'])
        text_rect = text.get_rect()
        text_rect.center = (rect.width/2-text.get_width()/2, rect.height/2-text.get_height()/2)
        
        pygame.draw.rect(surf, pygame.Color('skyblue'), (2, 2, TILE_SIZE-4, TILE_SIZE-4), 0, 15)
        surf.blit(text, text_rect.center)
        screen.blit(surf, rect)

    def draw(self, surf):
        self.screen.fill(COLORS['gray'])
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.draw_cell((y, x), surf)


class AbstractButton:
    def __init__(self, rect, **kwargs):
        self.rect = pygame.Rect(rect)
        self.process_kwargs(kwargs)
        self.cur_color = self.out_color
    
    def set_ava_kwargs(self):
        return {  }
    
    def process_kwargs(self, kwargs):
        init_kwargs = { "func" : lambda: "empty button func",
                        "in_color" : pygame.Color('brown'),
                        "out_color" : pygame.Color('darkred'), 
                        }
        defaults = self.set_ava_kwargs()
        defaults.update(init_kwargs)
        for kwarg in kwargs:
            if kwarg in defaults.keys():
                defaults[kwarg] = kwargs[kwarg]
            else:
                raise KeyError("Button accepts no keyword {}.".format(kwarg)) 
        self.__dict__.update(defaults)
    
    def in_rect(self):
        self.cur_color = self.in_color
    
    def out_rect(self):
        self.cur_color = self.out_color

    def on_press(self):
        self.func()
    
    def get_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                self.in_rect()
            else:
                self.out_rect()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.on_press()
                
    def draw(self, surf):
        """overload"""
        pass


class IconButton(AbstractButton):
    def __init__(self, rect, **kwargs):
        AbstractButton.__init__(self, rect, **kwargs)
        self.icon_rect = self.icon.get_rect()
        self.icon_rect.center = self.rect.center
    
    def set_ava_kwargs(self):
        return {
            "icon" : pygame.Surface((20, 20)),
            }
    
    def draw(self, surf):
        pygame.draw.rect(surf, self.cur_color, self.rect, 0, 15)
        surf.blit(self.icon, self.icon_rect)


class TextButton(AbstractButton):
    def __init__(self, rect, **kwargs):
        AbstractButton.__init__(self, rect, **kwargs)

    def set_ava_kwargs(self):
        return {
            "text" : "button",
            "text_color" : (255, 255, 0),
            }
        
    def set_text_color(self, color):
        self.text_color = color

    def draw(self, surf):
        pygame.draw.rect(surf, self.cur_color, self.rect, 0, 15)
        text = FONT.render(self.text, True, self.text_color)
        surf.blit(text, (self.rect.centerx - text.get_width()/2, self.rect.centery - text.get_height()/2))


class Button:   # надо переделать это с использованием AbstractButton
    def __init__(self, x, y, width=100, height=50, text="button", func=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.slot = func
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.main_color = pygame.Color('darkred')
        self.hower_color = pygame.Color('brown')
        self.text_color = pygame.Color('white')
        self.cur_color = self.main_color
    
    def get_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                self.cur_color = self.hower_color
            else:
                self.cur_color = self.main_color
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.slot()

    def draw(self, surf):
        pygame.draw.rect(surf, self.cur_color, self.rect, 0, 15)
        text = FONT.render(self.text, True, self.text_color)
        surf.blit(text, (self.rect.centerx - text.get_width()/2, self.rect.centery - text.get_height()/2))


class DialogBox(_Scene):
    def __init__(self):
        _Scene.__init__(self, "WIN")
        self.bg = pygame.Surface((SCREEN_SIZE, SCREEN_SIZE))
        self.bg.set_alpha(70)
        self.reset()
    
    def reset(self):
        _Scene.reset(self)
        self.rect = pygame.Rect(0, 0, SCREEN_SIZE/3*2, SCREEN_SIZE/3*2)
        self.rect.center = SCREEN_SIZE/2, SCREEN_SIZE/2
    
    def get_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.done = True

    def update(self, now):
        _Scene.update(self, now)

    def draw(self, surf):
        background = self.screen_copy.copy()
        background.blit(self.bg, (0, 0))
        surf.blit(background, (0,0))
        pygame.draw.rect(surf, COLORS['gray'], self.rect, 0, 15)


class ChoiceScreen(DialogBox):
    score = 0
    text = pygame.Surface((20, 20))
    def __init__(self):
        DialogBox.__init__(self)
        self.reset()
    
    def reset(self):
        DialogBox.reset(self)
        # self.yes_btn = Button(0, 0, text='yes', func=self.save_results)
        self.yes_btn = TextButton((0, 0, 100, 50), text='yes', func=self.save_results)
        self.no_btn = TextButton((0, 0, 100, 50), text='no', func=self.on_no_btn)
        self.yes_btn.set_text_color(COLORS['white'])
        self.no_btn.set_text_color(COLORS['white'])
        self.yes_btn.rect.y = self.no_btn.rect.y = self.rect.midbottom[1] - 70
        self.yes_btn.rect.x = self.rect.x + 20
        self.no_btn.rect.topright = self.rect.topright[0] - 20 , self.no_btn.rect.y
        
    def generate_text(self):
        text = FONT.render(f"Your time is", True, COLORS['white'])
        text_score = FONT.render(str(self.score/1000), True, COLORS['white'])
        text1 = FONT.render("Save result?", True, COLORS['white'])
        surf = pygame.Surface((text1.get_width(), text.get_height() + text1.get_height() + text_score.get_height()))
        # surf.set_colorkey((0, 0, 0))
        rct = surf.get_rect()
        surf.blit(text, (surf.get_width()/2 - text.get_width()/2, 0))
        surf.blit(text_score, (surf.get_width()/2 - text_score.get_width()/2, text.get_height()))
        surf.blit(text1, (surf.get_width()/2 - text1.get_width()/2, surf.get_height() - text1.get_height()))
        surf.set_colorkey((0, 0, 0))
        self.text = surf

    def on_no_btn(self):
        self.done = True

    def save_results(self):
        dt = date.today()
        dt_str = dt.strftime('%d/%m/%Y')
        try:
            with open('scores.txt', 'a') as file:
                file.write("{} {}\n".format(self.score/1000.0, dt_str))
        except FileNotFoundError:
            with open('scores.txt', 'w') as file:
                file.write("{} {}\n".format(self.score/1000.0, dt_str))
        self.done = True

    def get_event(self, event):
        DialogBox.get_event(self, event)
        self.yes_btn.get_event(event)
        self.no_btn.get_event(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.save_results()
    
    def update(self, now):
        DialogBox.update(self, now)
    
    def draw(self, surf):
        DialogBox.draw(self, surf)
        self.yes_btn.draw(surf)
        self.no_btn.draw(surf)
        surf.blit(self.text, (self.rect.x + self.rect.width/2-self.text.get_width()/2, self.rect.y + 40))


class WinScreen(_Scene):
    def __init__(self):
        self.states = ['GAME', 'STATS']
        _Scene.__init__(self)
        self.reset()
    
    def reset(self):
        _Scene.reset(self)
        self.button = TextButton((100, 100, SCREEN_SIZE/2, SCREEN_SIZE/2), text="S T A R T", func=self.on_start_button)
        self.button.set_text_color(COLORS['white'])
        self.stats_btn = IconButton((10, 10, 50, 50), func=self.on_stats_btn, icon=MENU_ICON)


    def on_start_button(self):
        self.set_next_state(self.states[0])
        self.done = True
    
    def on_stats_btn(self):
        self.set_next_state(self.states[1])
        self.done = True

    def get_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.on_start_button()
        self.button.get_event(event)
        self.stats_btn.get_event(event)

    def update(self, now):
        _Scene.update(self, now)

    def draw(self, surf):
        surf.fill(COLORS['gray'])
        self.button.draw(surf)
        self.stats_btn.draw(surf)


class ScrollView:
    def __init__(self, child: pygame.Surface, height, pos=(0, 0)):
        self.child = child
        self.child_rect = child.get_rect() # перемещается
        self.child_rect.height = height # неизменен
        self.pos = pos # неизменен
        self.scrollsurf = pygame.Surface(self.child_rect.size) # то где будем рисовать кусок child
        self.scrollrect = self.scrollsurf.get_rect()
        self.cur_y_pos = self.child_rect.y

    def get_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            self.update(event.y)

    def update(self, y):
        self.child_rect.y += y
    
    def update_scrolled_surface(self, surf):
        self.__init__(surf, self.child_rect.height, self.pos)

    def draw(self, surf):
        self.scrollsurf.fill(tuple(map(lambda x: x - 10, COLORS['gray'])))
        self.scrollsurf.blit(self.child, self.child_rect)
        surf.blit(self.scrollsurf, self.pos)


class StatsScreen(_Scene):
    data_surf = pygame.Surface((50, 50))

    def __init__(self):
        _Scene.__init__(self, "WIN")
        self.reset()
    
    def reset(self):
        _Scene.reset(self)
        self.num = 0
        self.data_surf = self.generate_table_surf()
        self.data_scroll = ScrollView(self.data_surf, 300, (20, 90))
        self.back_btn = IconButton((10, 10, 50, 50), func=self.dead, icon=BACK_ICON)
        

    def generate_table_surf(self):
        margin = 10
        with open('scores.txt', 'r') as file:
            data = list(map(lambda x: x.split(), file.readlines()))
        value_list = []
        for i in data:
            value_row = []
            for val in i:
                surf = FONT.render(val, True, pygame.Color(COLORS['white']))
                value_row.append(surf)
            value_list.append(value_row)

        val_width = value_list[0][0].get_width() if value_list[0][0].get_width() > value_list[0][1].get_width() else value_list[0][1].get_width()
        val_height = value_list[0][0].get_height()

        surf_width = val_width * 2 + margin
        surf_height = val_height * len(value_list) + margin * len(value_list) - 1
        
        surf = pygame.Surface((surf_width, surf_height))
        surf.set_colorkey((0, 0, 0))

        for y in range(len(value_list)):
            for x in range(len(value_list[0])):
                value = value_list[y][x]
                _x = x * val_width
                _y = y * val_height
                surf.blit(value, (_x, _y))
                
        return surf
    
    def update_table(self):
        self.data_surf = self.generate_table_surf()
        self.data_scroll.update_scrolled_surface(self.data_surf)

    def get_event(self, event):
        if event.type == pygame.KEYDOWN:
            self.done = True
        if event.type == pygame.MOUSEWHEEL:
            self.num += event.y
        if event.type == pygame.MOUSEBUTTONDOWN:
            pass
        self.data_scroll.get_event(event)
        self.back_btn.get_event(event)
    
    def update(self, now):
        _Scene.update(self, now)
        if now - self.start_time > 5 and now - self.start_time < 80:
            self.update_table()
    
    def draw(self, surf):
        text = FONT.render(str(self.num), True, (255, 255, 255))
        surf.fill(COLORS['gray'])
        surf.blit(text, (SCREEN_SIZE/2-text.get_width()/2, SCREEN_SIZE/2-text.get_height()/2))
        self.data_scroll.draw(surf)
        self.back_btn.draw(surf)


class Control:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.clock = pygame.time.Clock()
        self.fps = FPS
        self.done = False
        self.state_dict = {
            'STATS' : StatsScreen(),
            'WIN': WinScreen(), 
            'GAME': Game(),
            'CHOICE': ChoiceScreen(),
            }
        self.state = self.state_dict['WIN'] 

    def event_loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.done = True
            
            self.state.get_event(event)

    def update(self):
        now = pygame.time.get_ticks()
        self.state.update(now)
        if self.state.done:

            self.state.reset()
            self.state = self.state_dict[self.state.next]

    def draw(self):
        if self.state.start_time:

            self.state.draw(self.screen)

    def display_fps(self):
        caption = '{} - fps: {:.2f}'.format(CAPTION, self.clock.get_fps())
        pygame.display.set_caption(caption)
    
    def main_loop(self):
        # self.screen.fill(COLORS['background'])
        while not self.done:
            self.event_loop()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(self.fps)
            self.display_fps()


def main():
    global FONT, SMALL_FONT, MENU_ICON, BACK_ICON
    pygame.init()
    FONT = pygame.font.Font(None, 50)
    SMALL_FONT = pygame.font.Font(None, 25)

    pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))

    MENU_ICON = pygame.image.load('menu-button.png').convert_alpha()
    arr = pygame.PixelArray(MENU_ICON)
    arr.replace((0, 0, 0), COLORS['white'])
    del arr
    
    BACK_ICON = pygame.image.load('back-button.png').convert_alpha()
    arr = pygame.PixelArray(BACK_ICON)
    arr.replace((0, 0, 0), COLORS['white'])
    del arr

    Control().main_loop()
    
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
