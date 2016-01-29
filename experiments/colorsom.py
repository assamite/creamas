#
#	colorsom.py
#
#	by Tassu Takala 2016
#
#	an implementation of Self Organizing Map (SOM), including
#	wrapper for Processing grahics functions in Python
#
#	color demo as in http://computationalcreativity.net/iccc2015/proceedings/11_2Takala.pdf
# 
#	interactive part based on: 
#	https://docs.python.org/3/library/tk.html
#	http://www.tkdocs.com/tutorial/canvas.html
#

from tkinter import *
from tkinter import ttk

import math
import random
import time

######## 	some global variables (begin with 'P' when referring to Processing)    #######

PI = math.pi
Ph = 100
# Pwidth,Pheight = 100,100
Pbgcolor = "grey"
Pstrokecolor = "black"
Pfillcolor = "white"
Pstroke = True
Pfill = False

# Ploop = True	# repeating of the draw() function

CORNER = 0		# redo with enumeration!!!
CENTER = 1
Pmode = CENTER	# default here -- using the same for rects and ellipses!

######## 	implementation of some most important Processing functions     #######

def size(w,h):				##	must be called from setup(), and only once
	global root,canvas, Pwidth,Pheight
	Pwidth,Pheight = w,h
	canvas = Canvas(root, width=Pwidth, height=Pheight, bg=Pbgcolor)
	canvas.grid(column=0, row=0, sticky=(N, W, E, S))		# en tiedä mitä varten, mutta tarvitaan...
	canvas.bind("<Button-1>", buttonDown)
	canvas.bind("<ButtonRelease>", buttonUp)
	canvas.bind("<Motion>", updateMouse)
	canvas.bind("<B1-Motion>", updateMouse)

def noLoop():
	global Ploop
	Ploop = False

def background(r,g,b):
	canvas.delete("all")
	canvascolor = '#%02x%02x%02x' % (r, g, b)  # encode rgb color to hex
	canvas.config(background=canvascolor)

def stroke(r,g,b):
	global Pstroke, Pstrokecolor
	Pstroke = True
	Pstrokecolor = '#%02x%02x%02x' % (r, g, b)  # encode rgb color to hex

def noStroke():
	global Pstroke
	Pstroke = False

def fill(r,g,b):
	global Pfill, Pfillcolor
	Pfill = True
	Pfillcolor = '#%02x%02x%02x' % (r, g, b)  # encode rgb color to hex

def noFill():
	global Pfill
	Pfill = False

def rectMode(m):
	global Pmode
	Pmode = m

def line(x1,y1, x2,y2):
	if Pstroke: canvas.create_line((x1,y1, x2,y2), fill=Pstrokecolor)

def rect(x,y, w,h):
	if Pmode == CENTER:
		x,y = x-w/2, y-h/2
	# CORNER mode as default:
	r = canvas.create_rectangle(x,y, x+w,y+h)
	if Pfill: canvas.itemconfig(r, fill=Pfillcolor)
	if Pstroke: canvas.itemconfig(r, outline=Pstrokecolor)
	else: canvas.itemconfig(r, outline=Pfillcolor)	# NOT QUITE RIGHT...

def ellipse(cx,cy, w,h):
	if Pmode == CORNER:
		cx,cy = cx-w/2, cy-h/2
	N = int((w + h) / 4)
	if N < 4: N = 4
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
		line(px,py,x,y)
		px = x
		py = y

mouseX, mouseY = 0, 0
pmouseX, pmouseY = 0, 0
mousePressed = False

def updateMouse(event):
	global mouseX, mouseY, pmouseX, pmouseY
	pmouseX = mouseX
	pmouseY = mouseY
	mouseX = event.x
	mouseY = event.y

def buttonDown(event):
	global mousePressed
	mousePressed = True
	mousePressedF()

def buttonUp(event):
	global mousePressed
	mousePressed = False

def drawloop():
	# print("draw")
	draw()
	root.after(50, drawloop)



##########################	SOM written in Python	####################

NCX,NCY = 6,6		# number of rows and columns in the (2D) SOM
NCELLS = NCX*NCY	# total number of neurons
NFEATURES = 3		# input vector length
COEF = 0.01			# learning speed in training the map

class Cell:
	def __init__(self, xx, yy):		# xx,yy = cell location on the display
		self.x = xx
		self.y = yy
		self.weights = [random.random() for k in range(NFEATURES)]
		self.neighbors = []			# allows any kind of topology
		self.activity = 0			# in this implementation, constrained between [0,1]
		self.i, self.j = -1,-1		# cell index in a 2D map (only used for building the topology)

	def display(self):
		DRAWSCALE = 20
		r = (int)(255 * self.weights[0])
		g = (int)(255 * self.weights[1])
		b = (int)(255 * self.weights[2])
		stroke(0,0,0)
		fill(r,g,b)
		rect(self.x,self.y, DRAWSCALE,DRAWSCALE)

	def printme(self):	# for debugging
#		print( '(', self.x, self.y , ')', end=' ')
		print( '(', self.i, self.j , ')', end=' ')
		for k in range(len(self.neighbors)):
			nc = self.neighbors[k]
			print("[",nc.i,nc.j,"]",end=' ')
		print('\n')

class SOM:
	def __init__(self, nx,ny,nf):
		global NCX,NCY, NFEATURES, NCELLS, network, inputs
		NCX,NCY = nx,ny
		NFEATURES = nf
		NCELLS = NCX * NCY
		network = [Cell(0,0) for i in range(NCELLS)]
		inputs = [Cell(0,0) for i in range(NFEATURES)]
#	any topology is possible - these two are implemented:
#		build1Dtopology(network)
		build2Dtopology(network)		
		locateinputs(inputs)	# just for display purposes

	def reset(self):
		for n in range(NCELLS):
			c = network[n]
			for j in range(NFEATURES):
				c.weights[j] = random.random()

	def printme(self):
		print("SOM")
		for n in range(NCELLS):
			c = network[n]
			c.printme()

### these actually should be local methods in the class...

def build1Dtopology(network):
	DRAWSCALE = 5
	for i in range(NCELLS):
		c = network[i]
		c.x = DRAWSCALE * i
		c.y = 30
		if i == 0: c.neighbors.append(network[1])
		elif i < NCELLS-1:
			c.neighbors.append(network[i-1])
			c.neighbors.append(network[i+1])
		else: c.neighbors.append(network[i-1])	

def build2Dtopology(network):
	DRAWSCALE = 20
	for j in range(NCY):
		for i in range(NCX):
			k = i + j*NCX
			c = network[k]
			c.x = DRAWSCALE * i + 50
			c.y = DRAWSCALE * j + 50
			c.i, c.j = i,j
			if i == 0: c.neighbors.append(network[k+1])
			elif i < NCX-1:
				c.neighbors.append(network[k-1])
				c.neighbors.append(network[k+1])
			else: c.neighbors.append(network[k-1])

			if j == 0: c.neighbors.append(network[k+NCX])
			elif j < NCY-1:
				c.neighbors.append(network[k-NCX])
				c.neighbors.append(network[k+NCX])
			else: c.neighbors.append(network[k-NCX])
#			print(k,i,j,len(c.neighbors))

def locateinputs(inputs):
	DRAWSCALE = 50
	for i in range(NFEATURES):     # map input cells on the screen
		inputs[i].x = DRAWSCALE * i + 100
		inputs[i].y = 300
		for k in range(NFEATURES):	# associate input indices to the (dummy) weights
			if i==k: inputs[i].weights[k] = 1
			else: inputs[i].weights[k] = 0

def traincycle():
	stimulus()
	response()
	train()

def response():  # calculate cell activities based on inputs and weights
	for i in range(NCELLS):
		c = network[i]
		# dot product of input and weight vectors, clamped to [0,1] with a sigmoid function:
		sum = 0
		for j in range(NFEATURES): sum += (c.weights[j] - inputs[j].activity)**2
		d = math.sqrt(sum)
		c.activity = 1 - sigmoid(d)

def train():
	# find the winner
	amax = -1
	best = -1
	for i in range(NCELLS):
		if network[i].activity > amax:
			amax = network[i].activity
			best = i
	# update weights
	for i in range(NCELLS): network[i].updated = False
	c = network[best]
	update(c, COEF, 0)

def update(c, coef, level):		# propagate from winner to neighborhood up to level steps away
	if(c.updated): return
#	if(level > 2) coef = -coef	# experiment: negative learning if far from winner
	if(level > 2): return
	for j in range(NFEATURES):
		dif = inputs[j].activity - c.weights[j]
		c.weights[j] += coef * dif
	c.updated = True
	for j in range(len(c.neighbors)): update(c.neighbors[j], coef/2, level+1)

def sigmoid(a):
	s = 2 * math.atan(a) / PI
	return s

###  this part is unique for each SOM application: here a demo with colors as inputs

class Pcolor:	#  color type with components in range (0,1)
	def __init__(self, rr,gg,bb):
		self.r = rr
		self.g = gg
		self.b = bb

def stimulus():
	Pblack = Pcolor(0,0,0)
	Pred = Pcolor(1,0,0)
	Pgreen = Pcolor(0,1,0)
	Pblue = Pcolor(0,0,1)
	Pyellow = Pcolor(1,1,0)
	Pcyan = Pcolor(0,1,1)
	Pmagenta = Pcolor(1,0,1)
	Pwhite = Pcolor(1,1,1)
	Pgrey = Pcolor(0.5,0.5,0.5)
	
	p = random.uniform(0,1)
	if p < 0.1: c = Pblack
	elif p < 0.2: c = Pred
	elif p < 0.3: c = Pgreen
	elif p < 0.4: c = Pblue
	elif p < 0.5: c = Pyellow
	elif p < 0.6: c = Pcyan
	elif p < 0.7: c = Pmagenta
	elif p < 0.8: c = Pwhite
	else: c = Pgrey

	inputs[0].activity = c.r
	inputs[1].activity = c.g
	inputs[2].activity = c.b

	for i in range(NFEATURES):		# randomize and clamp
		inputs[i].activity += random.uniform(-0.1,+0.1)
		if inputs[i].activity < 0: inputs[i].activity = 0
		if inputs[i].activity > 1: inputs[i].activity = 1

##########################	Processing style main application starts here	####################

def setup():
	global som, network, inputs
	size(800,500)	#  setup() must call size() exactly once before drawing anything
	som = SOM(10,10,3)
#	som.printme()	
#	noLoop()		#  if testing just the initialization

def draw():
	background(255,255,255)

	## draw the network
	for n in range(NCELLS): network[n].display()
	for n in range(NFEATURES): inputs[n].display()
#	draw_connections()	# display the network topology
	draw_response(1,2)	# show how cell weights develop during training

	t = time.clock()
	for x in range(200): traincycle()
	print (time.clock()-t)

def mousePressedF():	# the mousePressed() function in Processing
	global som
	print("SOM RESET")
	som.reset()

def draw_connections():
	for n in range(NCELLS):
		c = network[n]
		for k in range(NFEATURES):
			line(c.x, c.y,	inputs[k].x,inputs[k].y)
	for n in range(NCELLS):
		c = network[n]
		for k in range(len(c.neighbors)):
			nc = c.neighbors[k]
			line(c.x,c.y, nc.x,nc.y)	

def draw_response(ix,iy):	# ix,iy = weight vector indices to be used as display dimensions
	cx,cy = 400,100
	for n in range(NCELLS):
		c = network[n]
		xx = loc(c,ix) + cx
		yy = loc(c,iy) + cy
		# print(xx, yy)
		ellipse(xx,yy, 10,10)
		for k in range(len(c.neighbors)):
			nc = c.neighbors[k]
			line(xx,yy, loc(nc,ix)+cx, loc(nc,iy)+cy)
	# draw a box outline
	noFill()
	stroke(0,0,255)
	rectMode(CORNER)
	rect(cx,cy,300,300)
	rectMode(CENTER)

def loc(c, dim):	# mapping cell values onto the display
	return 300 * c.weights[dim]

#################    ...and last comes the Python Tk main    ####################

if __name__=='__main__':
	global Pwidth,Pheight,Ploop
	root = Tk()
	Ploop = True
	setup()
	if Ploop: root.after(50, drawloop)	# repeat every 50 ms (frame rate = 20, if computer fast enough)
	root.mainloop()

###########################################################################
