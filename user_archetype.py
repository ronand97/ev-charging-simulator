import enum
import json
from datetime import datetime

class EventType(str, enum.Enum):
    START_CHARGING = "start_charging"
    STOP_CHARGING = "stop_charging"

class Event:
    """
    Class to define an event. An event can be
    * start charging
    * stop charging
    and has a timestamp
    """
    def __init__(self, event_type: EventType, timestamp: datetime) -> None:
        self.event_type = event_type
        self.timestamp = timestamp
    

class UserArchetype:

    def __init__(
        self,
        number: int,
        name: str,
        pcnt_population: float,
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
    ) -> None:
        """
        Holds state about a given user archetype. Inited with
        standard parameters for a user archetype that are used
        by a controller to control behaviour.
        """
        # init properties
        self.number = number
        self.name = name
        self.pcnt_population = pcnt_population
        self.miles_per_year = miles_per_year
        self.battery_kwh = battery_kwh
        self.efficiency_miles_per_kwh = efficiency_miles_per_kwh
        self.plug_in_frequency_per_day = plug_in_frequency_per_day
        self.charger_kw = charger_kw
        self.plug_in_time_hr = self._sanitise_str_time(plug_in_time_hr)
        self.plug_out_time_hr = self._sanitise_str_time(plug_out_time_hr)
        self.target_soc_pcnt = target_soc_pcnt
        self.kwh_per_year = kwh_per_year
        self.kwh_per_plug_in = kwh_per_plug_in
        self.plug_in_soc_pcnt = plug_in_soc_pcnt
        self.soc_requirement_pcnt = soc_requirement_pcnt
        self.charging_duration_hr = charging_duration_hr

        # state properties
        self.event_stream: list[Event] = []
        self.is_charging: bool = False

    @property
    def will_finish_charging_at(self) -> datetime:
        """
        eg need to go from 60-80%
        know the rate of charge
        know the current SOC
        know the target, so can get the delta
        convert the delta into a kW value
        then divide by the charger kW to get the time to charge
        add it to the event stream of start charging

        calculate from most recent start event and charged %
        means it can handle multiple start events
        """
        if not self.is_charging:
            return None
        else:
            # get the most recent start charging event
            start_charging_events = [event for event in self.event_stream if event.event_type == EventType.START_CHARGING]
            if not start_charging_events:
                return None
            else:
                start_charging_event = start_charging_events[-1]
                time_since_start_charging = datetime.now() - start_charging_event.timestamp
                time_to_charge = self.charging_duration_hr - time_since_start_charging.total_seconds() / 3600
                return datetime.now() + timedelta(hours=time_to_charge)



    def _sanitise_str_time(self, str_time: str) -> datetime.time:
        """
        Converts string time formatted as "H:MM AM/PM" to datetime object
        """
        return datetime.strptime(str_time, "%I:%M %p").time()
    
    def start_charging(self):
        """
        Start charging the vehicle
        """
        if self.is_charging:
            print(f"{self.name} is already charging")
            return
        else:
            print(f"Starting to charge {self.name}")
            self.is_charging = True
            self.event_stream.append(Event(EventType.START_CHARGING, datetime.now()))
    
    def stop_charging(self):
        """
        Stop charging the vehicle
        """
        if not self.is_charging:
            print(f"{self.name} is already not charging")
            return
        else:
            print(f"Stopping charging {self.name}")
            self.is_charging = False
            self.event_stream.append(Event(EventType.STOP_CHARGING, datetime.now()))



if __name__ == "__main__":
    from pathlib import Path
    import json

    config_fp = Path(__file__).parent / "config_json.json"
    with open(config_fp, "r") as f:
        config = json.load(f)
    users = []
    for user_config in config:
        users.append(UserArchetype(**user_config))
