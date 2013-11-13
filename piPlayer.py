import smbus, time, os, sys, subprocess, re, random
from subprocess import Popen, PIPE

aFiles = []

iCurrentFile = 0;
iNumberOfFiles = 0;

sPlayMode = 'sequence'

def loadFileList(directory):
    global iNumberOfFiles

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(".mp3"):
                 aFiles.append(os.path.join(root, file))

    iNumberOfFiles = len(aFiles)

def getCurrentFile():
    return aFiles[iCurrentFile]

def getRandomFile():
    global iCurrentFile
    
    iCurrentFile = random.randrange(0, len(aFiles))

    return aFiles[iCurrentFile]

def getNextFile():
    global iCurrentFile
    
    iCurrentFile += 1
    if iCurrentFile >= iNumberOfFiles:
        iCurrentFile = 0

    return aFiles[iCurrentFile]        

def getPrevFile():
    global iCurrentFile
    
    iCurrentFile -= 1
    if iCurrentFile < 0 :
        iCurrentFile = (iNumberOfFiles - 1)

    return aFiles[iCurrentFile]        


def checkIfProcessExists(proc_name):
    ps = subprocess.Popen("ps ax -o pid= -o args= ", shell=True, stdout=subprocess.PIPE)
    ps_pid = ps.pid
    output = ps.stdout.read()
    ps.stdout.close()
    ps.wait()

    for line in output.split("\n"):
        res = re.findall("(\d+) (.*)", line)

        if res:
            pid = int(res[0][0])
            if proc_name in res[0][1] and pid != os.getpid() and pid != ps_pid:
                return True

    return False

# define I2C bus number
BUS_NUMBER = 1

# define device address
DEVICE_ADDR = 0x20

BUTTON_1 = 1 # PLAY/STOP
BUTTON_2 = 2 # Prev
BUTTON_3 = 4 # Next
BUTTON_4 = 8 # PlayRandom / NextRandom

BUTTON_1_CURRENT = 0
BUTTON_1_PREV = 0
BUTTON_2_CURRENT = 0
BUTTON_2_PREV = 0
BUTTON_3_CURRENT = 0
BUTTON_3_PREV = 0
BUTTON_4_CURRENT = 0
BUTTON_4_PREV = 0

LED_1 = 16 #Status LED, lighted up when piPlayer starts
LED_2 = 32 #Status LED, lighted up when piPlayer is playing music
LED_3 = 64 #Status LED, lighted up any of buttons is pressed
LED_4 = 128 #Status LED, lighted up when random mode is selected

ledStates = {LED_1: 0, LED_2: 0, LED_3: 0, LED_4: 0}

bus = smbus.SMBus(BUS_NUMBER)

# PULLUP all ports to enable button state readout
writeVal = 255
bus.write_byte(DEVICE_ADDR,writeVal)

callAction = ''
currentAction = 'stop'
currentState = 'stop'

loadFileList(os.path.dirname(os.path.realpath(__file__)) + '/media/')

currentProcessExists = False
previousProcessExists = False

while 1==1:
    #get current value from register
    currentVal = bus.read_byte(DEVICE_ADDR)

    # print currentVal

    ledStates[LED_1] = 1

    '''
    Here come actual magic
    '''

    if currentVal & BUTTON_1 == 0:
        BUTTON_1_CURRENT = 1

    if currentVal & BUTTON_2 == 0:
        BUTTON_2_CURRENT = 1

    if currentVal & BUTTON_3 == 0:
        BUTTON_3_CURRENT = 1

    if currentVal & BUTTON_4 == 0:
        BUTTON_4_CURRENT = 1

    if (BUTTON_1_CURRENT == 1) & (BUTTON_1_PREV == 0):
        #PLAY button pressed
        if currentAction == 'stop':
            callAction = 'play'
        else:
            callAction = 'stop'

    if (BUTTON_4_CURRENT == 1) & (BUTTON_4_PREV == 0):
        #begin random mode
        sPlayMode = 'random'
        callAction = 'play'
        getRandomFile()                

    #NEXT button pressed
    if (BUTTON_2_CURRENT == 1) & (BUTTON_2_PREV == 0):
        sPlayMode = 'sequence'
        getPrevFile()
        callAction = 'play'

    #NEXT button pressed
    if (BUTTON_3_CURRENT == 1) & (BUTTON_3_PREV == 0):
        sPlayMode = 'sequence'
        getNextFile()
        callAction = 'play'

    # Detect is playing has stopped, and play next song
    currentProcessExists = checkIfProcessExists('mpg321')

    if (currentProcessExists == False and previousProcessExists == True and currentState == 'play'):
        callAction = 'play'

        if sPlayMode == 'random' :
            getRandomFile()
        else:
            getNextFile()

    previousProcessExists = currentProcessExists
    
    # If action is set, print it
    if callAction != '':       
        print callAction

    # Execute action+9 
    if callAction == 'play':
        os.popen('pkill -SIGHUP mpg321 #stop', 'w')
        sCommad = 'mpg321 ' + getCurrentFile()
        Popen(sCommad.split(' ',1), stdout=PIPE, close_fds=True)

        #lightup play LED (LED_2)
        ledStates[LED_2] = 1 
        currentState = 'play'

    elif callAction == 'stop':
        os.popen('pkill -SIGHUP mpg321 #stop', 'w')

        #turn off play LED (LED_2)
        ledStates[LED_2] = 0
        currentState = 'stop'

    if callAction != '':
        currentAction = callAction
    
    callAction = ''

    if BUTTON_1_CURRENT == 1 or BUTTON_2_CURRENT == 1 or BUTTON_3_CURRENT == 1:
        ledStates[LED_3] = 1
    else:
        ledStates[LED_3] = 0    

    BUTTON_1_PREV = BUTTON_1_CURRENT
    BUTTON_1_CURRENT = 0
    BUTTON_2_PREV = BUTTON_2_CURRENT
    BUTTON_2_CURRENT = 0
    BUTTON_3_PREV = BUTTON_3_CURRENT
    BUTTON_3_CURRENT = 0
    BUTTON_4_PREV = BUTTON_4_CURRENT
    BUTTON_4_CURRENT = 0

    # PULLUP bits 0-3 to enable button readout
    writeVal = 15

    # Write LED states
    for led, val in ledStates.iteritems():
        writeVal += led * (val^1)
            
    # write to device
    bus.write_byte(DEVICE_ADDR,writeVal)

    time.sleep(0.1)