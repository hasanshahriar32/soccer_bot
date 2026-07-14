#!/usr/bin/env python3
"""
This is a skeleton structure for the ROS 2 Core Brain node.
It acts as the central state machine for the soccer robot.
"""

class SoccerBotBrain:
    def __init__(self):
        self.state = 'SEARCHING' # States: SEARCHING, CHASING, AVOIDING
        
    def main_loop(self, ball_detected, ball_angle, obstacle_blocked, escape_vector):
        """
        The central logic loop that runs continuously.
        Returns: (linear_velocity, angular_velocity)
        """
        if obstacle_blocked:
            self.state = 'AVOIDING'
            return (0.0, escape_vector) # Stop moving forward, just rotate to escape
            
        if ball_detected:
            self.state = 'CHASING'
            # Proportional control to keep the ball centered
            angular_velocity = ball_angle * 0.05 
            linear_velocity = 0.5 # Move forward
            return (linear_velocity, angular_velocity)
            
        else:
            self.state = 'SEARCHING'
            # Spin in place to find the ball
            return (0.0, 0.4) 

if __name__ == '__main__':
    print("Core Brain module ready. This will be wrapped in a ROS 2 Node class.")
