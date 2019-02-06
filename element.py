import random
import math
import numpy as np
from math_functions import *
from scipy import linalg
from world import WINDOWWIDTH, WINDOWHEIGHT
from landmark import Landmark

class Particle(object):
    """Represents the robot and particles"""
    TOL = 1E-250
    RADIUS = 80


    def __init__(self, x, y, orien, is_robot=False):
        """pos_x: from left to right
           pos_y: from up to down
           orientation: [0,2*pi)
        """
        self.pos_x = x
        self.pos_y = y
        self.orientation = orien
        self.dick_length = 20
        self.is_robot = is_robot
        self.landmarks =[]
        self.set_noise()
        self.weight = 1.0
        # Model error term will relax the covariance matrix
        self.obs_noise = np.array([[0.1, 0], [0, (3.0*math.pi/180)**2]])

    def pos(self):
        return (self.pos_x, self.pos_y)

    def set_noise(self):
        if self.is_robot:
            # Measurement Noise will detect same feature at different place
            self.bearing_noise = 0.1
            self.distance_noise = 0.1
            self.motion_noise = 0.5
            self.turning_noise = 1
        else:
            self.bearing_noise = 0
            self.distance_noise = 0
            self.motion_noise = 0
            self.turning_noise = 0 # unit: degree

    def set_pos(self, x, y, orien):
        """The arguments x, y are associated with the origin at the bottom left.
        """
        if x > WINDOWWIDTH:
            x = WINDOWWIDTH
        if y > WINDOWHEIGHT:
            y = WINDOWHEIGHT
        self.pos_x = x
        self.pos_y = y
        self.orientation = orien

    def reset_pos(self):
        self.set_pos(random.random() * WINDOWWIDTH, random.random() * WINDOWHEIGHT, random.random() * 2. * math.pi)

    def check_pos(self, x, y):
        """Checks if a particle is in the invalid place"""
        if x >= WINDOWWIDTH or y >= WINDOWHEIGHT or x <=0 or y <= 0:
            return True

    def forward(self, d):
        """Motion model.
           Moves robot forward of distance d plus gaussian noise
        """
        x = self.pos_x + d * math.cos(self.orientation) + gauss_noise(0, self.motion_noise)
        y = self.pos_y + d * math.sin(self.orientation) + gauss_noise(0, self.motion_noise)
        if self.check_pos(x, y):
            if self.is_robot:
                return
            else:
                self.reset_pos()
                return
        else:
            self.pos_x = x
            self.pos_y = y

    def turn_left(self, angle):
        self.orientation = (self.orientation + (angle + gauss_noise(0, self.turning_noise)) / 180. * math.pi) % (2 * math.pi)

    def turn_right(self, angle):
        self.orientation = (self.orientation - (angle + gauss_noise(0, self.turning_noise)) / 180. * math.pi) % (2 * math.pi)

    def dick(self):
        return [(self.pos_x, self.pos_y), (self.pos_x + self.dick_length * math.cos(self.orientation), self.pos_y + self.dick_length * math.sin(self.orientation))]

    def update(self, obs):
        """After the motion, update the weight of the particle and its EKFs based on the sensor data"""
        for o in obs:
            prob = np.exp(-70)

            if self.landmarks:
                # find the data association with ML
                prob, landmark_idx, ass_obs, ass_jacobian, ass_adjcov = self.find_data_association(o)
                if prob < self.TOL:
                    # create new landmark
                    self.create_landmark(o)
                else:
                    # update corresponding EKF
                    self.update_landmark(np.transpose(np.array([o])), landmark_idx, ass_obs, ass_jacobian, ass_adjcov)
            else:
                # no initial landmarks
                self.create_landmark(o)
            self.weight *= prob

    def sense(self, landmarks, num_obs):
        """
        Only for robot.
        Given the existing landmarks, generates a random number of obs (distance, direction)
        """
        obs_list = []
        for i in range(0,len(landmarks)):
            l = landmarks[i].pos()
            # apply distance noise
            dis = self.sense_distance(l)

            if dis < self.RADIUS:
                # apply angle noise
                direction = self.sense_direction(l)
                obs_list.append((dis, direction))

        return obs_list

    def sense_distance(self, landmark):
        """Measures the distance between the robot and the landmark. Add noise"""
        dis = euclidean_distance(landmark, (self.pos_x, self.pos_y))
        noise = gauss_noise(0, self.distance_noise)
        if (dis + noise) > 0:
            dis += noise
        return dis

    def sense_direction(self, landmark):
        """Measures the direction of the landmark with respect to robot. Add noise"""
        direction = cal_direction((self.pos_x, self.pos_y), (landmark[0], landmark[1]))
        angle_noise = gauss_noise(0, self.bearing_noise*math.pi/180)
        if direction + angle_noise > math.pi:
            result = direction + angle_noise - 2*math.pi
        elif direction + angle_noise < - math.pi:
            result = direction + angle_noise + 2*math.pi
        else:
            result = direction + angle_noise
        return result

    def compute_jacobians(self, landmark):
        dx = landmark.pos_x - self.pos_x
        dy = landmark.pos_y - self.pos_y
        d2 = dx**2 + dy**2
        d = math.sqrt(d2)

        predicted_obs = np.array([[d],[math.atan2(dy, dx)]])
        jacobian = np.array([[dx/d,   dy/d],
                             [-dy/d2, dx/d2]])
        adj_cov = jacobian.dot(landmark.sig).dot(np.transpose(jacobian)) + self.obs_noise
        return predicted_obs, jacobian, adj_cov

    def guess_landmark(self, obs):
        """Based on the particle position and observation, guess the location of the landmark. Origin at top left"""
        distance, direction = obs
        lm_x = self.pos_x + distance * math.cos(direction)
        lm_y = self.pos_y + distance * math.sin(direction)
        return Landmark(lm_x, lm_y)

    def find_data_association(self, obs):
        """Using maximum likelihood to find data association"""
        prob = 0
        ass_obs = np.zeros((2,1))
        ass_jacobian = np.zeros((2,2))
        ass_adjcov = np.zeros((2,2))
        landmark_idx = -1
        for idx, landmark in enumerate(self.landmarks):
            predicted_obs, jacobian, adj_cov = self.compute_jacobians(landmark)
            p = multi_normal(np.transpose(np.array([obs])), predicted_obs, adj_cov)
            if p > prob:
                prob = p
                ass_obs = predicted_obs
                ass_jacobian = jacobian
                ass_adjcov = adj_cov
                landmark_idx = idx
        return prob, landmark_idx, ass_obs, ass_jacobian, ass_adjcov

    def create_landmark(self, obs):
        landmark = self.guess_landmark(obs)
        self.landmarks.append(landmark)

    def update_landmark(self, obs, landmark_idx, ass_obs, ass_jacobian, ass_adjcov):
        landmark = self.landmarks[landmark_idx]
        K = landmark.sig.dot(np.transpose(ass_jacobian)).dot(linalg.inv(ass_adjcov))
        new_mu = landmark.mu + K.dot(obs - ass_obs)
        new_sig = (np.eye(2) - K.dot(ass_jacobian)).dot(landmark.sig)
        landmark.update(new_mu, new_sig)

    def __str__(self):
        return str((self.pos_x, self.pos_y, self.orientation, self.weight))




