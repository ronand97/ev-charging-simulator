import copy
import json
import logging
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import plotly.express as px

from _user import User
from _user_controller import UserController

logging.basicConfig(level=logging.INFO)


class Simulator:
    def __init__(
        self, population: int, start_time: datetime, end_time: datetime, logger: Optional[logging.Logger] = None
    ) -> None:
        """
        :param population: int: number of EVs to simulate
        """
        self.population = population
        self.logger = logger or logging.getLogger(__name__)
        self.current_time = start_time
        self.end_time = end_time
        self._time_delta = end_time - start_time
        self.user_controller = self._load_population_of_users()

    def _load_population_of_users(self) -> UserController:
        """
        eg if we have 1k people we know 40% are regular users, 20% are heavy users etc

        To do this will just do an initial load of the archetypes we have
        then duplicate them to make up the population as defined by
        each archetype

        Bit of a messy implementation as ideally we would figure out first
        how many we need then instantiate that many thus splitting the
        population creation from the user creation but for now this will do
        """
        # initial load of archetypes that we have
        config_fp = Path(__file__).parent / "config_json.json"
        with open(config_fp, "r") as f:
            config = json.load(f)
        users = []
        for user_config in config[:]:
            users.append(User(**user_config | {"logger": self.logger, "current_time": self.current_time}))
        assert 100 == sum([user.pcnt_population for user in users])  # sanity check

        # duplicate the archetypes to make up the population
        population = []
        for user in users:
            # append a deepcopy of user to the population list by the number of times defined by pcnt_population
            n_users = math.ceil(self.population * (user.pcnt_population / 100))
            to_add = [copy.deepcopy(user) for _ in range(n_users)]
            population.extend(to_add)
        return UserController(population)

    def _step(self):
        """
        Ask the controller to update all the states
        """
        self.user_controller.update_soc(self.current_time)
        self.user_controller.update_charge_status(self.current_time)

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
            markers=True,
            title=f"SOC Over Time for each user in the population (n={self.population})",
        )
        fig.show()

    def _plot_population_energy_usage(self) -> None:
        """
        Plot:
        - x: time
        - y: total energy usage
        - color: user
        """
        energy_usage = self.user_controller.get_energy_usage_per_hour()
        fig = px.bar(
            data_frame=energy_usage,
            x="Timestamp",
            y="Power Draw (kW)",
            color="User",
            title=f"Summed energy usage over all population (n={self.population})",
        )
        fig.show()

    def run(self, td: timedelta = timedelta(minutes=1)):
        """
        Runs the simulation in time intervals
        """
        while self.current_time < self.end_time:
            self._step()
            self.current_time += td
        self._plot_soc_over_time()
        self._plot_population_energy_usage()
