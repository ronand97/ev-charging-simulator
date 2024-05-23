# a file to orchestrate multiple user_archetype instances
# eg tell them to charge at a certain time
from datetime import datetime

from user_archetype import UserArchetype


class UserController:
    def __init__(self, user_archetypes: list) -> None:
        self.user_archetypes = user_archetypes

    def update_charge_status(self, current_time: datetime.time) -> None:
        """
        Updates the charge status of all user archetypes
        """
        for user in self.user_archetypes:
            if user.plug_in_time_hr <= current_time <= user.plug_out_time_hr:
                user.start_charging()
            else:
                user.stop_charging()

if __name__ == "__main__":
    from pathlib import Path
    import json

    config_fp = Path(__file__).parent / "config_json.json"
    with open(config_fp, "r") as f:
        config = json.load(f)
    users = []
    for user_config in config:
        users.append(UserArchetype(**user_config))
    
    controller = UserController(users)
    controller.update_charge_status(datetime.now().time())