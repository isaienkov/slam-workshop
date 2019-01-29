import sys
import random
import math
from copy import deepcopy
from world import World
from element import Element

class Slam(object):
    """Main class that implements the FastSLAM1.0 algorithm"""
    def __init__(self, x, y, orien, elements_size = 50):
        self.world = World()
        self.elements = [Element(x, y, random.random()* 2.*math.pi) for _ in range(elements_size)]
        self.robot = Element(x, y, orien, is_robot=True)
        self.elements_size = elements_size

    def simulate(self):
        while True:
            for event in self.world.pygame.event.get():
                self.world.test_end(event)
            self.world.clear()
            key = self.world.pygame.key.get_pressed()
            if self.world.move_forward(key):
                self.move_forward(2)
                obs = self.robot.sense(self.world.landmarks, 2)
                for element in self.elements:
                    element.update(obs)
                self.elements = self.resample_particles()
            if self.world.turn_left(key):
                self.turn_left(5)
            if self.world.turn_right(key):
                self.turn_right(5)
            self.world.render(self.robot, self.elements, self.get_predicted_landmarks())

    def move_forward(self, step):
        self.robot.forward(step)
        for p in self.elements:
            p.forward(step)

    def turn_left(self, angle):
        self.robot.turn_left(angle)
        for p in self.elements:
            p.turn_left(angle)

    def turn_right(self, angle):
        self.robot.turn_right(angle)
        for p in self.elements:
            p.turn_right(angle)

    def resample_particles(self):
        new_particles = []
        weight = [p.weight for p in self.elements]
        index = int(random.random() * self.elements_size)
        beta = 0.0
        mw = max(weight)
        for i in range(self.elements_size):
            beta += random.random() * 2.0 * mw
            while beta > weight[index]:
                beta -= weight[index]
                index = (index + 1) % self.elements_size
            new_particle = deepcopy(self.elements[index])
            new_particle.weight = 1
            new_particles.append(new_particle)
        return new_particles

    def get_predicted_landmarks(self):
        return self.elements[0].landmarks

if __name__=="__main__":
    random.seed(5)
    simulator = Slam(80, 140, 0, elements_size=20)
    simulator.simulate()
