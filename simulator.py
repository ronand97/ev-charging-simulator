# simulator that steps through times
# defines population size
# defines user archetypes
# defines controller
# simulator should step through time and call controller to tell user archetypes to charge
# any data that is useful should come back out to the simulator

# stretch:

def Simulator:
    def __init__(self, user_controller: UserController, start_time: datetime.time, end_time: datetime.time) -> None:
        self.user_controller = user_controller
        self.current_time = start_time
        self.end_time = end_time

    def step(self):
        """
        Steps the simulator forward in time by 1 hour
        """
        self.user_controller.update_charge_status(self.current_time)
        self.current_time += timedelta(hours=1)
        if self.current_time >= self.end_time:
            print("Simulation over")
            return
        else:
            self.step()
