# a file to orchestrate multiple user_archetype instances
# eg tell them to charge at a certain time
from datetime import datetime

import pandas as pd

from user import User


class UserController:
    def __init__(self, user_archetypes: list) -> None:
        self.user_archetypes = user_archetypes

    def update_charge_status(self, current_time: datetime) -> None:
        """
        Tells user whether to start or stop charging
        """
        for user in self.user_archetypes:
            try:
                user.current_time = current_time
                if user.should_be_charging:
                    user.start_charging()
                elif not user.should_be_charging and user.is_charging:
                    user.stop_charging()
            except Exception as e:
                user.logger.error(f"Error updating charge status for user {user.name}: {e}")
                continue

    def update_soc(self, current_time: datetime) -> None:
        """
        Updates the SOC of the user
        """
        for user in self.user_archetypes:
            try:
                user.current_time = current_time
                user.update_and_report_soc()
            except Exception as e:
                user.logger.error(f"Error updating SOC for user {user.name}: {e}")
                continue

    def get_soc_events_df(self) -> pd.DataFrame:
        """
        Returns the SOC events for all users as a dataframe
        for easy analysis
        """
        _events: list[pd.DataFrame] = []
        for user in self.user_archetypes:
            soc_events = user.event_stream.return_soc_events()
            if soc_events:
                data = {
                    "Event": [event.event_type.name for event in soc_events],
                    "Charge Percentage": [event.soc_pcnt for event in soc_events],
                    "Timestamp": [event.timestamp for event in soc_events],
                }
                _events.append(pd.DataFrame(data).assign(User=user.name))
        return pd.concat(_events)
