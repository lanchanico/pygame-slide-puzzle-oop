import pygame
import sys

CAPTION = "supergame"
SCR_SIZE = (400, 400)

COLORS = {
    'background' : (15, 15, 15),

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

    def reset(self):
        """Prepare for next time scene has control."""
        self.done = False
        self.start_time = None
        self.screen_copy = None

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


class InterestingGame(_Scene):
    def __init__(self):
        _Scene.__init__(self, "SUPERNEXTSCREEN")
        self.reset()
    
    def reset(self):
        _Scene.reset(self)
        self.interesting_text = 'InterestingGame here, press n to go next'
        self.x = 10
        self.y = 10
    
    def get_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_n:
                self.done = True
    
    def update(self, now):
        _Scene.update(self, now)
        self.y += 0.5
    
    def draw(self, surf):
        surf.fill(COLORS["background"])
        pygame.draw.rect(surf, pygame.Color('red'), (10, 10, 50, 50), 0, 20)
        text = FONT.render(self.interesting_text, True, (255, 255, 255))
        surf.blit(text, (self.x, int(self.y)))


class SuperNextScreen(_Scene):
    def __init__(self):
        _Scene.__init__(self, "INTERESTINGGAME")
        self.reset()
    
    def reset(self):
        _Scene.reset(self)
        self.interesting_text = 'this is SuperNextScreen, press b...'
        self.x = 10
        self.y = 10
        self.timer = 0
        self.seconds = 0
    
    def get_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_b:
                self.done = True
    
    def update(self, now):
        _Scene.update(self, now)
        self.y += 0.5
        self.x += 0.5
        if now - self.timer >= 1000:
            self.timer = now
            self.seconds += 1
    
    def draw(self, surf):
        surf.fill(pygame.Color('skyblue'))
        pygame.draw.rect(surf, pygame.Color('yellow'), (10, 10, 50, 50), 0, 20)
        text = FONT.render(self.interesting_text, True, (0, 0, 0))
        time = FONT.render(str(self.seconds), True, (0, 0, 0))
        surf.blit(time, (SCR_SIZE[0]/2, SCR_SIZE[1]/2))
        surf.blit(text, (int(self.x), int(self.y)))


class Control:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.done = False
        self.state_dict = { 
            "INTERESTINGGAME" : InterestingGame(), 
            "SUPERNEXTSCREEN" : SuperNextScreen()
            }
        self.state = self.state_dict['INTERESTINGGAME']
    
    def event_loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.done = True
            self.state.get_event(event)
    
    def update(self):
        now = pygame.time.get_ticks()
        self.state.update(now)
        if self.state.done:
            self.state.reset()  # типа перезапустили сцену для дальнейшего использования 
                                # повторно
            self.state = self.state_dict[self.state.next]

    def draw(self):
        if self.state.start_time:
            self.state.draw(self.screen)

    def display_fps(self):
        caption = '{} - fps: {:.2f}'.format(CAPTION, self.clock.get_fps())
        pygame.display.set_caption(caption)
    
    def main_loop(self):
        self.screen.fill(COLORS['background'])
        while not self.done:
            self.event_loop()
            self.update()
            self.draw()
            pygame.display.update()
            self.clock.tick(self.fps)
            self.display_fps()


def main():
    global FONT
    pygame.init()
    FONT = pygame.font.Font(None, 25)
    pygame.display.set_mode(SCR_SIZE)
    Control().main_loop()
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()