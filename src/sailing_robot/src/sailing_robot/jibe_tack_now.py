from collections import deque
import LatLon as ll
import math
from shapely.geometry import Point, Polygon

from .navigation import angleSum
from .taskbase import TaskBase
from .heading_planning import TackVoting

# For calculations, lay lines don't extend to infinity.
# This is in m; 10km should be plenty for our purposes.

class JibeTackNow(TaskBase):
    def __init__(self, nav,
                 action='auto',
            ):
        """Jibe or tack now

        *nav* is a sailing_robot.navigation.Navigation instance.
        
        *action* is a string, can be either 'jibe', 'tack', or 'auto' depending
        on what is needed, 'auto' will tack if the boat was jibing and jibe
        if the boat was tacking by default
        """
        self.nav = nav
        self.sailing_state = 'normal' 
        self.action = action
        self.continue_tack = True
    
    def start(self):
        pass

    def check_end_condition(self):
        """Are we there yet?"""
        return not self.continue_tack

    def calculate_state_and_goal(self):
        """Work out what we want the boat to do
        """
        boat_wind_angle = self.nav.angle_to_wind()

        if self.sailing_state != 'normal':
            # A tack/jibe is in progress
            if self.sailing_state == 'force_jibe_to_port_tack':
                goal_angle = 120
                self.continue_tack = boat_wind_angle < 0 or boat_wind_angle > 120
            elif self.sailing_state == 'force_jibe_to_stbd_tack':
                goal_angle = -120
                self.continue_tack = boat_wind_angle > 0 or boat_wind_angle < -120
            elif self.sailing_state == 'force_tack_to_port_tack':
                goal_angle = self.nav.beating_angle
                self.continue_tack = boat_wind_angle < goal_angle
            else:  # 'tack_to_stbd_tack'
                goal_angle = -self.nav.beating_angle
                self.continue_tack = boat_wind_angle > goal_angle

            if self.continue_tack:
                return self.sailing_state, self.nav.wind_angle_to_heading(goal_angle)
            else:
                # Tack completed
                self.log('info', 'Finished tack (%s)', self.sailing_state)
                self.sailing_state = 'normal'
                return self.sailing_state, self.nav.wind_angle_to_heading(goal_angle)


        on_port_tack = boat_wind_angle > 0
        # Ready about!
        if on_port_tack:
            if self.action == 'jibe' or \
                    (self.action == 'auto' and self.nav.jibe_to_turn):
                state = 'force_jibe_to_stbd_tack'
                goal_wind_angle = 180
            else:
                state = 'force_tack_to_stbd_tack'
                goal_wind_angle = -self.nav.beating_angle
        else:
            if self.action == 'jibe' or \
                    (self.action == 'auto' and self.nav.jibe_to_turn):
                state = 'force_jibe_to_port_tack'
                goal_wind_angle = -180
            else:
                state = 'force_tack_to_port_tack'
                goal_wind_angle = self.nav.beating_angle
        self.sailing_state = state
        self.log('info', 'Starting tack/jibe (%s)', state)
           
        return state, self.nav.wind_angle_to_heading(goal_wind_angle)
