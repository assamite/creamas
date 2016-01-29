'''
.. py:module:: spiro_agent
    :platform: Unix

Agent that creates spirographs and evaluates them by their novelty, similar to
Saunders etal. work.
'''
import os
import time
import functools

import numpy as np
from scipy import ndimage, misc

from creamas.core import CreativeAgent
from creamas.math import gaus_pdf

from som import ImageSOM
from spiro import give_dots

class SpiroAgent(CreativeAgent):

    def __init__(self, environment, desired_novelty, log_folder=None):
        # Call super class' constructor first
        super().__init__(environment, log_folder=log_folder)
        self.spiro_args = np.array(np.random.uniform(10, 190, [2,]))
        # How many spirographs are generated to find the best one per iteration.
        self.search_width = 10 
        self.img_size = 32
        self.desired_novelty = desired_novelty
        init_func = functools.partial(np.random.normal, 0.9, 0.4)
        self.som = ImageSOM(6, 6, self.img_size**2, init_func, coef=0.1)

    def create(self, r, _r, R=200):
        '''Crete new spirograph image with given arguments. Returned image is
        scaled to agent's preferred image size.
        '''
        x, y = give_dots(R, r, _r, spins=20)
        xy = np.array([x, y]).T
        xy = np.array(np.around(xy), dtype=np.int64)
        xy = xy[(xy[:, 0] >= -250) & (xy[:, 1] >= -250) & (xy[:, 0] < 250) & (xy[:, 1] < 250)]
        xy = xy + 250
        img = np.ones([500, 500], dtype=np.uint8)
        img[:] = 255
        img[xy[:, 0], xy[:, 1]] = 0
        img = misc.imresize(img, [32, 32])
        fimg = img / 255.0
        return fimg

    def randomize_args(self):
        '''Randomize agent's spirograph generation arguments.
        '''
        args = self.spiro_args + np.random.normal(0, 10, self.spiro_args.shape)
        np.clip(args, -199, 199, args)
        return args

    def hedonic_value(self, novelty):
        lmax = gaus_pdf(self.desired_novelty, self.desired_novelty, 4)
        pdf = gaus_pdf(novelty, self.desired_novelty, 4)
        return pdf / lmax

    def novelty(self, img):
        # distance to closes cell in som
        dist = self.som.distance(img.flatten())
        return dist

    def invent(self):
        '''Invent new spirograph by taking n random steps from current position
        (spirograph generation parameters) and selecting the best one.
        '''
        best_args = self.randomize_args()
        best_img = self.create(best_args[0], best_args[1])
        best_hedonic_value = self.hedonic_value(self.novelty(best_img))
        for i in range(self.search_width-1):
            args = self.randomize_args()
            img = self.create(args[0], args[1])
            hedonic_value = self.hedonic_value(self.novelty(img))
            if hedonic_value > best_hedonic_value:
                best_hedonic_value = hedonic_value
                best_args = args
                best_img = img
        return best_img, best_args, best_hedonic_value

    async def act(self):
        '''Agent's main method to create new artifacts.

        See Simulation and CreativeAgent documentation for details.
        '''
        img, args, val = self.invent()
        self.logger.log(self.logger.DEBUG, "args={}, val={}".format(args, val))
        self.spiro_args = args
        for i in range(5):
            self.som.train_cycle(img.flatten())
        if self.logger is not None:
            im_name = '{}_N{}_{:0>4}.png'.format(self.name, self.desired_novelty,
                                               self.age)
            path = os.path.join(self.logger.folder, im_name)
            misc.imsave(path, img)
            somimg = self.som.get_as_image()
            somim_name = '{}_N{}_SOM_{:0>4}.png'.format(self.name,
                                                    self.desired_novelty,
                                                    self.age)
            path = os.path.join(self.logger.folder, somim_name)
            misc.imsave(path, somimg)


if __name__ == "__main__":
    from creamas.core import Simulation, Environment
    log_folder = 'logs'
    env = Environment(log_folder=log_folder)
    for e in range(1, 21):
        a = SpiroAgent(env, desired_novelty=e, log_folder=log_folder)

    env.create_initial_connections(n=len(env.agents)-1)
    sim = Simulation(env, log_folder=log_folder)
    sim.steps(10)
    sim.end()