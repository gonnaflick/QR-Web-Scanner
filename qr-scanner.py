# Import dependency to check what OS is running
from sys import platform

# Import json for file config
import json

# Import dependencies for OpenCV (QR detection by camera)
import os
import cv2
import numpy as np
import pathlib
import time
from pyzbar.pyzbar import decode

# Import dependencies for Notify-Py and PyAutoGUI (Notification systems)
from notifypy import Notify
import pyautogui

# Import dependencies for Selenium (Browser auto-fill)
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options

# Function to send notifications
def notify(message, audio, icon):
    notification = Notify()

    notification.title = "Registro de acceso por QR"
    notification.message = message
    notification.audio = audio
    notification.icon = icon

    notification.send()

# Function to draw line and text around QR code
def draw(barcode, img, message, red, green, blue):
    # Draw around the QR code
    pts = np.array([barcode.polygon],np.int32)
    pts = pts.reshape((-1,1,2))
    cv2.polylines(img,[pts],True,(blue,green,red),5)

    # Draw QR ID
    pts2 = barcode.rect
    cv2.putText(img, message, (pts2[0],pts2[1]),cv2.FONT_HERSHEY_DUPLEX,
    0.9,(blue,green,red),2)

# Config video capture, size and previous data init
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    pyautogui.alert('No se ha encontrado ninguna camara.','Advertencia','Aceptar')
    exit()

# Define window size and init variables
cap.set(3,300)
cap.set(4,300)
oldData = ""
delayScan = False
scanTime = time.time() + 10

# Web auto-fill config
options = Options()
options.add_argument("--start-maximized")
browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), chrome_options=options)

browser.get('YOUR BROWSER URL')

# Wait for login input to find XPATH in home
try:
    # Where tuition is the auto-filled object for the text element
    idNum = WebDriverWait(browser, 600).until(EC.presence_of_element_located((By.XPATH,'ELEMENT XPATH')))
except Exception as e: 
    # Exception alert for timeout
    pyautogui.alert('Saliendo de la aplicacion por inactividad.','Advertencia','Aceptar')
    browser.close()
    exit()

# While the camara is connected, run the decode
while True:
    # Capture frame-by-frame
    success, img = cap.read()

    # If camera is not detected after instance began, interrupt and exit
    if not success:
        pyautogui.alert('No se ha encontrado ninguna camara, saliendo de la aplicacion.','Advertencia','Aceptar')
        cv2.destroyAllWindows()
        browser.close()
        exit()

    # For each value in the QR code, run the decode
    for barcode in decode(img):
        newData = barcode.data.decode('utf-8')
        # If the new decoded value != from the previous one, run the insert
        if oldData != newData:
            if time.time() - scanTime <= 3:
                # Call draw as success
                draw(barcode,img,f"Espere: {3 - (time.time() - scanTime)} seg.",50,50,50)
                continue

            # Call draw as success
            draw(barcode,img,newData,0,255,0)
        
            # Auto-fill to browser
            idNum.clear()
            idNum.send_keys(newData)
            # idNum.send_keys(Keys.ENTER)

            # Send notification (success)
            notify(f"Acceso registrado ID: {newData[1:-4].strip()}", "./etc/audio/success.wav", "./etc/icon/success/96.png")

            # Update the previous decode for next scan
            oldData = newData
            
            # Save the time of the 'succesful scan' or SS
            scanTime = time.time()
            delayScan = True

        # Else if, run the error for previous input
        elif oldData == newData:
            # If diff between actual time and SS is lower or equal to 2 sec 
            # and delay is True, draw success
            if time.time() - scanTime <= 3 and delayScan == True:
                # Call draw as success
                draw(barcode,img,newData,0,255,0)

            # If diff between actual time and SS is higher than 2 sec 
            # and delay is True, delay no longer necessary
            elif time.time() - scanTime > 3 and delayScan == True:
                delayScan = False
            
            # Else if diff between actual time and SS is lower than 5 sec 
            # and delay is False, draw remove
            elif time.time() -scanTime < 5 and delayScan == False:
                # Call draw as remove
                draw(barcode,img,f"Retire ID",255,0,0)
            
            # Else if diff between actual time and SS is equal or higher than 5 sec 
            # and delay is False, draw remove and send notification
            elif time.time() - scanTime >= 5 and delayScan == False:
                # Call draw as removeif oldData == newData
                draw(barcode,img,f"Retire ID",255,0,0)
                
                # Send notification (remove)
                notify(f"Retire del escaner ID: {newData[1:-4].strip()}", "./etc/audio/remove.wav", "./etc/icon/remove/96.png")

                # Update scan time
                scanTime = time.time()

        # Else, run the error
        else:
            # If diff betwrrn actual time and SS is lower than 3 sec, draw error
            if time.time() - scanTime < 3:
                # Call draw as error
                draw(barcode,img,"Error desconocido.",0,0,255)

            # Else draw error and send notification
            else:
                # Call draw as error
                draw(barcode,img,"Error desconocido.",0,0,255)

                # Send notification (error)
                notify(f"Error desconocido detectado. Favor de reportarlo.", "./etc/audio/error.wav", "./etc/icon/error/96.png")
                
                # Show dialog window to check user input for reset
                reset = pyautogui.confirm('Ha ocurrido un error desconocido. ¿Desea reiniciar la aplicación para intentar resolver el error?', "Advertencia", ['Reiniciar','Cancelar'])

                # Reset if true
                if reset == "Reiniciar":
                    cap.release()                
                    cv2.destroyWindow("QR Camera POV")

                    # Reset
                    cap = cv2.VideoCapture(0)
                    if not cap.isOpened():
                        pyautogui.alert('No se ha encontrado ninguna camara.','Advertencia','Aceptar')
                        exit()
                    cap.set(3,300)
                    cap.set(4,300)
                    oldData = ""
                    delayScan = False
                else:
                    # Update last scan if False
                    scanTime = time.time()

    # Create the camera window
    cv2.imshow('QR Camera POV', img)
    cv2.waitKey(1)

    # If camera window is closed, break
    if cv2.getWindowProperty('QR Camera POV',cv2.WND_PROP_VISIBLE) < 1:
        browser.close()
        break

# When exiting, release the capture 
cap.release()
cv2.destroyAllWindows()