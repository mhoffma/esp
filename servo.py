import machine
import time
class Servo:
    '''Hobby servo motors can be controlled using PWM. They require a
    frequency of 50Hz and then a duty between about 40 and 115, with
    77 being the centre value. If you connect a servo to the power and
    ground pins, and then the signal line to pin 12 (other pins will
    work just as well), you can control the motor using:'''
    def __init__(self,pinno,pos=77):
        self.pinno = pinno
        self.pin=machine.Pin(pinno)
        self.pin.init(self.pin.OUT)
        self.p = machine.PWM(self.pin,freq=50)
        self.rot(pos)

    def __repr__(self):
        return "Servo({},pos={})".format(self.pin,self.position)
    def rot(self,angle):
        self.position=angle
        self.p.duty(angle)
        time.sleep_ms(250)
        self.p.duty(0)
    def write(self,angle):
        self.rot(angle)
    def __call__(self,angle):
        self.rot(angle)
    def read(self):
        return self.position
        

        
