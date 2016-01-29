'''
.. py:module:: gifgen
    :platform: Unix

Simple gif-generator.
'''
import os
import shlex
import subprocess

from PIL import Image, ImageDraw
import numpy as np

rotate = lambda p,a: np.array([[np.cos(a), -np.sin(a)], [np.sin(a),  np.cos(a)]]) @ p


def draw(func, A, X, width=512, height=512):
    cx, cy = width/2, height/2
    img = Image.new('RGB', (width, height), 'black')
    draw = ImageDraw.Draw(img)
    Y = func(X)
    P = [np.array([x, y]) for x, y in zip(X, Y)]
    for a in A:
        for p in P:
            point = rotate(p, a)
            cp = [point[0]+cx, point[1]+cy]
            draw.point(cp, fill='white')
    return img


def make_gif(img_folder, ext):
    cmd = 'convert -delay 0 -loop 0 *.{} test.gif'.format(ext)
    curcwd = os.getcwd()
    os.chdir(img_folder)
    sh_cmd = shlex.split(cmd)
    proc = subprocess.Popen(sh_cmd)
    proc.communicate()
    proc.wait()
    os.chdir(curcwd)


def create_images(steps=10, img_folder='imgs'):
    if not os.path.exists(img_folder):
        os.makedirs(img_folder)
    img_name = 'test{:0>'+str(len(str(steps)))+'}.png'
    A = np.linspace(0, 2*np.pi, 13)[:-1]
    X = np.linspace(0, 200, 41)

    for i in range(steps):
        func = lambda x: np.sin(np.radians(x+(i*1.2))*10)*(30.0*np.sin(np.radians(i*2.0)))*(x/70.0)
        B = A + np.radians(i*0.5)
        X = np.linspace(0, 150+i%100, 41)
        img = draw(func, B, X)
        img_path = os.path.join(img_folder, img_name.format(i))
        img.save(img_path, format='png')



if __name__ == '__main__':
    create_images(1000)
