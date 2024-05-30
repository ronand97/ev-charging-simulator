# What is this repo?
This repo contains some code I've written to simulate electric car charging
users charging their car batteries up at different times of the day based on
some charging archetypes. Each archetype can be found written as an entry
in `config_json.json`. There are 6 main python files:

- `_user_archetype.py` which simply reads in an archetype config and returns
as a nice python object with some sanitisation
- `_user.py` which represent a single person of a specific archetype and
provides tools and levers to start/stop charging their car, report the charge
status and so on. I tried to keep this decision-agnostic, ie the user should
just be told when to do things but not decide itself.
- `_events.py` helps me keep track of every time a user updates their state
by appending to a log stream of each user which can be queried to return
things like total power drawn, or the time at which they started/stopped
charging
- `_user_controller.py` exists to control multiple users at once and make the
decisions to change the user state e.g. when a car should start or stop
charging. I was thinking of a smart car charger automating the starting and
stopping of car charging based on certain criteria.
- `_simulator.py` which simulates the real world and just steps through time.
- `run_simulator.py` which is the entry point to the whole sim and designed
to be the file that is run.

# How to run this code?
- install requirements.txt using python >=3.9 into a virtualenv or equivalent
- run `run_simulation.py`

# What happens when I run the simulator?
- Each user config is loaded in and we spawn multiple `User` instances
based on population size. These Users are given to a UserController
for orchestration. Each User reports their current SOC into their event
stream.
- The simulator steps through timesteps whilst asking the Controller to
poll each User to:
  - Log current SOC of the battery (whether it is charging, % charged, kW of power draw)
  - Begin or end charging based on the time of day and state of battery
- Once the simulation end time has been reached, two plots are generated:
  1. A plot showing the charging curve of each car over time (% charged on the y-axis) split by archetype group (but not split by individual user)
  2. A plot showing the overall power consumption from the whole population split by archetype type

# Assumptions
- I assumed you can break the archetype config mostly into: charging-time
parameters; driving-time parameters. I ignored the driving-time parameters.
- I mainly relied on the plug in/out times; plug in SOC percent; charger kW; battery kWh; and target SOC pcnt
- I assumed the `Charging duration (hrs)` was not important to an MVP and I'm still unsure what this parameter is

# Other thoughts
- I mainly spent time on building state-changing functionality within the User Controller and User, because by providing the correct information and state-changing methods it is now quite extensible to any scenario. I think this can be tricky in real life as the "User" can be a dumb object waiting to be told what to do, or it could be a car with in-built controller that can dictate from the charger how much charge it should be given vs the other way round.
- I've only focused on charging time, but added no functionality based on regular driving. That means the simulator starts, each car battery charges to full, and then nothing else happens.
- I have no concept of what day it is and just assumes everyone plugs in every day at the given time (so I didn't use plug-in frequency)

# End use
I thought about how the energy market trading might work. For example
axle energy brokers a trade to drain car batteries between 5 and 6pm. So
things that have to happen:
- Current SOC is reportable
- Car needs to be told to start charging and stop charging ahead of time
- Car needs to be able to report on actual power drawn/discharged to
prove to the markets that you provided that power after the fact
- Controller controls this behaviour (I believe this is essentially a simple model of how axle manages multiple "Assets" (Users))

I generated the plots to aid with choosing energy assets that could be suitable
for orchestration for energy market trading. By examining charge curves
of cars it is easier to predict the starting charge time required to add a certain
% of battery on (ie it will be quicker to add 10% when the car is low on charge).
By examining a plot of total energy usage in kW by all cars it becomes easier
to predict when peak energy usage might happen and how to leverage that
information, e.g.
- shift charging to greener/cheaper grid times
- identify assets that will be fully charged by _x_ time
- identify assets that will be plugged in between _x_ and _y_ times
