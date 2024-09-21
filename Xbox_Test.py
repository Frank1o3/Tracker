from Scripts.XboxController import PhantomForcesController
from threading import Event, Thread
import keyboard as kb
import time


class Bot:
    def __init__(self) -> None:
        self.Controller = PhantomForcesController()
        self.stop_event = Event()
    
    def Main(self):
        while not self.stop_event.is_set():
            self.Controller.update()
            
    
    def keyboard_event(self, event: kb.KeyboardEvent) -> None:
        if event.name == "f1" and event.event_type == "down":
            self.stop_event.set()
            return
    
    def start(self) -> None:
        kb.hook_key("f1", self.keyboard_event, suppress=True)
        
        self.threads = [
            Thread(target=self.Main),
        ]
        
        for t in self.threads:
            t.start()
            
        self.stop_event.wait()
        
        for t in self.threads:
            t.join()
        
        kb.unhook_all()
        self.Controller.close()


if __name__ == "__main__":
    aimbot = Bot()
    time.sleep(3)
    kb.send("f11")
    time.sleep(3)
    aimbot.start()
    time.sleep(3)
    aimbot.Controller.look_around_float(0.5, 0.5)
    time.sleep(3)
    aimbot.Controller.look_around_float(0.0, 0.0)
