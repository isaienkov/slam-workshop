import pygame
import sys
from pygame.locals import *
from landmark import Landmark
import numpy as np

FPS=10
WINDOWWIDTH = 600
WINDOWHEIGHT = 600
LANDMARKNUMBER = 8
seed = 0

np.random.seed(seed)

COLOR = {
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "red": (255, 0, 0),
    "purple": (128, 0, 128)
}

class World(object):
    """Implement the pygame simulator, drawing and rendering stuff"""
    def __init__(self):
        self.pygame = pygame
        self.fpsClock = self.pygame.time.Clock()
        self.main_clock = self.pygame.time.Clock()
        self.window = self.pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT), 0, 32)
        self.pygame.display.set_caption("SLAM simulator")
        self.setup_world()

    def setup_world(self):
        """Set up landmarks"""
        self.landmarks = [Landmark(np.random.randint(0,WINDOWHEIGHT-20), np.random.randint(0,WINDOWWIDTH-20)) for _ in range(LANDMARKNUMBER)]

    def draw(self, robot, particles, landmarks):
        """Draw the objects in the window"""
        for landmark in self.landmarks:
            self.pygame.draw.circle(self.window, COLOR["green"], self.convert_coordinates(landmark.pos()), 7)
        self.pygame.draw.circle(self.window, COLOR["blue"], self.convert_coordinates(robot.pos()), 12)
        self.pygame.draw.line(self.window, COLOR["green"], *[self.convert_coordinates(pos) for pos in robot.dick()])
        for particle in particles:
            self.pygame.draw.circle(self.window, COLOR["red"], self.convert_coordinates(particle.pos()), 5)
        for landmark in landmarks:
            self.pygame.draw.circle(self.window, COLOR["purple"], self.convert_coordinates(landmark.pos()), 5)

    def convert_coordinates(self, pos):
        return (int(pos[0]), int(WINDOWHEIGHT - pos[1]))

    def test_end(self, event):
        if event.type == QUIT:
            self.pygame.quit()
            sys.exit()

    def clear(self):
        self.window.fill(COLOR["black"])

    def move_forward(self, key_pressed):
        return key_pressed[K_UP]

    def turn_left(self, key_pressed):
        return key_pressed[K_LEFT]

    def turn_right(self, key_pressed):
        return key_pressed[K_RIGHT]

    def render(self, robot, particles, landmarks):
        self.draw(robot, particles, landmarks)
        self.fpsClock.tick(FPS)
        self.pygame.display.update()