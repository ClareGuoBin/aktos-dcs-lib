import pigpio
import time

try:
  pi = pigpio.pi()
  GPIO_pin=4

  pi.set_mode(GPIO_pin, pigpio.OUTPUT)
  pi = pigpio.pi() # connect to local Pi

  freq = 30000 # Hz 

  period = 1.0 / freq * 10**6

  print "period: %f" % period


  #ramp_time = 5 # sec

  #start_date = time.time()

  # final wave 
  square = []
  square.append(pigpio.pulse(1<<GPIO_pin, 0,       period/2.0))
  square.append(pigpio.pulse(0,       1<<GPIO_pin, period/2.0))

  pi.wave_clear()
  pi.wave_add_generic(square)

  wid0 = pi.wave_create()

  square = []

  steps = 200
  for i in range(steps): 
    #print "i : ", i
    #                          ON       OFF    MICROS
    square.append(pigpio.pulse(1<<GPIO_pin, 0,       period/2.0 * (steps / (i + 1.0))))
    square.append(pigpio.pulse(0,       1<<GPIO_pin, period/2.0 * (steps / (i + 1.0))))

  pi.wave_add_generic(square)


  # lee-way
  square = []

  offset = pi.wave_get_micros()

  print("ramp is {} micros".format(offset))

  square.append(pigpio.pulse(0, 0, offset))

  for i in range(2000):
    square.append(pigpio.pulse(1<<GPIO_pin, 0,       period/2))
    square.append(pigpio.pulse(0,       1<<GPIO_pin, period/2))

  pi.wave_add_generic(square)

  wid1 = pi.wave_create()

  pi.wave_send_once(wid1)

  time.sleep(float(offset)/1000000.0) # make sure it's a float

  pi.wave_send_repeat(wid0)

  time.sleep(20)



finally: 
  pi.wave_clear()
  pi.wave_tx_stop() # <- important!
  pi.stop()