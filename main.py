import PySimpleGUI as sg
import os.path
import threading
import ue9

# Column Layout
column = [
    [sg.Text('ETD555 Motor Driver Controller', font='Helvitica 16 bold')],
    [sg.HorizontalSeparator()],
    [sg.Text('Speed (%)')],
    [sg.Slider( range=(1,100), 
                default_value=50, 
                size=(60,20), 
                orientation='horizontal',
                key='_SLDR_INP_'
            )
    ],
    [    
        sg.Button('Left',  key='_L_BTN_'),
        sg.Button('Right', key='_R_BTN_')
    ],
    [sg.Text("Current Output Status: 0", key='_OUTP_STS_')],
    [sg.Text("Current EStop  Status: 0", key='_ESTOP_STS_')],
    [sg.Text("Current Speed  Value : 0", key='_SPEED_STS_')],
    [sg.HorizontalSeparator()],
    [
        sg.Button('Stop',  key='_STOP_BTN_'),
        sg.Button('Start', key='_START_BTN_')
    ]
]


# Full layout
layout = [
    [
        sg.Column(column)
    ]
]

class MotorDriver:
    estope = 0
    fio_mask    = 0b1111
    fio_dir     = 0b1011
    fio_state   = 0b0000

    # New Instance Init
    def __init__(self, layout):
        self.window = sg.Window("ETD555 Motor Driver Controller", layout)
        self.running = True
        self.window.read()
        self.initUE9()

    # Initialize UE9
    def initUE9(self):
        try: 
            self.d = ue9.UE9(ethernet = True)
            results = self.d.feedback(FIOMask=self.fio_mask, FIODir=self.fio_dir, FIOState=self.fio_state) 
            self.d.timerCounter(TimerClockBase=1, TimerClockDivisor=1, Timer0Mode=0, NumTimersEnabled=1, UpdateConfig=1, Timer0Value=0)
        except:
            self.errorHandler("Init UE9 ")
            self.exit()

    # Read FIO2 (ESTOP) every 1s, handle ESTOP
    def readThread(self):
        threading.Timer(1.0, self.readThread).start()
        print("[MEAS] MEASURE FIO2")
        self.estop(self.d.singleIO(1, 2, Dir = 0, State = 0)['FIO2 State'])
            
    # Handle user input events
    def eventHandler(self, event, values):
        print("[EVENT] {}: {}".format(event, values))
        if event == "Exit" or event == sg.WIN_CLOSED:
            self.exit()
        if event == "_STOP_BTN_":
            self.stop()
        elif event == "_START_BTN_":
            self.start(values['_SLDR_INP_'])  
        elif event == "_R_BTN_":
            self.rotate(1, values['_SLDR_INP_'])
        elif event == "_L_BTN_":
            self.rotate(0, values['_SLDR_INP_'])
        else:
            print('[WARNING] WTF')

    # Stop behaviour
    def stop(self):
        print("[OUT] Stop PWM")
        self.window['_OUTP_STS_'].update('Current Output Status: 0')
        self.window['_SPEED_STS_'].update('Current Speed  Value : 0')
        # Stop PWM on FIO0
        self.d.timerCounter(TimerClockBase=1, TimerClockDivisor=1, Timer0Mode=0, NumTimersEnabled=1, UpdateConfig=1, Timer0Value=0)

    # Start behaviour
    def start(self, speed):
        print("[OUT] Start PWM")
        if self.estope == 0:
            self.window['_OUTP_STS_'].update('Current Output Status: 1')
            self.window['_SPEED_STS_'].update('Current Speed  Value : {}'.format(speed))
            # PWM on FIO0, speed D.C.
            value = round((65536 * speed) / 100)
            self.d.timerCounter(TimerClockBase=1, TimerClockDivisor=1, Timer0Mode=0, NumTimersEnabled=1, UpdateConfig=1, Timer0Value=value)
        else:
            print("[WARNING] ESTOP ENGAGED {}".format(self.estope))

    # Estop engage/disengage (disables output)
    def estop(self, value):
        # print('Emergency Stop Engaged')
        self.stop()
        if not self.estope == value:
            self.estope = value
            self.window['_ESTOP_STS_'].update('Current EStop  Status: {}'.format(value))

    # Direction Change
    def rotate(self, direction, speed):
        print("[OUT] Rotate {} at {} speed".format(direction, speed))
        self.start(speed)
        # WIP: Change FIO1 to DIRECTION

    def exit(self):
        print("Exiting")
        self.stop()
        self.window.close() 
        self.running = False

    def errorHandler(self, msg):
        print("[ERROR] {}".format(msg))
        self.exit()



# Create new instance and ESTOP reading thread
m = MotorDriver(layout)
m.readThread()

# Run the Event Loop
while m.running:
    event, values = m.window.read()
    m.eventHandler(event, values)
    # Insert additional behaviour here
    