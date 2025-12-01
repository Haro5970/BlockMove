import pygame
from settings import *

class Player(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pygame.Surface((TILESIZE, TILESIZE))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = x * TILESIZE
        self.rect.y = y * TILESIZE
        self.offset_x = 0
        self.offset_y = 0

    def move(self, dx=0, dy=0):
        self.x += dx
        self.y += dy

    def bounce(self, dx, dy):
        self.offset_x = dx * 10
        self.offset_y = dy * 10

    def update(self):
        # Animate back to center
        if self.offset_x > 0:
            self.offset_x -= 2
        elif self.offset_x < 0:
            self.offset_x += 2
        
        if self.offset_y > 0:
            self.offset_y -= 2
        elif self.offset_y < 0:
            self.offset_y += 2

        self.rect.x = self.x * TILESIZE + self.offset_x
        self.rect.y = self.y * TILESIZE + self.offset_y

class Wall(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.walls
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pygame.Surface((TILESIZE, TILESIZE))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = x * TILESIZE
        self.rect.y = y * TILESIZE

class Block(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.blocks
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pygame.Surface((TILESIZE, TILESIZE))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = x * TILESIZE
        self.rect.y = y * TILESIZE

    def move(self, dx=0, dy=0):
        self.x += dx
        self.y += dy
        self.rect.x = self.x * TILESIZE
        self.rect.y = self.y * TILESIZE

class Hole(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.holes
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pygame.Surface((TILESIZE, TILESIZE))
        self.image.fill(BLACK)
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = x * TILESIZE
        self.rect.y = y * TILESIZE
