import machine
import esp
esp.uart_nostdio(1)
u=machine.UART(0)
u.init(57600)
gpio2=machine.Pin(2)
gpio2.init(machine.Pin.OUT)
gpio0=machine.Pin(0)

# reset min pro gpio2 ---> (pro)RESET
gpio2.value(1)
gpio2.value(0)
gpio2.value(1)

