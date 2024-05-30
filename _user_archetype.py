import logging
from datetime import datetime, timedelta
from typing import Optional


def sanitise_str_time(str_time: str) -> datetime.time:
    """
    Converts string time formatted as "H:MM AM/PM" to datetime object
    """
    return datetime.strptime(str_time, "%I:%M %p").time()


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
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """
        Holds initial user archetype parameters and does any necessary
        parameter sanitisation
        """
        self.logger = logger if logger is not None else logging.getLogger(__name__)

        # init properties
        self.number = number
        self.name = name
        self.pcnt_population = pcnt_population
        self.miles_per_year = miles_per_year
        self.battery_kwh = battery_kwh
        self.efficiency_miles_per_kwh = efficiency_miles_per_kwh
        self.plug_in_frequency_per_day = plug_in_frequency_per_day
        self.charger_kw = charger_kw
        plug_in_time_hr = sanitise_str_time(plug_in_time_hr)
        plug_out_time_hr = sanitise_str_time(plug_out_time_hr)
        self.plug_in_datetime = datetime.combine(datetime.now(), plug_in_time_hr)
        self.plug_out_datetime = self._calculate_plug_out_datetime(self.plug_in_datetime, plug_out_time_hr)
        self.target_soc_pcnt = target_soc_pcnt
        self.kwh_per_year = kwh_per_year
        self.kwh_per_plug_in = kwh_per_plug_in
        self.plug_in_soc_pcnt = plug_in_soc_pcnt
        self.soc_requirement_pcnt = soc_requirement_pcnt
        self.charging_duration_hr = charging_duration_hr

    def _calculate_plug_out_datetime(self, plug_in_datetime: datetime, plug_out_time: datetime.time) -> datetime:
        """
        Plug in time can be PM and plug out time can also be PM
        but plug in time can be PM and plug out time is AM which
        means the following day
        So need to add a day on if plug out time is before plug in time
        """
        plug_in_time = plug_in_datetime.time()
        if plug_out_time < plug_in_time:
            self.logger.info(
                f"Plug out time is earlier than plug-in time for {self.name}. Assuming plug out time references following day"
            )
            return datetime.combine(plug_in_datetime.date() + timedelta(days=1), plug_out_time)
        else:
            return datetime.combine(plug_in_datetime.date(), plug_out_time)
