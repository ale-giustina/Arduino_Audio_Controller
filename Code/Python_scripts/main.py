import serial
import main2
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import pyautogui
import time
import pygetwindow as gw
import psutil
import ctypes


def get_process_name_by_window_title(window_title):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if window_title in proc.name():
                return proc.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None

def get_current_fullscreen_process_name(prev_win, current_win):
    active_window = gw.getActiveWindow()
    
    if active_window==prev_win:
        return current_win, prev_win
    
    elif active_window is not None:
        window_title = active_window.title
        return get_process_name_by_window_title(window_title), active_window
    
    else:
        return None

# Get the default audio endpoint
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(
IAudioEndpointVolume._iid_, CLSCTX_ALL, None)

# Query the IAudioEndpointVolume interface
volume = cast(interface, POINTER(IAudioEndpointVolume))

#initialize led switches
pin5=False
pin5release=False

pin6=False
pin6release=False

firefox=main2.AudioController("firefox.exe")
discord=main2.AudioController("Discord.exe")


serialfound=False


timeout = time.time() + 25  # 25 seconds from now

current_win = None
current_fullscreen_process_name = None

port=['COM7', 9600]

retry=False

#try to open the serial port
while not serialfound:
    try:
    
        # Open serial port
        ser = serial.Serial(port[0],port[1])  # Use the correct port for your Arduino
        serialfound=True
    
    except:

        if time.time() > timeout:
            
            result = ctypes.windll.user32.MessageBoxW(0, f"Error opening serial port {port[0]} baud {port[1]}", u"Python controller Error", 21)
            
            if result == 4: #retry
                retry=True
                timeout = time.time() + 25  # 25 seconds from now

            elif result == 2: #ignore
                pass

            while retry:
                try:
                    ser = serial.Serial(port[0],port[1])  # Use the correct port for your Arduino
                    serialfound=True
                    break 
                except:
                    if time.time() > timeout:
                        break
                        
            if serialfound==False:
                raise Exception("connection timeout")
                break

#initialize the leds
ser.write(str("pin6low").encode())
ser.write(str("pin5low").encode())
time.sleep(1)          
ser.write(str("pin5high").encode())
time.sleep(1)
ser.write(str("pin6high").encode())
time.sleep(1)
ser.write(str("pin5low").encode())
time.sleep(1)
ser.write(str("pin6low").encode())


firmuted=False
firefox.unmute()

mutedmain=False

sessions = AudioUtilities.GetAllSessions()

previmp=[0,0,0,0,0,0,0,0]

mastervolume = 0
mainmuted=False
fullmuted=False

fullscreenvol=0

#main loop
while True:

    if devices!=AudioUtilities.GetSpeakers():
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
        IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))

    lista = [];

    data = ser.readline().strip()
    
    #recive and decode the inputs from the arduino
    inputs = eval(data.decode())
    inputs[6]=1023-inputs[6]
    inputs[7]=1023-inputs[7]
    inputs[5]=1023-inputs[5]
    
    #mute mic
    if inputs[2] == 1:
        
        if not pin5 and not pin5release:
            pin5 = True
            pyautogui.hotkey('win','ctrl','alt','shift','0')
            ser.write(str("pin5high").encode())

        if pin5release and pin5:
            pin5 = False
            pyautogui.hotkey('win','ctrl','alt','shift','0')
            ser.write(str("pin5low").encode())

    else:
        pin5release = pin5

    #mute main
    if inputs[1] == 1:
        
        if not pin6 and not pin6release:
            pin6 = True
            mainmuted=True
            ser.write(str("pin6high").encode())

        if pin6release and pin6:
            pin6 = False
            mainmuted=False
            volume.SetMasterVolumeLevelScalar(mastervolume, None)
            ser.write(str("pin6low").encode())
    else:
        pin6release = pin6



    delta=0.01

    #FIREFOX
    try:

        if(abs(firefox.process_volume()-float(inputs[6]/1023))>delta):

            firefox.set_volume(float(inputs[6]/1023))
        
        if(inputs[6]>1020):
            firefox.set_volume(1)

        if(inputs[6]<7 and firmuted==False):
            firefox.mute()
            firmuted=True
        elif(inputs[6]>7 and firmuted==True):
            firefox.unmute()
            firmuted=False

    except TypeError:
        print("firefox not open")
        pass

    #DISCORD
    try:
        if(abs(discord.process_volume()-float(inputs[4]/1023))>delta):

            discord.set_volume(float(inputs[4]/1023))
        
        if(inputs[4]>1017):
            discord.set_volume(1)

        if(inputs[3]==0):
            discord.mute()
            dismuted=True
        else:
            discord.unmute()
            dismuted=False
    
    except TypeError:
        print("discord not open")
        pass
    
    #FULLSCREEN WINDOW
    try:
        
        if(abs(fullscreenvol-float(inputs[5]/1023))>delta):
            
            current_fullscreen_process_name, current_win= get_current_fullscreen_process_name(current_win,current_fullscreen_process_name)
            
            main2.AudioController(current_fullscreen_process_name).set_volume(float(inputs[5]/1023))
            fullscreenvol=float(inputs[5]/1023)
        
            if(inputs[5]>1017):
                main2.AudioController(current_fullscreen_process_name).set_volume(1)

            if(inputs[5]<15 and fullmuted==False):
                main2.AudioController(current_fullscreen_process_name).mute()
                fullmuted=True
            
            elif(inputs[5]>15 and fullmuted==True):
                main2.AudioController(current_fullscreen_process_name).unmute()
                fullmuted=False

    except TypeError:
        print("no fullscreen window found")
        pass

    #MASTER
    try:
        if(abs(mastervolume-float(inputs[7]/1023))>delta and mainmuted==False):

            volume.SetMasterVolumeLevelScalar(float(inputs[7]/1023), None)
            mastervolume=float(inputs[7]/1023)

    except:
        print("error")
        pass

    if(inputs[7]>1020):
        volume.SetMasterVolumeLevelScalar(1, None)

    if(inputs[7]<7 and mutedmain==False):
        volume.SetMasterVolumeLevelScalar(0, None)
        mutedmain=True
    elif((inputs[7]>7 and mutedmain==True) or mainmuted==True):
        volume.SetMasterVolumeLevelScalar(0, None)
        mutedmain=False

        
    previmp=inputs

    print(inputs)