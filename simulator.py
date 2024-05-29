# simulator that steps through times
# defines population size
# defines user archetypes
# defines controller
# simulator should step through time and call controller to tell user archetypes to charge
# any data that is useful should come back out to the simulator

# this file simulates what happens in the real life

# stretch: simulate what happens not during charging hours ie how much people use their cars

from datetime import datetime, timedelta
import time
from user import User
from user_controller import UserController
import plotly.express as px
import logging
from typing import Optional


logging.basicConfig(level=logging.INFO)


class Simulator:
    def __init__(self, user_controller: UserController, start_time: datetime, end_time: datetime, logger: Optional[logging.Logger] = None) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.user_controller = user_controller
        self.current_time = start_time
        self.end_time = end_time
        self.hours_delta = (self.end_time - self.current_time).seconds // 3600

    def _step(self):
        """
        Steps the simulator forward in time by 1 hour
        """
        self.user_controller.update_soc(self.current_time)
        self.user_controller.update_charge_status(self.current_time)
        self.current_time += timedelta(hours=1)
    
    def _plot_soc_over_time(self) -> None:
        """
        Plot:
        - x: time
        - y: soc % 
        - color: user
        """
        soc_events = self.user_controller.get_soc_events_df()
        fig = px.line(
            data_frame=soc_events,
            x="Timestamp",
            y="Charge Percentage",
            color="User",
            markers=True
        )
        fig.show()
    
    def _plot_charge_events(self) -> None:
        """
        Plot:
        - x: time
        - y: charge percentage
        - color: user

        """
        charge_events = self.user_controller.get_charge_events_df()
        fig = px.bar(
            data_frame=charge_events,
            x="Timestamp",
            y="Charge Percentage",
            color="User",
        )
        fig.show()

    def run(self):
        """
        Runs the simulation
        """
        for hour in range(self.hours_delta):
            self.logger.info(f"Simulating hour {hour+1}/{self.hours_delta}")
            self._step()
            time.sleep(.2)
        self._plot_soc_over_time()
        # self._plot_charge_events()

if __name__ == "__main__":
    
    from pathlib import Path
    import json
    import logging
    logger = logging.getLogger()

    config_fp = Path(__file__).parent / "config_json.json"
    with open(config_fp, "r") as f:
        config = json.load(f)
    users = []
    for user_config in config:
        users.append(User(**user_config | {"logger": logger}))
    
    controller = UserController(users)
    simulator = Simulator(controller, datetime.now(), (datetime.now() + timedelta(hours=12)), logger=logger)
    simulator.run()