import smbus
import time
import os, sys, subprocess, re

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

BUTTON_1 = 1
BUTTON_2 = 2
BUTTON_3 = 4
BUTTON_4 = 8

BUTTON_1_CURRENT = 0
BUTTON_1_PREV = 0
BUTTON_2_CURRENT = 0
BUTTON_2_PREV = 0
BUTTON_3_CURRENT = 0
BUTTON_3_PREV = 0
BUTTON_4_CURRENT = 0
BUTTON_4_PREV = 0

LED_1 = 16
LED_2 = 32
LED_3 = 64
LED_4 = 128

ledStates = {LED_1: 0, LED_2: 0, LED_3: 0, LED_4: 0}

bus = smbus.SMBus(BUS_NUMBER)

# PULLUP all ports to enable button state readout
writeVal = 255
bus.write_byte(DEVICE_ADDR,writeVal)

callAction = ''
currentAction = 'stop'

while 1==1:
        #get current value from register
        currentVal = bus.read_byte(DEVICE_ADDR)

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
                #here....
                if currentAction == 'stop':
                        callAction = 'play'
                else:
                        callAction = 'stop'

        print callAction

        if callAction == 'play':
                # music = os.popen('mpg321 media/01.mp3', 'w')
                Popen('mpg321 media/01.mp3'.split(' ',1), stdout=PIPE, close_fds=True)
        elif callAction == 'stop':
                os.popen('pkill -SIGHUP mpg321 #stop', 'w')

        if callAction != '':
                currentAction = callAction
        
        callAction = ''

        # print BUTTON_1_CURRENT

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
                # print led, val;

        '''
        if currentVal & BUTTON_1 == 0:
                print 'Pressed'
        else:
                print 'Not Pressed'   
        '''

        # write to device
        bus.write_byte(DEVICE_ADDR,writeVal)

        time.sleep(0.1)