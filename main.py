import sys
import random
import math
from copy import deepcopy
from world import World
from element import Particle

class Slam(object):

    def __init__(self, x, y, orien, particle_size = 50):
        self.world = World()
        self.particles = [Particle(x, y, random.random()* 2.*math.pi) for _ in range(particle_size)]
        self.robot = Particle(x, y, orien, is_robot=True)
        self.particle_size = particle_size

    def simulate(self):
        while True:
            for event in self.world.pygame.event.get():
                self.world.test_end(event)
            self.world.clear()
            key = self.world.pygame.key.get_pressed()
            if self.world.move_forward(key):
                self.move_forward(5)
                obs = self.robot.sense(self.world.landmarks, 2)
                for particle in self.particles:
                    particle.update(obs)
                self.particles = self.resample_particles()
            if self.world.turn_left(key):
                self.turn_left(5)
            if self.world.turn_right(key):
                self.turn_right(5)
            self.world.render(self.robot, self.particles, self.get_predicted_landmarks())

    def move_forward(self, step):
        self.robot.forward(step)
        for p in self.particles:
            p.forward(step)

    def turn_left(self, angle):
        self.robot.turn_left(angle)
        for p in self.particles:
            p.turn_left(angle)

    def turn_right(self, angle):
        self.robot.turn_right(angle)
        for p in self.particles:
            p.turn_right(angle)

    def resample_particles(self):
        new_particles = []
        weight = [p.weight for p in self.particles]
        index = int(random.random() * self.particle_size)
        beta = 0.0
        mw = max(weight)
        for i in range(self.particle_size):
            beta += random.random() * 2.0 * mw
            while beta > weight[index]:
                beta -= weight[index]
                index = (index + 1) % self.particle_size
            new_particle = deepcopy(self.particles[index])
            new_particle.weight = 1
            new_particles.append(new_particle)

        return new_particles

    def get_predicted_landmarks(self):
        return self.particles[0].landmarks

if __name__=="__main__":
    random.seed(5)
    simulator = Slam(160, 140, 0, 100)
    simulator.simulate()
