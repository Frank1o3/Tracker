import vgamepad as vg
import time


class PhantomForcesController:
    def __init__(self):
        self.gamepad = vg.VX360Gamepad()

    def press_button(self, button):
        """Press and release a button on the gamepad."""
        self.gamepad.press_button(button=button)
        self.gamepad.update()
        time.sleep(0.1)
        self.gamepad.release_button(button=button)
        self.gamepad.update()

    def hold_button(self, button):
        """Hold a button on the gamepad."""
        self.gamepad.press_button(button=button)
        self.gamepad.update()

    def release_button(self, button):
        """Release a button on the gamepad."""
        self.gamepad.release_button(button=button)
        self.gamepad.update()

    def move_stick_float(self, stick, x: float, y: float):
        """Move a stick on the gamepad."""
        if stick == "left":
            self.gamepad.left_joystick_float(x_value_float=x, y_value_float=y)
        elif stick == "right":
            self.gamepad.right_joystick_float(x_value_float=x, y_value_float=y)
        self.gamepad.update()

    def move_stick(self, stick, x: int, y: int):
        """Move a stick on the gamepad."""
        if stick == "left":
            self.gamepad.left_joystick(x_value_float=x, y_value_float=y)
        elif stick == "right":
            self.gamepad.right_joystick(x_value_float=x, y_value_float=y)
        self.gamepad.update()

    def trigger(self, trigger, value=255):
        """Press a trigger on the gamepad."""
        if trigger == "left":
            self.gamepad.left_trigger(value)
        elif trigger == "right":
            self.gamepad.right_trigger(value)
        self.gamepad.update()

    def fire_weapon(self):
        """Simulate firing the weapon by pressing the right trigger."""
        self.trigger("right", 255)
        time.sleep(0.2)  # Hold trigger for a short duration
        self.trigger("right", 0)  # Release trigger

    def aim_down_sights(self):
        """Simulate aiming down sights by pressing the left trigger."""
        self.trigger("left", 255)

    def stop_aiming_down_sights(self):
        """Stop aiming down sights by releasing the left trigger."""
        self.trigger("left", 0)

    def jump(self):
        """Simulate jumping by pressing the A button."""
        self.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A)

    def crouch(self):
        """Simulate crouching by pressing the B button."""
        self.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_B)

    def reload(self):
        """Simulate reloading by pressing the X button."""
        self.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_X)

    def switch_weapon(self):
        """Simulate switching weapons by pressing the Y button."""
        self.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)

    def throw_grenade(self):
        """Simulate throwing a grenade by pressing the right bumper."""
        self.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)

    def melee_attack(self):
        """Simulate a melee attack by pressing the right stick button."""
        self.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)

    def move_character_float(self, x: float, y: float):
        """Simulate moving the character with the left joystick."""
        self.move_stick_float("left", x, y)

    def look_around_float(self, x: float, y: float):
        """Simulate looking around with the right joystick."""
        self.move_stick_float("right", x, y)

    def move_character(self, x: int, y: int):
        """Simulate moving the character with the left joystick."""
        self.move_stick("left", x, y)

    def look_around(self, x: int, y: int):
        """Simulate looking around with the right joystick."""
        self.move_stick("right", x, y)

    def start_steady_aim(self):
        """Press the left stick button to steady aim."""
        self.hold_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB)

    def stop_steady_aim(self):
        """Release the left stick button to stop steady aim."""
        self.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB)

    def close(self):
        """Close the virtual gamepad."""
        self.gamepad.reset()
