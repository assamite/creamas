'''
.. py:module:: som
    :platform: Unix

Self-Organizing Map implementation.
'''
import numpy as np
from gui import ColorSOM_GUI, ImageSOM_GUI
from matplotlib.mlab import dist

class Cell():
    '''Basic SOM cell that knows its location in 2D space, but has no display
    method.
    '''
    def __init__(self, x, y, n_feats, sw_func):
        self.x = x
        self.y = y
        self.n_feats = n_feats
        self.weights = sw_func(n_feats)
        np.clip(self.weights, 0.0, 1.0, self.weights)
        self.neighbors = []            # allows any kind of topology
        self.activity = 0            # in this implementation, constrained between [0,1]
        self.i, self.j = -1,-1        # cell index in a 2D map (only used for building the topology)

    def __str__(self):
        s = '({},{}) '.format(self.i, self.j)
        for n in self.neighbors:
            s += "[{},{}] ".format(n.i, n.j)
        s += "\n"
        return s


class SOM():
    '''Self-Organizing Map implementation.
    '''
    def __init__(self, nx, ny, n_feats, coef=0.01,
                 sw_func=np.random.random):
        '''
        :param int nx: grid size in first dimension
        :param int ny: grid size in second dimension
        :param int n_feats: Number of features for cells
        :param float coef: Learning coefficient
        :param callable sw_func: cell starting weight initialization function
        '''
        self.ncx, self.ncy = nx, ny
        self.n_feats = n_feats
        self.n_cells = nx * ny
        self.network = [Cell(0,0, n_feats, sw_func) for i in range(self.n_cells)]
        self.inputs = np.zeros(self.n_feats)
        #self.inputs = [Cell(0,0, n_feats) for i in range(self.n_feats)]
        self.coef = coef
        self.iterations = 0
        self.convergence = 0
        self.build2Dtopology()

    def __str__(self):
        s = "SOM:\n"
        for cell in self.network:
            s += str(cell)
        return s

    def reset(self):
        '''Reset SOM to random state.
        '''
        print("Resetting SOM...\n")
        self.iterations = 0
        self.convergence = 0
        for c in self.network:
            c.weights = np.random.random(c.n_feats)

    def train_cycle(self, stimuli=None):
        '''Progress SOM one iteration with generating new stimulus, calculating
        its response and training SOM based on response.
        '''
        self.iterations += 1
        self.stimulus(stimuli)
        self.response()
        self.train()

    def stimulus(self, stimuli):
        if stimuli is not None:
            self.inputs = stimuli

    def response(self):
        '''Calculate cell activities based on inputs and weights.
        '''
        for c in self.network:
            #c = self.network[i]
            # dot product of input and weight vectors, clamped to [0,1] with a sigmoid function:
            #sum = 0
            d = np.sqrt(np.sum(np.square(c.weights - self.inputs)))
            #
            #for j in range(self.n_feats):
            #    sum += (c.weights[j] - self.inputs[j].activity)**2
            #d = np.sqrt(sum)
            c.activity = 1 - _sigmoid(d)

    def train(self):
        '''Train SOM with current cell activity.
        '''
        amax = -1
        best = None
        for c in self.network:
            if c.activity > amax:
                amax = c.activity
                best = c
        # update weights
        for c in self.network: 
            c.updated = False
            c.dist = -1
        self.cell_distance(best, 0)
        self.convergence = 0.99 * self.convergence + 0.01 * amax
        self.update(best, self.coef)

    def update(self, c, coef):
        '''Update cell weights by propagating from winner to neighborhood up to
        level steps away.
        '''
        if c.updated:
            return
        if c.dist < 0:
            return
        dif = self.inputs - c.weights
        c.weights = c.weights + (dif * (coef / (c.dist + 1)))
        #for j in range(self.n_feats):
        #    dif = self.inputs[j].activity - c.weights[j]
        #    c.weights[j] += coef * dif
        c.updated = True
        for neighbor in c.neighbors:
            self.update(neighbor, coef)

    def build1Dtopology(self, draw_scale=5):
        for i in range(self.n_cells):
            c = self.network[i]
            c.x = draw_scale * i
            c.y = 30
            if i == 0: c.neighbors.append(self.network[1])
            elif i < self.n_cells-1:
                c.neighbors.append(self.network[i-1])
                c.neighbors.append(self.network[i+1])
            else: c.neighbors.append(self.network[i-1])

    def build2Dtopology(self, scale=20):
        '''Build topology for visual purposes.

        :param int scale: (drawing) scale for cells
        '''
        for j in range(self.ncy):
            for i in range(self.ncx):
                k = i + j*self.ncx
                c = self.network[k]
                c.x = scale * i + 100
                c.y = scale * j + 150
                c.i, c.j = i, j
                if i == 0:
                    c.neighbors.append(self.network[k+1])
                elif i < self.ncx-1:
                    c.neighbors.append(self.network[k-1])
                    c.neighbors.append(self.network[k+1])
                else:
                    c.neighbors.append(self.network[k-1])

                if j == 0:
                    c.neighbors.append(self.network[k+self.ncx])
                elif j < self.ncy-1:
                    c.neighbors.append(self.network[k-self.ncx])
                    c.neighbors.append(self.network[k+self.ncx])
                else:
                    c.neighbors.append(self.network[k-self.ncx])

    def cell_distance(self, cur_cell, depth):
        '''Calculate network distance from the current cell.
        '''
        if cur_cell.dist >= 0:
            return
        if depth > 2:
            return
        cur_cell.dist = depth
        for neighbor in cur_cell.neighbors:
            self.cell_distance(neighbor, depth+1)

    def distance(self, stimuli):
        '''Get euclidean distance to the closest Cell for stimuli.
        '''
        s = stimuli
        if len(stimuli.shape) > 1:
            s = stimuli.flatten()
        closest = len(s)
        for c in self.network:
            dist =  np.sqrt(np.sum(np.square(s - c.weights)))
            if dist < closest:
                closest = dist
        return closest


class RGB_SOM(SOM):
    def stimulus(self, stimuli):
        Pblack = RGB_Color(0,0,0)
        Pred = RGB_Color(1,0,0)
        Pgreen = RGB_Color(0,1,0)
        Pblue = RGB_Color(0,0,1)
        Pyellow = RGB_Color(1,1,0)
        Pcyan = RGB_Color(0,1,1)
        Pmagenta = RGB_Color(1,0,1)
        Pwhite = RGB_Color(1,1,1)
        Pgrey = RGB_Color(0.5,0.5,0.5)

        p = np.random.uniform(0,1)
        if p < 0.1: c = Pblack
        elif p < 0.2: c = Pred
        elif p < 0.3: c = Pgreen
        elif p < 0.4: c = Pblue
        elif p < 0.5: c = Pyellow
        elif p < 0.6: c = Pcyan
        elif p < 0.7: c = Pmagenta
        elif p < 0.8: c = Pwhite
        else: c = Pgrey

        self.inputs = c.rgb + np.random.uniform(-0.1, 0.1, c.rgb.shape)
        np.clip(self.inputs, 0.0, 1.0, self.inputs)
        #self.inputs[0].activity = c.r
        #self.inputs[1].activity = c.g
        #self.inputs[2].activity = c.b

        #for i in range(self.n_feats):        # randomize and clamp
        #    self.inputs[i].activity += np.random.uniform(-0.1, 0.1)
        #    if self.inputs[i].activity < 0:
        #        self.inputs[i].activity = 0
        #    if self.inputs[i].activity > 1:
        #        self.inputs[i].activity = 1


class RGB_Color():
    '''Color type with components in range (0,1).
    '''
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b
        self.rgb = np.array([r, g, b])


class ImageSOM(SOM):
    def __init__(self, nx, ny, n_feats, sw_func, coef=0.1):
        super().__init__(nx, ny, n_feats, coef, sw_func)
        self.images = self.read_images()
        self.img_size = int(np.sqrt(n_feats))

    def read_image(self, filename):
        from scipy import misc
        img = misc.imread(filename)
        temp = np.asarray(img, dtype=np.float)
        img = temp / 255.0
        return img

    def read_images(self):
        import os
        img_folder = 'test_imgs'
        img_paths = ("spiro2.png","spiro1.png","haba.png","lenna.png","teapot.png","bunny.png")
        images = []
        for s in img_paths:
            path = os.path.join(img_folder, s)
            images.append(self.read_image(path))
        return images

    def stimulus(self, stimuli):
        if stimuli is None:
            if not hasattr(self, 'images'):
                self.images = self.read_images()
            p = np.random.uniform(0,1)
            index = int(p * len(self.images))
            stimuli = self.images[index].flatten()
            stimuli = stimuli + np.random.uniform(-0.1, 0.1, stimuli.shape)
            np.clip(stimuli, 0.0, 1.0, self.inputs)
        else:
            self.inputs = stimuli

    def cell_as_image(self, c):
        return c.weights.reshape([self.img_size, self.img_size])

    def get_as_image(self):
        img = np.zeros([self.ncx*self.img_size, self.ncy*self.img_size])
        for y in range(self.ncy):
            for x in range(self.ncx):
                c = self.network[y*self.ncy + x]
                cimg = self.cell_as_image(c)
                img[self.img_size*x:self.img_size*(x+1),
                    self.img_size*y:self.img_size*(y+1)] = cimg
        return img


def _sigmoid(a):
    s = 2 * np.arctan(a) / np.pi
    return s


if __name__ == "__main__":
    #som = RGB_SOM(10, 10, 3)
    #gui = ColorSOM_GUI(som)
    #gui.run()
    som = ImageSOM(6, 6, 32*32, np.random.random, 0.1)
    gui = ImageSOM_GUI(som)
    gui.run()