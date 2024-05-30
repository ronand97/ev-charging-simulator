from datetime import datetime, timedelta

from _simulator import Simulator

sim_start = datetime.now()
next_whole_hour = (sim_start + timedelta(hours=1)).replace(
    minute=0, second=0, microsecond=0
)  # starting from next whole hour (or similar) makes end charts render nicer on the x-axis
sim_end = next_whole_hour + timedelta(days=1)

population_size = 1000
time_step = timedelta(minutes=1)  # how often to update the simulation

sim = Simulator(population=population_size, start_time=next_whole_hour, end_time=sim_end)
sim.run(td=time_step)
