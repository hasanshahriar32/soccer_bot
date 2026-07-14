#!/usr/bin/env python3
# Note: This requires the gpiozero library to be installed on the Pi.
# Ensure your motor controller (L298N) is correctly wired.

try:
    from gpiozero import Robot
except ImportError:
    print("Warning: gpiozero not installed. Hardware control disabled.")
    Robot = None

class MotorController:
    def __init__(self, left_pins=(17, 18), right_pins=(22, 23)):
        """
        Initializes the motor controller pins.
        left_pins: Tuple of (Forward_Pin, Backward_Pin)
        right_pins: Tuple of (Forward_Pin, Backward_Pin)
        """
        if Robot:
            self.robot = Robot(left=left_pins, right=right_pins)
        else:
            self.robot = None
            
    def move(self, linear_velocity, angular_velocity):
        """
        Converts abstract linear and angular velocity commands into wheel commands.
        linear_velocity: Forward/Backward speed (-1.0 to 1.0)
        angular_velocity: Turning speed (-1.0 to 1.0, positive is right)
        """
        if not self.robot:
            print(f"[Simulated Motor] Linear: {linear_velocity}, Angular: {angular_velocity}")
            return
            
        left_speed = linear_velocity + angular_velocity
        right_speed = linear_velocity - angular_velocity
        
        # Clamp speeds between -1 and 1
        left_speed = max(-1.0, min(1.0, left_speed))
        right_speed = max(-1.0, min(1.0, right_speed))
        
        self.robot.value = (left_speed, right_speed)

    def stop(self):
        if self.robot:
            self.robot.stop()
        else:
            print("[Simulated Motor] Stop")

if __name__ == '__main__':
    print("MotorController module ready.")
