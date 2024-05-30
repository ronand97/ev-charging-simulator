from datetime import datetime, timedelta

from _simulator import Simulator


def run_sim():
    now = datetime.now()
    next_whole_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

    sim = Simulator(population=10, start_time=next_whole_hour, end_time=next_whole_hour + timedelta(days=1))
    sim.run()


if __name__ == "__main__":
    run_sim()
