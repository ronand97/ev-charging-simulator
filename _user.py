import logging
import math
from datetime import datetime, timedelta
from typing import Optional

from _events import Event, EventStream, EventType
from _user_archetype import UserArchetype


class User(UserArchetype):
    def __init__(
        self,
        number: int,
        name: str,
        pcnt_population: int,
        miles_per_year: float,
        battery_kwh: float,
        efficiency_miles_per_kwh: float,
        plug_in_frequency_per_day: float,
        charger_kw: float,
        plug_in_time_hr: str,
        plug_out_time_hr: str,
        target_soc_pcnt: float,
        kwh_per_year: float,
        kwh_per_plug_in: float,
        plug_in_soc_pcnt: float,
        soc_requirement_pcnt: float,
        charging_duration_hr: float,
        current_time: datetime = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Holds state about a given user. Provides methods to
        interact with the user state.
        """
        super().__init__(
            number,
            name,
            pcnt_population,
            miles_per_year,
            battery_kwh,
            efficiency_miles_per_kwh,
            plug_in_frequency_per_day,
            charger_kw,
            plug_in_time_hr,
            plug_out_time_hr,
            target_soc_pcnt,
            kwh_per_year,
            kwh_per_plug_in,
            plug_in_soc_pcnt,
            soc_requirement_pcnt,
            charging_duration_hr,
            logger,
        )

        # state properties
        self._current_time = current_time if current_time else datetime.now()
        self.event_stream: EventStream = EventStream()
        self.is_charging: bool = False
        self.current_charge_pcnt = self.plug_in_soc_pcnt

        # initial state logged
        self.event_stream.append(Event(EventType.REPORT_SOC, self._current_time, soc_pcnt=self.current_charge_pcnt))

    @property
    def current_time(self) -> datetime:
        return self._current_time

    @current_time.setter
    def current_time(self, new_time: datetime):
        self._current_time = new_time

    @property
    def should_be_charging(self) -> bool:
        """
        Returns whether the vehicle should be charging
        """
        time_to_charge = self.plug_in_datetime <= self.current_time <= self.plug_out_datetime
        battery_less_than_target = self.current_charge_pcnt < self.target_soc_pcnt
        return time_to_charge and battery_less_than_target

    @property
    def energy_required_for_target_soc(self) -> float:
        """
        Returns the energy required to reach the target state of charge
        """
        target_energy = self.battery_kwh * (self.target_soc_pcnt / 100)  # target energy in kwh
        current_energy = self.battery_kwh * (self.current_charge_pcnt / 100)  # current energy in kwh
        assert (
            target_energy >= current_energy
        ), "Target energy should be greater than or equal to current energy (probably)"
        self.logger.debug(f"Energy required for target SOC: {target_energy - current_energy}")
        return target_energy - current_energy

    def start_charging(self):
        """
        Start charging the vehicle
        """
        if self.is_charging:
            self.logger.debug(f"{self.name} is already charging")
            return
        else:
            self.logger.debug(f"Starting to charge {self.name}")
            self.is_charging = True
            self.event_stream.append_start_charging(timestamp=self.current_time, soc_pcnt=self.current_charge_pcnt)
            self.event_stream.append_report_soc(timestamp=self.current_time, soc_pcnt=self.current_charge_pcnt)

    def stop_charging(self):
        """
        Stop charging the vehicle
        """
        if not self.is_charging:
            self.logger.debug(f"{self.name} is already not charging")
            return
        else:
            self.logger.debug(f"Stopping charging {self.name}")
            self.is_charging = False
            self.event_stream.append_stop_charging(timestamp=self.current_time, soc_pcnt=self.current_charge_pcnt)
            self.event_stream.append_report_soc(timestamp=self.current_time, soc_pcnt=self.current_charge_pcnt)

    @property
    def _current_charger_kw(self) -> float:
        """
        Apply tanh scaling to charger kw based on
        current charge percentage assuming that listed
        charger kw is the peak charger kw

        Naive implementation not considering other factors
        """
        inverted_charge = 1 - (self.current_charge_pcnt / 100)
        tanh_output = math.tanh(inverted_charge)

        # tanh operates between -1 and 1, shift between 0 and 1
        shifted_tanh = 0.5 * (tanh_output + 1)
        return self.charger_kw * shifted_tanh

    def _update_soc(self):
        """
        Calculate current battery percentage based on time
        since last reported SOC
        """
        last_reported_soc = self.event_stream.last_reported_soc
        time_since_last_report: timedelta = self.current_time - last_reported_soc.timestamp
        if self.is_charging:
            should_have_added_kwh = self._current_charger_kw * (time_since_last_report.total_seconds() / 3600)
            self.current_charge_pcnt += 100 * (should_have_added_kwh / self.battery_kwh)
            self.logger.debug(
                f"{last_reported_soc.soc_pcnt=}, {time_since_last_report=}, {should_have_added_kwh=}, {self.current_charge_pcnt=}"
            )

    def update_and_report_soc(self):
        """
        Update and log the state of charge of the vehicle.
        Also logs if the vehicle is charging, and if so,
        the power draw
        """
        self._update_soc()
        self.event_stream.append_report_soc(self.current_time, self.current_charge_pcnt)
        self.event_stream.append_report_charge_status(self.current_time, self.is_charging)
        if self.is_charging:
            self.event_stream.append_report_power_draw(self.current_time, self._current_charger_kw)
        self.logger.debug(f"Reporting SOC: {self.current_charge_pcnt}")
