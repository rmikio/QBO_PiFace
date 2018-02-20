#!/usr/bin/env python2.7

from multiprocessing import Process, Queue
import time
import cv2
import serial
import binascii
import QboCmd
import sys
import time
import QBOtalk

Qbo = QBOtalk.QBOtalk()

Kpx = 1
Kpy = 1
Ksp = 40

## Head X and Y angle limits

Xmax = 725
Xmin = 290
Ymax = 550
Ymin = 420

## Initial Head position

Xcoor = 511
Ycoor = 600
Facedet = 0

## Time head wait turned
touch_wait = 2

no_face_tm = time.time()
face_det_tm = time.time()
touch_tm = 0
touch_samp = time.time()
qbo_touch = 0
touch_det = False
Listenig = False
listen_thd = 0
face_not_found_idx = 0

Step_x = ([2, 5, 10])
Step_y = ([1, 3, 7])

if len(sys.argv) > 1:
        port = sys.argv[1]
else:
        port = '/dev/serial0'

try:
        # Open serial port
        ser = serial.Serial(port, baudrate=115200, bytesize = serial.EIGHTBITS, stopbits = serial.STOPBITS_ONE, parity = serial.PARITY_NONE, rtscts = False, dsrdtr =False, timeout = 0)
        print "Open serial port sucessfully."
        print(ser.name)
except:
        print "Error opening serial port."
        sys.exit()


QBO = QboCmd.Controller(ser)

QBO.SetServo(1, Xcoor, 100)
QBO.SetServo(2, Ycoor, 100)
time.sleep(1)
QBO.SetPid(1, 32, 8, 16)
time.sleep(1)
QBO.SetPid(2, 32, 8, 16)
time.sleep(1)
QBO.SetNoseColor(0)       #Off QBO nose brigth

webcam = cv2.VideoCapture(0)				# Get ready to start getting images from the webcam
webcam.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 320)		# I have found this to be about the highest-
webcam.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 240)	# resolution you'll want to attempt on the pi
#webcam.set(cv2.CV_CAP_PROP_BUFFERSIZE, 2)		# frame buffer storage

if not webcam:
	print "Error opening WebCAM"
	sys.exit(1)

##get webcam properties
#for i in range(0,24):
#   print webcam.get(i)

frontalface = cv2.CascadeClassifier("haarcascade_frontalface_alt2.xml")		# frontal face pattern detection
profileface = cv2.CascadeClassifier("haarcascade_profileface.xml")		# side face pattern detection

face = [0,0,0,0]	# This will hold the array that OpenCV returns when it finds a face: (makes a rectangle)
Cface = [0,0]		# Center of the face: a point calculated from the above variable
lastface = 0		# int 1-3 used to speed up detection. The script is looking for a right profile face,-
			# a left profile face, or a frontal face; rather than searching for all three every time,-
			# it uses this variable to remember which is last saw: and looks for that again. If it-
			# doesn't find it, it's set back to zero and on the next loop it will search for all three.-
			# This basically tripples the detect time so long as the face hasn't moved much.

time.sleep(1)		# Wait for them to start

#====================================================================================================
def ServoHome():
        global Xcoor, Ycoor, touch_tm
        Xcoor = 511
        Ycoor = 450
        QBO.SetServo(1, Xcoor, 100)
        QBO.SetServo(2, Ycoor, 100)
        touch_tm = time.time()
        return

def WaitForSpeech():
        global Listenig, listen_thd
        if Listenig == False:
                return
        elif Qbo.GetResponse == True:
                listen_thd(wait_for_stop = True)
                Qbo.SpeechText(Qbo.Response)
                QBO.SetNoseColor(0)
                Qbo.GetResponse = False
                Listenig = False
        return
def WaitTouchMove():
        global Xcoor, Ycoor, touch_tm
        time.sleep(2)
        QBO.SetServo(1, Xcoor, 100)
        time.sleep(0.1)
        QBO.SetServo(2, Ycoor, 100)
        #time.sleep(1)
        touch_tm = time.time()
        return
#============================================================================================================

print" Face tracking running."
print" QBO nose bright green when see your face"

Qbo.SpeechText("I am ready.")

touch_tm = time.time()

fr_time = 0
while True:
	print "frame time: " + str(time.time() - fr_time)
	fr_time = time.time()

	faceFound = False       # This variable is set to true if, on THIS loop a face has already been found
                                # We search for a face three diffrent ways, and if we have found one already-
                                # there is no reason to keep looking.
        WaitForSpeech()

        if not faceFound:
                if lastface == 0 or lastface == 1:
			t_ini = time.time()
                        while time.time()-t_ini < 0.01: # wait for present frame
				t_ini = time.time()
				aframe = webcam.read()[1]       #       there seems to be an issue in OpenCV or V4L or my webcam-
				print "t: " + str(time.time()-t_ini)
                        fface = frontalface.detectMultiScale(aframe,1.3,4,(cv2.cv.CV_HAAR_DO_CANNY_PRUNING + cv2.cv.CV_HAAR_FIND_BIGGEST_OBJECT + cv2.cv.CV_HAAR_DO_ROUGH_SEARCH),(60,60))
                        if fface != ():                 # if we found a frontal face...
				print "FAAACEEEE"
                                lastface = 1            # set lastface 1 (so next loop we will only look for a frontface)
                                for f in fface:         # f in fface is an array with a rectangle representing a face
                                        faceFound = True
                                        face = f

        if not faceFound:                               # if we didnt find a face yet...
                if lastface == 0 or lastface == 2:      # only attempt it if we didn't find a face last loop or if-
                        t_ini = time.time()
                        while time.time()-t_ini < 0.01: # wait for present frame
				t_ini = time.time()
				aframe = webcam.read()[1]       #       there seems to be an issue in OpenCV or V4L or my webcam-
				print "tp: " + str(time.time()-t_ini)
                        pfacer = profileface.detectMultiScale(aframe,1.3,4,(cv2.cv.CV_HAAR_DO_CANNY_PRUNING + cv2.cv.CV_HAAR_FIND_BIGGEST_OBJECT + cv2.cv.CV_HAAR_DO_ROUGH_SEARCH),(80,80))

                        if pfacer != ():                # if we found a profile face...
				print "PROFILE FAAACEEEE"
                                lastface = 2
                                for f in pfacer:
                                        faceFound = True
                                        face = f

        if not faceFound:               # if no face was found...-
     #           print "To file"
#              	fr_time_ms = time.time()
#                cv2.imwrite("../frames/frame"+str(fr_time_ms)+".jpg", aframe)     # save frame as JPEG file
     #           print "To file end!"
		face_not_found_idx += 1
		if (face_not_found_idx > 3):
			face_not_found_idx = 0
	                lastface = 0            #       the next loop needs to know
	                face = [0,0,0,0]        # so that it doesn't think the face is still where it was last loop
	                QBO.SetNoseColor(0)       #Off QBO nose brigth
	                if Facedet != 0:
	                        Facedet = 0
	                        no_face_tm = time.time()
	                        print "No face.!"
	                elif(time.time() - no_face_tm > 10):
	                        ServoHome()
	                        Cface[0] = [0,0]
	                        no_face_tm = time.time()
        else:
                x,y,w,h = face
                Cface = [(w/2+x),(h/2+y)]       # we are given an x,y corner point and a width and height, we need the center
#		cv2.rectangle(aframe, (x,y), (x+w, y+h), (255,0,0), 3)
                #print "To file"
#              	fr_time_ms = time.time()
#                cv2.imwrite("../frames/frame"+str(fr_time_ms)+".jpg", aframe)     # save frame as JPEG file
      	        #print "To file end!"
		print "face ccord: " + str(Cface[0]) + "," + str(Cface[1])
                if Facedet == 0:
                        if Listenig == False:
                                QBO.SetNoseColor(4)
			Facedet = 1
                        face_det_tm = time.time()
                        #print "Face detected.!"
                elif Listenig == False & (time.time() - face_det_tm > 2):
                        face_det_tm = time.time()
                        if Listenig == False:
                           QBO.SetNoseColor(1)
                           listen_thd = Qbo.StartBack()
                           Listenig = True
                else :
                        if Listenig:
                                QBO.SetNoseColor(1)       # Set QBO nose blue
                        else:
                                QBO.SetNoseColor(4)

                if touch_det == False:
			faceOffset_X = 160 - Cface[0]
                        if (faceOffset_X > 20) | (faceOffset_X < -20):
				time.sleep(0.002)
                                QBO.SetAngleRelative(1, faceOffset_X >> 1 )
				#wait for move
				time.sleep(0.05)
				print "MOVE REL X: " + str(faceOffset_X >> 1)
			faceOffset_Y = 120 - Cface[1]
                        if (faceOffset_Y > 20) | (faceOffset_Y < -20):
				time.sleep(0.002)
                                QBO.SetAngleRelative(2, faceOffset_Y >> 1 )
				#wait for move
				time.sleep(0.05)
				print "MOVE REL Y: " + str(faceOffset_Y >> 1)

        if time.time() -touch_samp > 0.5:
#                qbo_touch = QBO.GetHeadCmd("GET_TOUCH", 0)
                if touch_tm == 0 and qbo_touch:
                        if qbo_touch == [1]:
                                QBO.SetServo(1, Xmax - 25, 100)
                                time.sleep(0.002)
                                QBO.SetServo(2, Ymin - 5, 100)
                                WaitTouchMove()
                        elif qbo_touch == [2]:
                                QBO.SetServo(2, Ymin - 5, 100)
                                WaitTouchMove()
                        elif qbo_touch == [3]:
                                QBO.SetServo(1, Xmin + 25, 100)
                                time.sleep(0.002)
                                QBO.SetServo(2, Ymin - 5, 100)
                                WaitTouchMove()
        if touch_tm != 0 and time.time() - touch_tm > touch_wait:
                print "touch ready"
                touch_tm = 0

#	QBO.port.flush()
