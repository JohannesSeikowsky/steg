from PIL import Image
import time
import logging
from random import randint

################################################################################
# Classes
################################################################################

class text:
  def __init__(self, path):
    f = open(path, 'r')
    self.raw = f.read()
    self.words = self.raw.split(' ') # Split the words over spaces.

class image:
  def __init__(self, path):
    self.image = Image.open(path)
    self.width = self.image.width 
    self.height = self.image.height

# Class to get the text into an image. Both are specified and an end product 
#   is saved.
class makeSteganograph(text, image):
  def __init__(self, textPath, imagePath):
    self.textPath       = textPath
    self.imagePath      = imagePath
    self.text           = text(textPath)
    self.image          = image(imagePath)
    self.serialisedText = stringToInt(self.text.raw)
    self.maxTextValue   = max(self.serialisedText)
    self.minTextValue   = min(self.serialisedText)
    self.nbPixelsNeeded = len(self.serialisedText)
    self.originalPixels = getPixelValues(self.image.image)
    self.picDim         = self.image.image.size
    self.possible       = self.stegnoPossible()
    self.imgFilePath    = imageIO
    self.textFilePath   = textIO

  def stegnoPossible(self):
    nbPixels = self.picDim[0]*self.picDim[1]
    needed = self.nbPixelsNeeded
    if needed > nbPixels:
      return False
    else:
      return True

  def length(self):
    chars = len(self.text.raw)
    wrds = len(self.text.words)
    w,h = self.image.image.size
    print("Number of characters: \t\t"        + str(chars)  + "\n"
          "Number of words: \t\t"             + str(wrds)   + "\n"
          "Width of image (in pixels): \t"    + str(w)      + "\n"
          "Height of image (in pixels): \t"   + str(h)      + "\n")

class decodeSteganograph(text, image):
  def __init__(self):
    pass


################################################################################
# Functions
################################################################################

# String to integer array
# Integers are the unicode value of that integer in unicode.
def stringToInt(string):
  serial = []
  for character in string:
    serial.append(int(ord(character)))

  return serial

  
# Assumes img is an 'Image' object from PIL
def getPixelValues(img):
  pix = []
  for i in range(img.height):
    for j in range(img.width):
      loc = (j,i) #NOTE: Location has to be a tuple
      p = img.getpixel(loc)
      p = list(p) # Format data to be able to be edited.
      pix.append(p)
  return pix
  
  
def distEncodePixel(pixel, char):
  if type(char) == str:
    if ord(char) > 127:
      char = 127
    else:
      char = ord(char)
  #                                  bits  6543210
  # Treat the 7 bits of the char like this BBGGGRR
  redAdd = char & 0x03
  greenAdd = (char >> 2) & 0x07
  blueAdd = (char >> 5) & 0x03

  # Alter the pixels with the fragmented information.
  p = [0,0,0]
  p[0] = pixel[0] + redAdd
  p[1] = pixel[1] + greenAdd
  p[2] = pixel[2] + blueAdd

  return tuple(p)
  

def distEncode(stegno):
  width, height = stegno.picDim
  # Init a new image to store stuff into of the same size as the given one.
  encoded = Image.open('jim.jpg')
  chars = stegno.text.raw
  origPxl = stegno.originalPixels

# loc = []
# for i in range(height):
#   for j in range(width):
#     loc.append(tuple([j,i])) #NOTE: Location has to be a tuple

  loc = getPixelLocations(stegno.image, stegno.nbPixelsNeeded)

  logging.info("The last image pixel to be encoded will be = {}".format(
               loc[len(chars) -1]))

  for i in range(len(chars)):
    p = distEncodePixel(origPxl[i], chars[i])
    encoded.putpixel(loc[i], p)

  return encoded


# Encode the text into the image and return an image object as the end result.
def bulkEncode(stegno):
  width, height = stegno.picDim
  # Init a new image to store stuff into of the same size as the given one.
  encoded = Image.open(stegno.imgFilePath)
  chars = stegno.text.raw
  origPxl = stegno.originalPixels

  loc = []
  for i in range(height):
    for j in range(width):
      loc.append(tuple([j,i])) #NOTE: Location has to be a tuple
  
  #loc = getPixelLocations(stegno.image, stegno.nbPixelsNeeded)

  logging.info("The last image pixel to be encoded will be = {}".format(
               loc[len(chars) -1]))

  for i in range(len(chars)):
    p = distEncodePixel(origPxl[i], chars[i])
    encoded.putpixel(loc[i], p)

  # Add random noise to the rest of the image.
  for i in range(len(chars), len(loc)):
    noise = randint(0, 127)
    original = list(encoded.getpixel(tuple(loc[i])))

    if loc[i] == loc[-10]:
      logging.debug("noise is {}\toriginal is: {}".format(noise, original))
      logging.debug("type of noise is {}\ttype of original is: {}".format(
                    type(noise), type(original)))

    p = distEncodePixel(original, noise)
    encoded.putpixel(loc[i], p)

  return encoded


def endEncodePixel(pixel, char):
  shelf = (pixel[0] << 16) | (pixel[1] << 8) | (pixel[2])
  shelf += ord(char)
  leftMask    = 255 << 16
  middleMask  = 255 << 8
  rightMask   = 255
  p = [0,0,0]
  p[0] = (leftMask & shelf)   >> 16
  p[1] = (middleMask & shelf) >> 8
  p[2] = (rightMask & shelf) 
  return tuple(p)

  
def endDecodePixel(oldPixel, newPixel):
  newShelf = (newPixel[0] << 16) | (newPixel[1] << 8) | (newPixel[2])
  oldShelf = (oldPixel[0] << 16) | (oldPixel[1] << 8) | (oldPixel[2])
  shelf = newShelf - oldShelf
  leftMask    = 255 << 16
  middleMask  = 255 << 8
  rightMask   = 255
  p = [0,0,0]
  p[0] = (leftMask & shelf)   >> 16
  p[1] = (middleMask & shelf) >> 8
  p[2] = (rightMask & shelf) 
  char = chr(p[2])
  return char


def getFileDate():
  string = time.asctime()
  string = string.split(' ')[1:] # Get rid of the spaces and format
  string = '_'.join(string)
  string = string.split(':')
  string = '.'.join(string)
  string = string[0:3] + string[4:] # Format it prettier.
  return string
  
# Take in the image with the encoded text and the original image (no encoded
#   text) and log the encoded message, returning True if success.
# TODO
def endDecode(origImg, ecdImg):
  oWidth, oHeight = origImg.size
  eWidth, eHeight = ecdImg.size

  # TODO: Turn into error class not just a print message.
  if oWidth != eWidth and oHeight != eHeight:
    logging.critical("Dimensions of images do not agree.")
    return None

  # Decoded message may be long, so it will be written to a file.
  outputPath = "decoded/" + getFileDate() + "_" + imageIO[:-4] + '.txt'
  decoded = open(outputPath, "w")
  
  loc = [] # Create the tuple of all x,y coordinates in the image
  for i in range(eHeight):
    for j in range(eWidth):
      loc.append(tuple([j,i])) #NOTE: Location has to be a tuple

  for i in range(len(loc)):
    # Grab a pixel and make it editable (as a list)
    origPxl = list(origImg.getpixel(loc[i]))
    ecdPxl = list(ecdImg.getpixel(loc[i]))
    c = endDecodePixel(origPxl, ecdPxl)
    decoded.write(str(c))
  decoded.close()

  return True
  
# Returns a tuple of vectors of where to add encoded pixels into an image.
def getPixelLocations(img, nbPixelsNeeded):
  w,h = img.image.size
  nbPxlAvailable = w*h

  # Periodicity = How many pixels between an encoded pixel.
  period = nbPxlAvailable // nbPixelsNeeded
  if (w % period == 0) and period > 1:
    period -= 1

  loc = []
  for i in range(h):
    for j in range(0, w, period): # Jump in increments of the period
      loc.append(tuple([j,i])) 

  logging.info("Width of image = {}\tHeight of image = {}".format(w,h))
  logging.info("nbPxlAvailable = {}\tnbPixelsNeeded = {}".format(
                nbPxlAvailable, nbPixelsNeeded))
  logging.info("Each encoded pixel will jump by {} pixels.".format(period))
  logging.info("Last entry in location vector = {}".format(loc[-1]))
  logging.info("Length of the location vector = {}".format(len(loc)))

  return loc 
  
  
# Main -- runs when the script is executed
def main():
  steg = makeSteganograph(textIO, imageIO)
  im = bulkEncode(steg)  
  im.save("bulkDistDog_wNoise.jpg", "JPEG")


################################################################################
# Admin
################################################################################

imageIO = 'dog.jpg'
textIO = 'othello.txt'

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    main()

################################################################################ 
# Notes
################################################################################ 

# TODO:
# When doing arithmetic adding letters in, have to handle for overflow issues,
#   recall that the text has to be recoverable, so you must be able to pull it 
#   out with an inverse method.
# Be able to evenly distribute encoded pixels with a location array generator
# Leftshift the "redAdd" etc so that more distortion is caused
# Bulk encode the data. After data is encoded, put random noise into the rest
#   of the pixels. Use the image as the input to an algorithm that will 
#   generate the location in the "noisy" section of how long the message 
#   actually is, so you know when to stop decoding. In this way, the original
#   image will be the entire key to decrypting. 


# NOTE:

# Take in image for encoding.
#im = Image.open(io)

# Must pass tuple of x,y cooridnate of pixel you want.
#im.getpixel((0,0))

# TESTED CODE:
#  steg = makeSteganograph(textIO, imageIO)
#  othelloJim = distEncode(steg)
#  othelloJim.save("othelloJim.jpg", "JPEG")
# original = Image.open('jim.jpg')
# encoded = Image.open('endEncodedResult.jpg')
# endDecode(original, encoded) # Doesn't work.
# im.save("diffuseEndMsgTest.jpg", "JPEG")
# im = distEncode(steg)
# im.save("diffuseDstMsgTest.jpg", "JPEG")
#  l = getPixelLocations(steg.image, steg.nbPixelsNeeded)
