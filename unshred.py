#!/usr/bin/python
from PIL import Image
import sys
import operator
import math

import numpy
import pylab

class Strip:
	def __init__(self, leftPixels, rightPixels, id):
		self.id = id
		self.leftPixels = leftPixels
		self.rightPixels = rightPixels
		
class UnShredder:
	def __init__(self, image, numStrips):
		self.image = image
		self.pixelData = image.getdata()
		self.imageWidth, self.imageHeight = image.size
		self.numStrips = numStrips
		self.stripWidth = self.imageWidth / self.numStrips
		self.strips = self.makeStrips()
		self.unshreddedImage = Image.new("RGBA", image.size)
		
		self.controlScore = self.computeControlScore()
		self.key = self.computeNeighbors()
		self.stripOrder = [0]
		self.parseKeyLeft(0)
		self.parseKeyRight(0)
		
		print self.stripOrder

	def getPixelValue(self, x,y):
		pixel = self.pixelData[y * self.imageWidth + x]
		return pixel
	
	def _getColumnOfPixelValues(self, x):
		values = []
		for i in range(self.imageHeight):
			values.append(self.getPixelValue(x,i))
		return values
		
	def makeStrips(self):
		strips = []
		for i in range(self.numStrips):
			leftPixels = self._getColumnOfPixelValues(i*self.stripWidth)
			rightPixels = self._getColumnOfPixelValues(i*self.stripWidth + self.stripWidth-1)
			strips.append(Strip(leftPixels, rightPixels, i))
		return strips
	
	def euclidDist(self,a,b):
		# given two RGB tuples, 'a' and 'b', return the scalar euclidian distance between them
		sum = reduce(lambda a,b: a+b, [math.pow(a[i]-b[i],2) for i in range(3)])
		dist = math.sqrt(sum)
		return dist

	def subtractLists(self, a, b):
		difference = math.fabs(a - b)
		return difference
		
	def computeControlScore(self):
		x_midpoint_strip = self.stripWidth/2
		a = self._getColumnOfPixelValues(x_midpoint_strip)
		b = self._getColumnOfPixelValues(x_midpoint_strip+1)
		differences = map(self.euclidDist, a, b)
		score = reduce(lambda a,b:a+b, differences)
		print "control score: ", score
		return score
		
	def computeNeighbors(self):
		key = {}

		lmax_delta = 0
		lmax_delta_id= -1
		rmax_delta = 0
		rmax_delta_id= -1
		
		# iterate over each strip
		for i in range(len(self.strips)):
			
			# store running minimum
			minScoreLeftNeighbor = sys.maxint
			minStripLeftNeighbor = -1
			minScoreRightNeighbor = sys.maxint
			minStripRightNeighbor = -1
			
			# make a copy of self.strips
			restStrips = list(self.strips)
			
			# compare 'the strip' with the rest of the strips
			print 'theStrip: ',i
			theStrip = restStrips.pop(i)
			for strip in restStrips:
			
				# find the best left neighbor
				a = theStrip.leftPixels
				b = strip.rightPixels
				differences = map(self.euclidDist, a, b)
				scoreL = reduce(lambda a,b:a+b, differences)
				if scoreL < minScoreLeftNeighbor:
					minScoreLeftNeighbor = scoreL
					minStripLeftNeighbor = strip.id			
	
				# find the best right neighbor
				a = theStrip.rightPixels
				b = strip.leftPixels
				differences = map(self.euclidDist, a, b)
				scoreR = reduce(lambda a,b:a+b, differences)
				if scoreR < minScoreRightNeighbor:
					minScoreRightNeighbor = scoreR
					minStripRightNeighbor = strip.id
			
			ldelta = minScoreLeftNeighbor - minScoreRightNeighbor
			if (ldelta > lmax_delta):
				lmax_delta = ldelta
				lmax_delta_id = i
			rdelta = minScoreRightNeighbor - minScoreLeftNeighbor
			if (rdelta > rmax_delta):
				rmax_delta = rdelta
				rmax_delta_id = i
			# set the right and left neighbor for this strip
			key[theStrip.id] = (minStripLeftNeighbor, minStripRightNeighbor)
		print "lmax_delta: %d, id: %d" %(lmax_delta,lmax_delta_id)
		print "rmax_delta: %d, id: %d" %(rmax_delta,rmax_delta_id)
		
		# update key to reflect the start and end strips
		startStrip = key[lmax_delta_id]
		key[lmax_delta_id] = ("start", startStrip[1])
		endStrip = key[rmax_delta_id]
		key[rmax_delta_id] = (endStrip[0], "end")
		print key
		return key
	
	def parseKeyLeft(self, strip):
		leftStrip, rightStrip = self.key[strip]
		print "leftStrip: ", leftStrip
		self.stripOrder.insert(0,leftStrip)
		if leftStrip == "start":
			return
		self.parseKeyLeft(leftStrip)
		
	def parseKeyRight(self, strip):
		leftStrip, rightStrip = self.key[strip]
		print "rightStrip: ", rightStrip
		self.stripOrder.append(rightStrip)
		if rightStrip == "end":
			return
		self.parseKeyRight(rightStrip)
		
	def reconstructImage(self):
		for i in range(self.numStrips):
			print "i: ",i
			order = self.stripOrder[1:-1]
			x1, y1 = self.stripWidth * order[i], 0
			x2, y2 = x1 + self.stripWidth, self.imageHeight
			source_region = self.image.crop((x1, y1, x2, y2))
			destination_point = (self.stripWidth*i, 0)
			self.unshreddedImage.paste(source_region, destination_point)
		self.unshreddedImage.save("finalResult.jpg", "JPEG")

if __name__ == "__main__":
	numStrips = 20
	image = Image.open("file.jpg")
	myUnShredder = UnShredder(image, numStrips)
	myUnShredder.reconstructImage()

	