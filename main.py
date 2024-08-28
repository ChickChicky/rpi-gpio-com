import RPi.GPIO as GPIO
from sys import argv
import time

PIN_IN  = 29
PIN_OUT = 31

FREQ = 1/80
WIDTH = FREQ * .5

PAUSE = .0001

GPIO.setmode(GPIO.BOARD)

GPIO.setup(PIN_IN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(PIN_OUT, GPIO.OUT, initial=0)

def pause():
  time.sleep(PAUSE)

def eq(a, b, eps):
  return abs(a-b) < eps

class Tick:
  state:   bool
  rising:  bool
  falling: bool
  
  def __init__(self, state: bool, edge: int):
    self.state = state
    self.rising = edge == 1
    self.falling = edge == 2

class Clock:
  width: float
  freq: float
  ref: float
  
  def __init__(self, width: float, freq: float):
    self.width = width
    self.freq = freq
    self.ref = now()
    self._t = False
  
  def tick(self):
    state = (now() - self.ref - self.width/2) % self.freq < self.width
    edge = 0
    if state != self._t:
      edge = self._t + 1
      self._t = state
    return Tick(state,edge)
    
def now():
  return time.time()

def main_a():
  print('Running Sender')
  
  msg = bytes(input('Message: '),'utf-8')
  
  clk = Clock(WIDTH, FREQ)
  
  buff = [1, 0]
  dat = bytearray([len(msg)]) + msg
  for it in dat:
    for i in range(8):
      buff.append(it&(1<<i))
  
  s = False
  
  while True:
    pause()
    
    tick = clk.tick()
    
    if tick.rising:
      if len(buff):
        s = buff.pop(0)
      else:
        break
      
    # print('/' if tick.rising else '\\' if tick.falling else '‾' if (tick.state) else '_', end='', flush=True)
      
    GPIO.output(PIN_OUT, tick.state and s)
  
def main_b():
  print('Running Receiver')
  
  def high():
    return GPIO.input(PIN_IN)
  
  def low():
    return not high()
  
  clk: Clock = None
  
  d = []
  hits = []
  
  def recv_sync() -> None:
    """
    Waits for a single bit to be received to synchronize the clock
    """
    nonlocal clk
    while not high():
      pause()
    sync_start = now()
    while not low():
      pause()
    sync_end = now()
    sync_len = sync_end - sync_start
    clk = Clock(sync_len, FREQ)
    clk.ref = sync_end + sync_len / 2
  
  def recv_bit() -> bool:
    """
    Waits for a single bit to be received and returns its value
    """
    hits = []
    while True:
      pause()
      tick = clk.tick()
      if tick.state:
        hits.append(high())
      elif len(hits):
        return eq(sum(hits)/len(hits), 1, .2)
  
  def recv_bits(count:int) -> list[bool]:
    """
    Waits for n bits to be received and returns their value
    """
    return [recv_bit() for _ in range(count)]
  
  def recv_int(bits:int) -> int:
    """
    Waits for an integer of n bits to be received and returns its value
    """
    n = 0
    for i, v in enumerate(recv_bits(bits)):
      n += v << i
    return n
  
  def recv_bytes(size:int) -> bytes:
    return bytes(int(recv_int(8)) for _ in range(size))
  
  recv_sync()
  
  mode = recv_bit()
  
  if mode == 1:
    raise TypeError('Received unsupported mode 1')
  
  msg_len = recv_int(8)
  print('len: ',msg_len)
  
  msg = recv_bytes(msg_len).decode('utf-8')
  print('msg: ',repr(msg))
  
  return    
  
  while True:
    
    time.sleep(PAUSE)
    
    if state == 0:
      if high():
        sync_start = now()
        state = 1
    
    if state == 1:
      if low():
        t = now()
        sync_len = t - sync_start
        clk = Clock(sync_len, FREQ)
        clk.ref = t + sync_len / 2
        state = 2
        
    if state == 2:
      tick = clk.tick()
      
      # print('/' if tick.rising else '\\' if tick.falling else '‾' if (tick.state) else '_', end='', flush=True)
      
      # if high() and not syncing:
      #   sync_start = now()
      #   syncing = True
      #   
      # if low() and syncing:
      #   t = now()
      #   sync_len = t - sync_start
      #   ref = t + sync_len / 2
      #   # print('-------------')
      #   # print('%.4f %.4f\n%.4f %.4f' % (clk.ref % clk.freq, clk.ref % sync_len, ref % clk.freq, ref % sync_len))
      #   # print('-------------')
      #   print('-------------')
      #   print((ref-clk.ref) % sync_len)
      #   print(clk.width - sync_len)
      #   print('%.4f %.4f' % (clk.ref % clk.freq, clk.ref % sync_len))
      #   print('-------------')
      #   syncing = False
      
      if tick.state:
        hits.append(high())
      
      elif len(hits):
        v = eq(sum(hits)/len(hits), 1, .2)
        print(sum(hits)/len(hits))
        d.append(v)
        hits = []
        
      if len(d) >= 2:
        print(list(map(int,d)))
        d = []
        state = 0

def main():
  if len(argv) <= 1:
    return
  if argv[1] == 'a':
    main_a()
  elif argv[1] == 'b':
    main_b()

try:
  main()
finally:
  GPIO.cleanup()
  print()