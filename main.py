import paho.mqtt.client as mqttClient
import cv2
import numpy as np
import imutils
import time
from plyer import notification
import plyer.platforms.win.notification


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to broker")
        global Connected  # Use global variable
        Connected = True  # Signal connection
    else:
        print("Connection failed")

Connected = False  # global variable for the state of the connection
item = 0
item1 = "close"
broker_address = "192.168.0.119"
port = 1883
user = "homeswitch"
password = "aizoox"
#OpenCV factors
statusOpen      = True
statusClosed    = True
SureFactor      = 0

binary_payload = {
            "name": "garden",
            "device_class": "motion",
            "state_topic": "homeassistant/binary_sensor/garden/state"
        }

client = mqttClient.Client("GateCameraSensor")  # create new instance
client.username_pw_set(user, password=password)  # set username and password
client.on_connect = on_connect  # attach function to callback
client.connect(broker_address, port=port)  # connect to broker

client.loop_start()  # start the loop
topic = "homeassistant/sensor/house/power_use1/config"



while Connected != True:  # Wait for connection
    time.sleep(0.1)

try:
    while True:

        # ////////////////////////////
        ContoursSum = 0

        RTSP_URL_1 = 'rtsp://192.168.0.144/user=admin_password=tlJwpbo6_channel=1_stream=0.sdp?real_stream'
        cap1 = cv2.VideoCapture(RTSP_URL_1, cv2.CAP_FFMPEG)

        if not cap1.isOpened():
            print('Cannot open RTSP stream')
            exit(-1)

        while True:
            success1, frame1 = cap1.read()
            if cv2.waitKey(1) == 27 or success1:
                cap1.release()
                break

        brama1 = frame1[149:300, 600:1150]
        #cv2.imshow('window_name1', brama1)

        GateOpen = brama1
        GateOpen = cv2.GaussianBlur(src=GateOpen, ksize=(5, 5), sigmaX=0)
        # progowanie obrazu
        GateOpenCanny = cv2.Canny(GateOpen, threshold1=50, threshold2=50)

        # Mask do conturów
        MaskOpen = cv2.threshold(src=GateOpen, thresh=200, maxval=255, type=cv2.THRESH_BINARY)[1]

        # DETEKCJA KONTUROW
        OpenContours = cv2.findContours(image=GateOpenCanny, mode=cv2.RETR_LIST, method=cv2.CHAIN_APPROX_SIMPLE)
        # print("open= ",len(OpenContours))

        # Sortowanie i Suma
        OpenContours = imutils.grab_contours(OpenContours)
        OpenContours = sorted(OpenContours, key=cv2.contourArea, reverse=True)

        for contour in range(10):
            # print(cv2.contourArea(contour=contour, oriented=True))
            if cv2.contourArea(contour=OpenContours[contour], oriented=True) > 400:
                ContoursSum = ContoursSum + cv2.contourArea(contour=OpenContours[contour], oriented=True)

        if (ContoursSum > 2000) and (statusClosed == True):
            SureFactor += 1
            print('Factor: ' + str(SureFactor))
            if SureFactor > 3:
                SureFactor = 0
                notification.notify("Brama", "Zamkieta")
                item1 = 'closed'
                statusOpen = True
                statusClosed = False
                print('Zamknieta: ' + str(ContoursSum))
                time.sleep(5)
        elif (ContoursSum < 2000) and (statusOpen == True):
            SureFactor += -1
            print('Factor: ' + str(SureFactor))
            if SureFactor < -3:
                SureFactor = 0
                notification.notify("Brama", "Otwarta")
                item1 = 'open'
                statusOpen = False
                statusClosed = True
                print('Otwarta: ' + str(ContoursSum))
        # new added - testing
        elif (ContoursSum > 2000) and (SureFactor < 0):
            SureFactor += 1
            print('NFactor: ' + str(SureFactor))
        elif (ContoursSum < 2000) and (SureFactor > 0):
            SureFactor += -1
            print('NFactor: ' + str(SureFactor))

        else:
            if statusOpen:
                print('Remains in position Closed: ' + str(ContoursSum) + 'Factor: ' + str(SureFactor))
                time.sleep(5)
            elif statusClosed:
                print('Remains in position Open: ' + str(ContoursSum) + 'Factor: ' + str(SureFactor))
                time.sleep(5)

        client.publish(topic="home-assistant/binary_sensor/Gate/state", payload=str(item1), qos=0, retain=False)
        time.sleep(7)

except KeyboardInterrupt:
    client.disconnect()
    client.loop_stop()