import pygame


SCREEN_SIZE = (720, 480)
PLAY_SIZE = (400, 400)
TILE_SIZE = (PLAY_SIZE[0] // 4, PLAY_SIZE[1] // 4)
TILE_SPEED = 5
TILE_STATES = {"movable": "immovable", "immovable": "movable"}

# OPPOSITES = {"left": "right", 
#              "right": "left",
#              "up": "down", 
#              "down": "up"}

DIRECT_DICT = {"left": (-1, 0), "right": (1, 0),
               "up": (0, -1), "down": (0, 1)}

OPPOSITES = {
    (-1, 0) : (1, 0), 
    (1, 0) : (-1, 0),
    (0, 1) : (0, -1), 
    (0, -1) : (0, 1),
}

KEY_MAPPING = {(pygame.K_LEFT, pygame.K_a): (-1, 0),   # left
               (pygame.K_RIGHT, pygame.K_d): (1, 0),   # right
               (pygame.K_UP, pygame.K_w): (0, -1),     # up
               (pygame.K_DOWN, pygame.K_s): (0, 1)}    # down



class Tile:
    def __init__(self, pos, num):
        self.bpos = pos
        self.num = num
        self.move_direction = None  # (int, int)
        self.init_pos = tuple([pos[i] * TILE_SIZE[i] for i in (0, 1)])
        self.moving = False
        self.tile_surf = pygame.Surface(TILE_SIZE)

        self.tile_rect = self.tile_surf.get_rect()
        self.tile_rect.topleft = self.init_pos

        self.zero_pos = None
    
    def get_key_pressed(self, key, zero_tile):
        for keys in KEY_MAPPING:
            if key in keys:
                direct = KEY_MAPPING[keys]
                if direct == self.move_direction:
                    self.move(zero_tile)

    def set_movable(self, bol):
        self.movable = bol

    def update_direction(self, vector):
        self.move_direction = OPPOSITES[vector]

    def move(self, zero_tile):
        self.zero_pos = zero_tile.tile_rect.topleft
        zero_tile.tile_rect.topleft = self.tile_rect.topleft
        self.moving = True
        temp = self.bpos
        self.bpos = self.zero_pos
        zero_tile.bpos = temp

    def update(self):
        if self.moving and (self.tile_rect.x != self.zero_pos[0] or \
                                self.tile_rect.x != self.zero_pos[1]):
            self.tile_rect.x += TILE_SPEED * self.move_direction[0]
            self.tile_rect.y += TILE_SPEED * self.move_direction[1] 
        else:
            self.moving = False
            

    def draw_text(self):
        text = FONT.render(str(self.num), True, (0, 0, 10))
        text_rect = text.get_rect()
        text_rect.center = (self.tile_rect.width // 2, self.tile_rect.height // 2)
        self.tile_surf.blit(text, text_rect)

    def draw(self, surf):
        self.tile_surf.fill((200, 10, 10))
        if self.num: self.draw_text()
        surf.blit(self.tile_surf, self.tile_rect)


class Game:
    def __init__(self):
        self.done = False
        self.game_screen = pygame.Surface(PLAY_SIZE)
        self.game_rect = self.game_screen.get_rect()
        self.zero_tile = None
        self.tiles = self.init_board()
        self.movable = []
        self.update_movable()
        self.tile = Tile((0, 0), 0)
    
    def init_board(self):
        board = []
        count = 0
        for y in range(0, 4):
            for x in range(0, 4):
                board.append(Tile((x, y), count+1))
                count += 1
        board[-1].num = 0
        self.zero_tile = board.pop() 
        return board

    def update_movable(self):
        self.movable.clear()
        for vector in DIRECT_DICT.values():
            tile_pos = tuple([vector[i] + self.zero_tile.bpos[i] for i in (0, 1)])
            if tile_pos in [i.bpos for i in self.tiles]:
                tile = list(filter(lambda x: x.bpos == tile_pos, self.tiles))[0]
                tile.update_direction(vector)
                tile.set_movable(True)
                self.movable.append(tile)


    def get_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            pass
        if event.type == pygame.KEYDOWN:
            for tile in self.movable:
                tile.get_key_pressed(event.key, self.zero_tile)
                
    
    def update(self):
        for tile in self.tiles:
            tile.update()
        self.update_movable()
        self.zero_tile.update()
    
    def draw(self, surf: pygame.Surface):
        # surf здесь нужен только для того чтобы отобразить игру на бекграунде
        # уберу это когда сделаю сцены, и тогда blit будет на self.screen_copy... 
        # наверное...
        self.game_screen.fill((0, 255, 0))
        for tile in self.tiles: 
            tile.draw(self.game_screen)
        # self.zero_tile.draw(self.game_screen)
        surf.blit(self.game_screen, list(map(lambda x: x - self.game_rect.width//2, 
                                                surf.get_rect().center)))


class Control:
    def __init__(self):
        self.fps = 60
        self.clock = pygame.time.Clock()
        self.scene = Game()
        self.done = False
        self.screen = pygame.display.get_surface()

    def update(self):
        self.scene.update()
        if self.scene.done:
            self.done = True

    def draw(self):
        self.screen.fill((150, 150, 150))
        self.scene.draw(self.screen)

    def event_loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.done = True
            self.scene.get_event(event)
        # print(pygame.mouse.get_pressed())

    def main_loop(self):
        while not self.done:
            self.event_loop()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(self.fps)


def main():
    global FONT
    pygame.init()
    
    FONT = pygame.font.Font(None, 20)

    pygame.display.set_mode(SCREEN_SIZE)
    game = Control()
    game.main_loop()


if __name__ == '__main__':
    main()
