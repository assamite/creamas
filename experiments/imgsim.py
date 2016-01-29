'''
Testing (binary) image similarity measures with rotated spirographss.
'''
from scipy import misc, ndimage
import numpy as np
from matplotlib import pyplot as plt

from spiro import give_dots


rot = lambda theta: np.array([[np.cos(theta), -np.sin(theta)],
                              [np.sin(theta),  np.cos(theta)]])

rot_matrices = [rot((i/360.0) * np.pi * 2) for i in range(0, 360)]


def rotations(dots, angles):
    rdots = []
    for a in angles:
        rdots.append(np.dot(dots, rot_matrices[a]))
    return rdots


def img_from_dots(dots):
    ddots = np.around(dots)
    unidots = np.vstack({tuple(row) for row in ddots})
    img = np.ones([500, 500])
    for x,y in unidots:
        img[x, y] = 0.0
    return img


def read_images(imgs):
    return [misc.imread(img, flatten=True) for img in imgs]


def calc_dists(imgs, names):
    sz = [len(imgs), len(imgs)]
    m = imgs[0].shape[0] * imgs[0].shape[1]
    edd = np.zeros(sz)
    ftd = np.zeros(sz)
    for i in range(len(imgs)):
        img1 = imgs[i]
        ftimg1 = np.fft.fft2(img1, norm='ortho')
        ftimg1[0, 0] = 0.0
        for j in range(i+1, len(imgs)):
            img2 = imgs[j]
            ftimg2 = np.fft.fft2(img2, norm='ortho')
            ftimg2[0, 0] = 0.0
            edd[i, j] = edd[j, i] = ed(img1, img2)
            ftd[i, j] = ftd[j, i] = np.real(ft(img1, img2))

    return edd, ftd


def ed(img1, img2):
    '''Euclidean distance between two 2d matrices.'''
    d = img1 - img2
    dp = np.square(d)
    s = np.sum(dp)
    return np.sqrt(s)


def ft(img1, img2):
    '''Euclidean distance between the Fourier transforms of two 2d matrices.'''
    ftimg1 = np.fft.fft2(img1, norm='ortho')
    #plt.imshow(np.abs(ftimg1), interpolation='nearest')
    #plt.show()
    #print(ftimg1)
    ftimg2 = np.fft.fft2(img2, norm='ortho')
    #plt.imshow(np.abs(np.fft.fftshift(ftimg2)), interpolation='nearest')
    #plt.show()
    return ed(ftimg1, ftimg2)


def cart2pol(dots):
    '''Convert Cartesian coordinates to polar coordinates.'''
    R = np.sqrt(np.sum(np.square(dots), axis=1))
    thetas = np.arctan2(dots[:,0], dots[:,1])
    ret = np.vstack([R, thetas])
    return ret.T


def heatmap(data, names):
    fig, ax = plt.subplots()
    hm = ax.pcolor(data, cmap=plt.cm.viridis)
    ax.set_xticks(np.arange(data.shape[0])+0.5, minor=False)
    ax.set_yticks(np.arange(data.shape[1])+0.5, minor=False)
    ax.invert_yaxis()
    ax.xaxis.tick_top()
    ax.set_xticklabels(names, minor=False)
    ax.set_yticklabels(names, minor=False)
    cbar = plt.colorbar(hm)
    plt.xticks(rotation=90)
    plt.show()


def test():
    dots = np.array(list(give_dots(200,140,160, spins = 50)))
    rots = np.arange(0, 360, 50)
    rdots = rotations(dots, rots)
    names = [("img1-{:0>3}").format(r) for r in rots]
    pdots = [r + 250 for r in rdots]
    dots2 =  np.array(list(give_dots(190,130,170, spins = 50)))
    rots2 = np.arange(0, 360, 45)
    rdots2 = rotations(dots2, rots2)
    names2 = [("img2-{:0>3}").format(r) for r in rots2]
    pdots2 = [r + 250 for r in rdots2]
    alldots = pdots + pdots2
    allnames = names + names2
    imgs = []
    for i in range(len(alldots)):
        img = img_from_dots(alldots[i])
        imgs.append(img)

    edd, ftd = calc_dists(imgs, allnames)
    heatmap(edd, allnames)




if __name__ == '__main__':
    test()