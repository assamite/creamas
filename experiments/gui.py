'''
..py:module:: gui
    :platform: Unix

Various graphical user interface functions. Mostly implemented with tk.
'''

#
#    colorsom.py
#
#    by Tassu Takala 2016
#
#    an implementation of Self Organizing Map (SOM), including
#    wrapper for Processing grahics functions in Python
#
#    color demo as in http://computationalcreativity.net/iccc2015/proceedings/11_2Takala.pdf
# 
#    interactive part based on: 
#    https://docs.python.org/3/library/tk.html
#    http://www.tkdocs.com/tutorial/canvas.html
#

from tkinter import Canvas, Tk, N, W, E, S

import math
import time

class SOM_GUI():

    ########     implementation of some most important Processing functions     #######

    def __init__(self, som, w=800, h=500):
        self.PI = math.pi
        self.Ph = 100
        self.Pbgcolor = "grey"
        self.Pstrokecolor = "black"
        self.Pfillcolor = "white"
        self.Pstroke = True
        self.Pfill = False
        self.Ploop = False
        self.Pwidth = 800
        self.Pheight = 500

        # current mouse position
        self.mouseX, self.mouseY = 0, 0
        # previous mouse position
        self.pmouseX, self.pmouseY = 0, 0
        self.mousePressed = False

        self.CORNER = 0        # redo with enumeration!!!
        self.CENTER = 1
        self.Pmode = self.CENTER    # default here -- using the same for rects and ellipses!

        self.som = som
        self.Pwidth, self.Pheight = w, h
        self.root = Tk()
        self.canvas = Canvas(self.root, width=self.Pwidth, height=self.Pheight,
                             bg=self.Pbgcolor)
        self.canvas.grid(column=0, row=0, sticky=(N, W, E, S))
        self.canvas.bind("<Button-1>", self.buttonDown)
        self.canvas.bind("<ButtonRelease>", self.buttonUp)
        self.canvas.bind("<Motion>", self.updateMouse)
        self.canvas.bind("<B1-Motion>", self.updateMouse)
        self.trains_in_loop = 100

    def run(self):
        self.Ploop = True
        if self.Ploop:
            self.root.after(50, self.draw_loop)
        self.root.mainloop()

    def noLoop(self):
        self.Ploop = False

    def background(self, r, g, b):
        canvascolor = '#%02x%02x%02x' % (r, g, b)  # encode rgb color to hex
        self.canvas.config(background=canvascolor)

    def clear(self):
        self.canvas.delete("all")

    def stroke(self, r, g, b):
        self.Pstroke = True
        self.Pstrokecolor = '#%02x%02x%02x' % (r, g, b)  # encode rgb color to hex

    def noStroke(self):
        self.Pstroke = False

    def fill(self, r, g, b):
        self.Pfill = True
        self.Pfillcolor = '#%02x%02x%02x' % (r, g, b)  # encode rgb color to hex

    def noFill(self):
        self.Pfill = False

    def rectMode(self, m):
        self.Pmode = m

    def line(self, x1, y1, x2, y2):
        if self.Pstroke:
            self.canvas.create_line((x1, y1, x2, y2), fill=self.Pstrokecolor)

    def rect(self, x, y, w, h):
        if self.Pmode == self.CENTER:
            x, y = x-w/2, y-h/2
        # CORNER mode as default:
        r = self.canvas.create_rectangle(x, y, x+w, y+h)
        if self.Pfill:
            self.canvas.itemconfig(r, fill=self.Pfillcolor)
        if self.Pstroke:
            self.canvas.itemconfig(r, outline=self.Pstrokecolor)
        else:
            self.canvas.itemconfig(r, outline=self.Pfillcolor)    # NOT QUITE RIGHT...

    def ellipse(self, cx, cy, w, h):
        if self.Pmode == self.CORNER:
            cx,cy = cx-w/2, cy-h/2
        N = int((w + h) / 4)
        if N < 4:
            N = 4
        r1 = w / 2
        r2 = h / 2
        alpha = 0
        delta = 2 * math.pi / N
        px = cx + r1
        py = cy
        for n in range(N):
            alpha += delta
            x = cx + r1 * math.cos(alpha)
            y = cy + r2 * math.sin(alpha)
            self.line(px,py,x,y)
            px = x
            py = y

    def draw_loop(self):
        self.draw()
        t=time.clock()
        for x in range(self.trains_in_loop):
            self.som.train_cycle(None)
        t2 = time.clock()
        print("Training time ({} steps): {}".format(self.trains_in_loop, t2-t))
        self.root.after(50, self.draw_loop)

    def _loc(self, c, dim):
        return 300 * c.weights[dim]

    def mousePressed(self, event):
        self.som.reset

    def updateMouse(self, event):
        self.pmouseX = self.mouseX
        self.pmouseY = self.mouseY
        self.mouseX = event.x
        self.mouseY = event.y

    def buttonDown(self, event):
        self.mousePressed = True
        self.som.reset()

    def buttonUp(self, event):
        self.mousePressed = False


class ColorSOM_GUI(SOM_GUI):
    '''GUI for RGB color SOM.
    '''
    def draw_cell(self, cell, draw_scale=20):
        '''Draw cell in its place.
        '''
        r = (int)(255 * cell.weights[0])
        g = (int)(255 * cell.weights[1])
        b = (int)(255 * cell.weights[2])
        self.stroke(0,0,0)
        self.fill(r,g,b)
        self.rect(cell.x, cell.y, draw_scale, draw_scale)

    def draw_connections(self):
        for c in self.som.network:
            for k in range(self.som.n_feats):
                self.line(c.x, c.y, self.som.inputs[k].x, self.som.inputs[k].y)
        for c in self.som.network:
            for nc in c.neighbors:
                nc = c.neighbors[k]
                self.line(c.x, c.y, nc.x, nc.y)

    def draw_response(self, ix, iy):
        '''Draw SOM's response.

        :param ix: Weight vector index
        :param iy: Weight vector index
        '''
        cx, cy = 400, 100
        for c in self.som.network:
            xx = self._loc(c,ix) + cx
            yy = self._loc(c,iy) + cy
            self.ellipse(xx,yy, 10,10)
            for k in range(len(c.neighbors)):
                nc = c.neighbors[k]
                self.line(xx, yy, self._loc(nc, ix)+cx, self._loc(nc, iy)+cy)
        # draw a box outline
        self.noFill()
        self.stroke(0,0,255)
        self.rectMode(self.CORNER)
        self.rect(cx,cy,300,300)
        self.rectMode(self.CENTER)


    def draw(self):
        '''Draw SOM.
        '''
        self.clear()
        self.background(255,255,255)

        ## draw the network
        for n in self.som.network:
            self.draw_cell(n)
        #for n in self.som.inputs:
        #    self.draw_cell(n)
        #self.draw_connections()    # display the network topology
        #self.draw_response(0, 2)    # show how cell weights develop during training


class ImageSOM_GUI(SOM_GUI):

    def __init__(self, som, w=800, h=600):
        super().__init__(som, w, h)
        self.selected_cell = -1
        self.img_size = int(self.som.img_size)
        self.pix_size = 2
        self.locate2Dnetwork()

    def locate2Dnetwork(self):
        spacing = self.pix_size * self.img_size + 10
        for j in range(self.som.ncy):
            for i in range(self.som.ncx):
                k = i + j*self.som.ncx
                c = self.som.network[k]
                c.x = spacing * i + 30
                c.y = spacing * j + 30

    def draw_cell(self, c):
        sz = self.pix_size * self.img_size
        self.show_image(c.weights, c.x, c.y, sz)

    def show_stimulus(self):
        # used for testing picsom
        self.show_image(self.som.inputs, 30, 500, self.pix_size * self.img_size)

    def show_image(self, img, x, y, scale):
        pix = int(scale / self.img_size)
        for i in range(self.img_size):
            for j in range(self.img_size):
                k = i + j * self.img_size
                w = img[k]
                b = int(255*w)
                self.fill(b, b, b)
                self.noStroke()
                xx = x + pix * i
                yy = y + pix * j
                self.rect(xx,yy, pix,pix)
        self.stroke(0, 0, 0)
        self.noFill()
        self.rectMode(self.CORNER)
        scale = pix * self.img_size
        self.rect(x, y, scale, scale)

    def show_input_images(self, scale):
        for n in range(len(self.som.images)):
            x = (scale+10) * (n+2)
            y = 500
            self.show_image(self.som.images[n].flatten(), x, y, scale)

    def draw(self):
        self.clear()
        self.background(255,255,255)
        self.show_input_images(self.pix_size * self.img_size)
        self.show_stimulus()
        ## draw the network
        for c in self.som.network:
            self.draw_cell(c)
        for x in range(100): 
            self.som.train_cycle()
        print(self.som.convergence)