import enum
import logging
import math
from datetime import datetime, timedelta
from typing import Optional, Union

from user_archetype import UserArchetype


class EventType(str, enum.Enum):
    START_CHARGING = "START_CHARGING"
    STOP_CHARGING = "STOP_CHARGING"
    REPORT_SOC = "REPORT_SOC"
    REPORT_CHARGE_STATUS = "REPORT_CHARGE_STATUS"
    REPORT_POWER_DRAW = "REPORT_POWER_DRAW"


class Event:
    """
    Something that happens to a user at a given time
    where the state of the user is changed
    """

    def __init__(self, event_type: EventType, timestamp: datetime, **kwargs) -> None:
        self.event_type = event_type
        self.timestamp = timestamp
        for key, value in kwargs.items():
            setattr(self, key, value)


class EventStream:
    """
    A stream of events that happen to a user
    """

    def __init__(self) -> None:
        self._event_stream: list[Event] = []

    @property
    def last_reported_soc(self) -> Event:
        """
        Returns the last reported SOC event
        """
        for event in reversed(self._event_stream):
            if event.event_type == EventType.REPORT_SOC:
                return event

    def append(self, event: Event):
        """
        append generic event to stream
        """
        self._event_stream.append(event)

    def append_start_charging(self, timestamp: datetime, soc_pcnt: float):
        """
        append start charging event to stream
        """
        self._event_stream.append(Event(EventType.START_CHARGING, timestamp, soc_pcnt=soc_pcnt))

    def append_stop_charging(self, timestamp: datetime, soc_pcnt: float):
        """
        append stop charging event to stream
        """
        self._event_stream.append(Event(EventType.STOP_CHARGING, timestamp, soc_pcnt=soc_pcnt))

    def append_report_soc(self, timestamp: datetime, soc_pcnt: float):
        """
        append report SOC event to stream
        """
        self._event_stream.append(Event(EventType.REPORT_SOC, timestamp, soc_pcnt=soc_pcnt))

    def append_report_charge_status(self, timestamp: datetime, is_charging: bool):
        """
        append report charge status event to stream
        """
        self._event_stream.append(Event(EventType.REPORT_CHARGE_STATUS, timestamp, is_charging=is_charging))

    def append_report_power_draw(self, timestamp: datetime, power_draw_kw: float):
        """
        append report power draw event to stream
        """
        self._event_stream.append(Event(EventType.REPORT_POWER_DRAW, timestamp, power_draw_kw=power_draw_kw))

    def return_soc_events(self) -> list[Event]:
        """
        Returns the SOC events for this user as a list of Event objects
        """
        return [event for event in self._event_stream if event.event_type == EventType.REPORT_SOC]


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
        self._current_time = datetime.now()  # defaults to now
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

    @property
    def charging_time_required_for_target_soc(self) -> timedelta:
        """
        Returns the time required to reach the target state of charge
        """
        time_required = timedelta(hours=self.energy_required_for_target_soc / self.charger_kw)
        self.logger.debug(f"Time required to charge: {time_required}")
        return time_required

    @property
    def will_finish_charging_at(self) -> Union[datetime, None]:
        """
        Return the time at which the vehicle will finish charging
        Used for reporting and logging purposes
        """
        if not self.is_charging:
            return None
        else:
            return self.current_time + self.charging_time_required_for_target_soc

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
            will_finish_at = self.will_finish_charging_at
            self.logger.debug(f"{self.name} will finish charging at {will_finish_at}")

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
        # Scale the input to range from -2 to 2
        inverted_charge_pcnt = 100 - self.current_charge_pcnt
        scaled_input = (inverted_charge_pcnt / 5) - 10

        # Calculate the tanh of the scaled input
        tanh_output = math.tanh(scaled_input)

        # Scale and shift the output to range from 0.1 to 7
        charging_power = ((tanh_output + 1) / 2) * (self.charger_kw - 0.1) + 0.1

        return charging_power

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
