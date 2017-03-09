import machine
import time

class sr04:
    def __init__(self,trig,echo):
        self.trig=machine.Pin(trig)
        self.trig.init(machine.Pin.OUT)
        self.trig.low()
        self.echo=machine.Pin(echo)
        self.echo.init(machine.Pin.IN)

    def __call__(self,pin):
        self.stop=time.ticks_us()
        self.flight=time.ticks_diff(self.stop,self.start)

    def ping0(self):
        self.trig.high()
        time.sleep_us(10)
        self.trig.low()
        d= machine.time_pulse_us(self.echo,1)
        return d

    def ping(self):
        t=sorted([self.ping0() for x in range(5)])[2]
        return t/148.0
        
