import keyboard as kb
from Scripts.Controller import VirtualMouse

VM = VirtualMouse()


def test(event: kb.KeyboardEvent):
    if event.event_type == "down":
        VM.move_relative(1,1)


kb.hook_key("e", test, suppress=True)

kb.wait("q", suppress=True)

kb.unhook_all()
