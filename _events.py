import enum
from datetime import datetime


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

    def return_power_draw_events(self) -> list[Event]:
        """
        Returns the power draw events for this user as a list of Event objects
        """
        return [event for event in self._event_stream if event.event_type == EventType.REPORT_POWER_DRAW]
