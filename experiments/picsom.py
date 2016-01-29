#
#	picsom.py
#
#	by Tassu Takala 2016
#
#	based on colorsom.py
#	- added reading of pictures (number tables) from file and using as SOM input
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

def fill(r,g,b):
	global Pfill, Pfillcolor
	Pfill = True
	Pfillcolor = '#%02x%02x%02x' % (r, g, b)  # encode rgb color to hex

def noStroke():
	global Pstroke
	Pstroke = False

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
	else: canvas.itemconfig(r, fill='')
	if Pstroke: canvas.itemconfig(r, outline=Pstrokecolor)
	else: canvas.itemconfig(r, width=0)

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

def mousePressedF():
	pass

##########################	SOM written in Python	####################

NCX,NCY = 6,6		# number of rows and columns in the (2D) SOM
NCELLS = NCX*NCY	# total number of neurons
NFEATURES = 3		# input vector length

COEF = 0.1			# learning speed in training the map
					#   This should depend on network and input dimensions (and dynamically on convergence)
					#   --> thus a parameter for train()/traincycle() method, instead of constant

class Cell:
	def __init__(self):
		self.x, self.y = 0,0  # xx,yy = cell location on the display (to be assigned later)
		self.weights = [random.random() for k in range(NFEATURES)]
		self.neighbors = []			# allows any kind of topology
		self.activity = 0			# in this implementation, constrained between [0,1]
		self.i, self.j = -1,-1		# cell index in a 2D map (only used for building the topology)

	def display(self):
		global IMGSIZE, PIXSIZE
		cellsize = 2*32
		cellsize = PIXSIZE * IMGSIZE
		"""
		# this is for colorsom:
		r = (int)(255 * self.weights[0])
		g = (int)(255 * self.weights[1])
		b = (int)(255 * self.weights[2])
		stroke(0,0,0)
		fill(r,g,b)
		rect(self.x,self.y, DRAWSCALE,DRAWSCALE)
		"""
		showimage(self.weights,self.x,self.y, cellsize)  #  for picsom testing

	def printme(self):	# for debugging
#		print( '(', self.x, self.y , ')', end=' ')
		print( '[', self.i, self.j , ']', end=' ')
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
		network = [Cell() for i in range(NCELLS)]
		inputs = [Cell() for i in range(NFEATURES)]
#	any topology is possible - these two are implemented:
#		build1Dtopology(network)
#		locate1Dnetwork(network)	# just for display purposes
		build2Dtopology(network)		
		locate2Dnetwork(network)	# just for display purposes - should be in the application module (setup) !
		locateinputs(inputs)	# just for display purposes
		self.reset()		

	def reset(self):
		global convergence
		convergence = 0
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
	for i in range(NCELLS):
		c = network[i]
		if i == 0: c.neighbors.append(network[1])
		elif i < NCELLS-1:
			c.neighbors.append(network[i-1])
			c.neighbors.append(network[i+1])
		else: c.neighbors.append(network[i-1])	

def build2Dtopology(network):
	for j in range(NCY):
		for i in range(NCX):
			k = i + j*NCX
			c = network[k]
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

def locate1Dnetwork(network):  	# just for display purposes - should be in the application module!
	spacing = 5
	for i in range(NCELLS):
		c = network[i]
		c.x = spacing * i
		c.y = 30

def locate2Dnetwork(network):  	# just for display purposes - should be in the application module!
	global IMGSIZE, PIXSIZE
	spacing = PIXSIZE * IMGSIZE + 10
	for j in range(NCY):
		for i in range(NCX):
			k = i + j*NCX
			c = network[k]
			c.x = spacing * i + 30
			c.y = spacing * j + 30

def locateinputs(inputs):    # map input cells on the screen  - should be in the application module!
	spacing = PIXSIZE * IMGSIZE + 10
	for i in range(NFEATURES):
		inputs[i].x = spacing * i + 100
		inputs[i].y = 500
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
	global convergence
	# find the winner
	amax = -1
	best = -1
	for i in range(NCELLS):
		if network[i].activity > amax:
			amax = network[i].activity
			best = i
	# update weights
	for i in range(NCELLS):		# variables to be used in update()
		network[i].updated = False
		network[i].dist = -1
	c = network[best]
	netdistance(c, 0)
	# printdist()
	convergence = 0.99 * convergence + 0.01 * amax
	update(c, COEF)

####  Simo: alla oleva lisätty, koska aikaisempi update() -versio ei toiminut oikein
####		(paitsi jos oppimisteho coef pidettiin vakiona rekursiivisessa kutsussa)

def netdistance(c, d):	# calculate network distance from the winner
	if c.dist >= 0: return
	if(d > 2): return
	c.dist = d
	for j in range(len(c.neighbors)): netdistance(c.neighbors[j], d+1)

def printdist():	# for debugging
	for i in range(NCX):
		for j in range(NCY):
			k = i + NCX * j
			print(network[k].dist,"\t",end='')
		print('\n')
	print("---------")

def update(c, coef):		# propagate from winner to neighborhood up to level marked by distance
	if(c.updated): return
#	if(c.dist > 2) coef = -coef	# experiment: negative learning if far from winner
	if(c.dist < 0): return
	for j in range(NFEATURES):
		dif = inputs[j].activity - c.weights[j]
		c.weights[j] += dif * coef / (c.dist + 1)
	c.updated = True
	for j in range(len(c.neighbors)): update(c.neighbors[j], coef)

def sigmoid(a):		# actually only the positive half is used
	s = 2 * math.atan(a) / PI
	return s

##########################	this part is unique for each SOM application:	####################

###  here a demo with colors or pictures as inputs

class Pcolor:	#  color type with components in range (0,1)
	def __init__(self, rr,gg,bb):
		self.r = rr
		self.g = gg
		self.b = bb

def stimulus():
	p = random.uniform(0,1)		# for selecting input alternative
	"""
	##  stimulus alternatives for colorsom:
	Pblack = Pcolor(0,0,0)
	Pred = Pcolor(1,0,0)
	Pgreen = Pcolor(0,1,0)
	Pblue = Pcolor(0,0,1)
	Pyellow = Pcolor(1,1,0)
	Pcyan = Pcolor(0,1,1)
	Pmagenta = Pcolor(1,0,1)
	Pwhite = Pcolor(1,1,1)
	Pgrey = Pcolor(0.5,0.5,0.5)

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
	"""
	
	#######  this part is for picsom:
	global images
	'''
	## some synthetic inputs for initial testing...
	
	for n in range(NFEATURES):
		### horizontal line images
		if n < 4 and p < 0.25: val = 1
		elif n >= 4 and n < 8 and p > 0.25 and p < 0.5: val = 1
		elif n >= 8 and n < 12 and p > 0.5 and p < 0.75: val = 1
		elif n >= 12 and p > 0.75: val = 1
		else: val = 0
		### squares
		j = n % 4
		i = n // 4
#		print('(',i,j,')',end=' ')

		if i < 2 and j < 2 and p < 0.25: val = 1
		elif i < 2 and j >= 2 and p > 0.25 and p < 0.5: val = 1
		elif i >= 2 and j < 2 and p > 0.5 and p < 0.75: val = 1
		elif i >= 2 and j >= 2 and p > 0.75: val = 1
		else: val = 0
#		if j == 0: print('\n')
#		print(val,end=' ')

	for n in range(NFEATURES):
		inputs[n].activity = val
		inputs[n].activity += random.uniform(-0.1,+0.1)
		if inputs[n].activity < 0: inputs[n].activity = 0
		if inputs[n].activity > 1: inputs[n].activity = 1
#	print("--------")
	'''
	index = int(p * len(images))
#	print(index)
	for n in range(NFEATURES):
		inputs[n].activity = images[index][n]
		inputs[n].activity += random.uniform(-0.1,+0.1)
		if inputs[n].activity < 0: inputs[n].activity = 0
		if inputs[n].activity > 1: inputs[n].activity = 1

def showstimulus():
	# used for testing picsom
	vec = []
	for n in range(len(inputs)):
		vec.append(inputs[n].activity)
	showimage(vec,30,500, PIXSIZE*IMGSIZE)

IMGSIZE = 0		#  for picsom, defined when reading image file
PIXSIZE = 1		#  size of one pixel in SOM visualization (minimum = 1, tuned below according to image size)

def readimages_w():		### initial testing (with different image sizes): all images in one workfile
	filename = "workfile8.txt"
	global IMGSIZE, PIXSIZE
	f = open(filename, 'r')

	images = []
	img = []
	n = 0
	for line in f:
#		print(line)
		list = line.split( )
#		print(list)
		if len(list) == 0: continue
		#  take image size from the first non-empty line of the image file
		if IMGSIZE == 0: IMGSIZE = len(list)
		for s in list:
			num = int(s)
#			print(s,'=',num)
			img.append(num/255)
		n = n + 1
		if n == IMGSIZE:	## end of image
			images.append(img)
			img = []
			n = 0
	PIXSIZE = 2*32 / IMGSIZE
	if PIXSIZE < 1: PIXSIZE = 1
#	print("INPUUT IMAGES:", images)
	return(images)

def readimages():
	allfiles = ("spiro2.txt","spiro1.txt","haba.txt","lenna.txt","teapot.txt","bunny.txt")
	images = []
	for s in allfiles:
		images.append(read_image(s))
#	print(images)
	return(images)

def read_image(filename):		### a quick hack - not needed when agents synthesize the images
	global IMGSIZE, PIXSIZE
	f = open(filename, 'r')
	n = 0
	img = []
	for line in f:
#		print(line)
		list = line.split( )
#		print(list)
		if len(list) == 0: continue
		#  take image size from the first non-empty line of the image file
		if IMGSIZE == 0: IMGSIZE = len(list)
		for s in list:
			num = int(s)
#			print(s,'=',num)
			img.append(num/255)
		n = n + 1
	if n != IMGSIZE: print("Inconsistent image file: ",filename)
	PIXSIZE = 2*32 / IMGSIZE
	if PIXSIZE < 1: PIXSIZE = 1
	return(img)

def showimage(img,x,y,scale):
#	print(IMGSIZE," x ",IMGSIZE," = ",len(img)," : ",img)
	pix = int(scale / IMGSIZE)
	for i in range(IMGSIZE):
		for j in range(IMGSIZE):
			k = i + j * IMGSIZE
			w = img[k]
			b = (int) (255*w)
			fill(b,b,b)
			noStroke()
			xx = x + pix * i
			yy = y + pix * j
			rect(xx,yy, pix,pix)
	stroke(0,0,0)
	noFill()
	rectMode(CORNER)
	scale = pix * IMGSIZE
	rect(x,y,scale,scale)

def show_input_images(scale):
#	print(len(images)," images:")
	for n in range(len(images)):
		x = (scale+10) * (n+2)
		y = 500
		showimage(images[n],x,y,scale)

##########################	Processing style main application starts here	####################

def setup():
	global som, network, inputs, selectedcell, images
	selectedcell = -1
	size(800,600)	#  setup() must call size() exactly once before drawing anything

	images = readimages()		## testing
#	images = readimages()		## defines IMGSIZE

	inputsize = IMGSIZE * IMGSIZE
	print("image size = ",IMGSIZE)
#	som = SOM(10,10,3)
	som = SOM(6,6,inputsize)	# testing picsom
#	som.printme()	
#	noLoop()		#  if testing just the initialization

def draw():
	global convergence			## for monitoring SOM learning
	background(255,255,255)
	show_input_images(PIXSIZE*IMGSIZE)

	showstimulus()
	## draw the network
	for n in range(NCELLS): network[n].display()
#	for n in range(NFEATURES): inputs[n].display()
#	draw_connections()	# display the network topology
#	draw_response(1,2)	# show network in coordinate system of selected weights 

	t = time.clock()
	for x in range(100): traincycle()
	print("Training time ({} steps): {}".format(100, time.clock()-t))
	print(convergence)	

def mousePressedF():	# the mousePressed() function in Processing
	global som, selectedcell
#	print("SOM RESET")
#	som.reset()

#	for picsom:  locate the cell pointed with mouse (if you want to ask its properties, for example)
	DRAWSCALE = 20
	d = DRAWSCALE / 2
	for n in range(NCELLS):
		dx = mouseX - network[n].x
		dy = mouseY - network[n].y
		if (dx > -d and dx < +d and dy > -d and dy < +d):
			selectedcell = n
			break
	else: selectedcell = -1  # NaN
#	print(selectedcell)

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

def draw_response(ix,iy):	# ix,iy = weight vector indices to be used as display dimensions of the network
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

def loc(c, dim):	# mapping cell values onto the display  (called by draw_response only)
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
