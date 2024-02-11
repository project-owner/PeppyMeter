from peppymeter import Peppymeter
from threading import Thread
import time

def thread_function(arg):
    print("start")
    pm = arg
    while 1:
        print("in thread")
        time.sleep(5)
        print("restarting")
        pm.meter.restart()
        print("restarted")
		
def meter_thread(arg):
    pm = arg
    pm.init_display()
    pm.start_display_output()

if __name__ == "__main__":
    print("main")
    pm = Peppymeter(standalone=True, timer_controlled_random_meter=False)
    m = Thread(target = meter_thread, args=(pm, ))
    m.start()
    t = Thread(target = thread_function, args=(pm, ))
    t.start()
    