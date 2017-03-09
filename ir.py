'''IR decoder
Marc Hoffman 2017

Wiring any available GPIO input pin can be used, Timeline is tight with Python isr.

'''
from machine import Pin,Timer,disable_irq,enable_irq
import time
import array
import micropython
micropython.alloc_emergency_exception_buf(100)

class DummyPort:
    def high(self):
        pass
    def low(self):
        pass

class irrecv:
    '''irrecv receive IR signal on pin into circular buffer'''
    def __init__(self,pno=4,bsz=1024,dbgport=None):
        self.BUFSZ=bsz
        self.pin=pno
        self.ir=Pin(pno,Pin.IN)
        self.buf=array.array('i',0 for i in range(self.BUFSZ))
        self.ledge=0
        self.wptr=0
        self.rptr=0
        self.dbgport=dbgport
        if dbgport is None:
            self.dbgport=DummyPort()
        self.dbgport.low()
        self.start()
    def __repr__(self):
        return "<irrecv: {}, wptr={} rptr={}>".format(self.pin,
                                                      self.wptr,self.rptr)
    def timeseq_isr(self,p):
        '''compute edge to edge transition time, ignore polarity'''
        e=time.ticks_us()
        self.dbgport.high()
        #s=2*p.value()-1
        d=time.ticks_diff(e,self.ledge)
        self.ledge=e
        self.buf[self.wptr]=d #*s
        self.wptr+=1
        if self.wptr >= self.BUFSZ:
            self.wptr = 0
        self.dbgport.low()

    def stop(self):
        '''disable isr'''
        self.ir.deinit()
    def start(self):
        self.ir.irq(trigger=Pin.IRQ_FALLING|Pin.IRQ_RISING,handler=self.timeseq_isr)
    def reset(self):
        state=disable_irq()
        self.wptr=0
        self.rptr=0
        enable_irq(state)

    def samples(self):
        w=self.wptr
        r=self.rptr
        n=w-r
        if n>=0:
            x=self.buf[r:w]
        elif n<0:
            x=self.buf[r:]+self.buf[:w]
        self.rptr=w
        return x
    def __call__(self):
        return self.samples()

class DecodeError(Exception):
    pass

class decoder:
    '''ir decoder base class'''
    def __init__(self,eps=64):
        self.eps=eps
    def match(self,measured,setpt,debug=False):
        d=abs(measured-setpt)
        ceil=((setpt*0x2F00)>>15)  # ~25%
        if debug:
            print("measured={} delta={} ceil={} setp={}".format(measured,d,ceil,setpt))
        return d<ceil
    def scan(self,timeseq,code,debug=False):
        n=len(timeseq)
        i=0
        while i<n and not self.match(timeseq[i],code,debug=debug):
            i+=1
        if i<n:
            return timeseq[i:]
        else:
            return None


class nec(decoder):
    '''nec decoder
    geometry follows in terms of us valid sequneces start with 
    9000us MARK 4500us SPACE [BIT_MARK SPACE]*32
    '''
    HDR_MARK   = 9000
    HDR_SPACE  = 4500
    BIT_MARK   = 560
    ONE_SPACE  = 1690
    ZERO_SPACE = 560
    RPT_SPACE  = 2250
    BITS = 32
    def __init__(self):
        super().__init__()
    def match(self,v,code,debug=False):
        return super().match(abs(v),code,debug=debug)
    def __call__(self,inp,debug=False):
        timeseq=self.scan(inp,self.HDR_MARK)
        if timeseq is None:
            return None
        n=len(timeseq)
        if debug:
            print(timeseq[:4])
        if (n>2
            and self.match(timeseq[1],self.RPT_SPACE,debug=debug) 
            and self.match(timeseq[2],self.ZERO_SPACE,debug=debug)):
            return ('repeat',0,timeseq[3:])

        if (n>1 and not self.match(timeseq[1],self.HDR_SPACE,debug=debug)):
            return None

        if n<2*self.BITS+2:
            return None
        
        data=0
        samps=[]
        for i in range(self.BITS):
            if not self.match(timeseq[2+2*i],self.BIT_MARK,debug=debug):
                raise DecodeError
            if self.match(timeseq[2+2*i+1],self.ONE_SPACE,debug=debug):
                b=1
            elif self.match(timeseq[2+2*i+1],self.ZERO_SPACE,debug=debug):
                b=0
            else:
                raise DecodeError
            data=(data<<1)|b
            samps.append(b)
        rest=timeseq[2+self.BITS*2:]
        return (data,samps,rest)

class IRnec(nec):
    def __init__(self,ir):
        self.ir=ir
        self.samples=array.array('i')
    def __call__(self,debug=False):
        self.samples=self.samples+self.ir()
        if len(self.samples):
            x=super().__call__(self.samples,debug=debug)
            if x is None:
                return None
            (data,samps,rest)=x
            self.samples=rest
            if isinstance(data,int):
                return hex(data)
            return data
        return None
    def reset(self):
        self.samples=array.array('i')        
dbg=None # Pin(5,Pin.OUT)
n=IRnec(irrecv(4,bsz=256,dbgport=dbg))
def test():
    while True:
        try:
            x=n()
        except DecodeError:
            print('DecodeError')
            print(n.samples)
            return
        if x:
            print(x)

