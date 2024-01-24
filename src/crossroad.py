from kisim import Entity, Logger
from graphics import *
import simpy
import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from enum import IntEnum
from collections import defaultdict, Counter, OrderedDict
from rich.progress import track
import argparse

directions = ['N', 'E', 'S', 'W']
start_pos = {'N': [0, 5], 'S': [11, 6], 'E': [5, 11], 'W': [6, 0]}
end_pos = {'N': [0, 6], 'S': [11, 5], 'E': [6, 11], 'W': [5, 0]}
crossroad_entry = {'N': [4, 5], 'S': [7, 6], 'E': [5, 7], 'W': [6, 4]}
turning_left_point = {'N': [6, 5], 'S': [5, 6], 'E': [5, 5], 'W': [6, 6]}
turning_left = {'N': 'E', 'S': 'W', 'E': 'S', 'W': 'N'}

class TrafficLightType(IntEnum):
    RANDOM_WAIT_TIME = 0
    STATIC_WAIT_TIME = 1
    COUNT_PREFERRED = 2
    TIME_SPEND_PREFERRED = 3


class Crossroad(Logger):
    """Simulation environment representing a crossroad.

    Attributes:
        road (List[List[int]]): A 2D list representing the road where cars move. It tracks the positions of cars on the crossroad.
        gr (Graphics): An instance of the graphics class representing the graphical environment.
        lights (Dict[str, str]): A dictionary representing the current state of traffic lights for each direction.
                                 Possible values are 'r' (red), 'g' (green), and 'o' (orange).
        lights_events (List[Event]): A list containing events for each traffic light to control their switching.
        cars_spawn_queue (Dict[str, List[Car]]): A dictionary representing the queue of cars waiting to enter the crossroad for each direction.
        cars (Dict[int, Car]): A dictionary containing instances of the Car class with their unique identifiers as keys.
        cars_in_queue (Dict[str, int]): A dictionary representing the count of cars currently waiting in the queue for each direction.
        cars_before_lights (Dict[str, int]): A dictionary representing the count of cars currently positioned before the traffic lights for each direction.
    """
     
    def __init__(self, graphics, factor=1.3, logEnabled=True):
        Logger.__init__(self, logEnabled)
        self.road = [[0 for i in range(12)] for j in range(12)]  # represents environment where cars move
        self.gr = graphics
        self.lights = {'N': 'r', 'E': 'r', 'S': 'r', 'W': 'r'}
        self.lights_events = [self.event(), self.event()]
        self.cars_spawn_queue = {'N': [], 'E': [], 'S': [], 'W': []}
        self.cars = {}
        self.cars_in_queue = {'N': 0, 'E': 0, 'S': 0, 'W': 0}
        self.cars_before_lights = {'N': 0, 'E': 0, 'S': 0, 'W': 0}

class RealtimeCrossroad(Crossroad, simpy.rt.RealtimeEnvironment, Logger):
    def __init__(self, graphics, factor=1.3, logEnabled=True):
        super().__init__(graphics, factor, logEnabled)
        simpy.rt.RealtimeEnvironment.__init__(self, factor=factor)

class FastSimulatedCrossroad(Crossroad, simpy.Environment, Logger):
    def __init__(self, graphics, factor=1.3, logEnabled=True):
        super().__init__(graphics, factor, logEnabled)
        simpy.Environment.__init__(self)

class Car(Entity):
    """Entity that navigates itself to its finish location."""

    def __init__(self, env, start, target_loc):
        super().__init__(env)
        self.start = start
        self.target_loc = target_loc
        self.speed = 0.4
        self.curr_pos = [-1, -1]
        self.progress = 0
        self.turning_left = True if turning_left[self.start] == self.target_loc else False
        self.start_time = self.env.now
        self.finish_time = -1
        self.spawn_event = self.env.event()

    def find_targets(self):
        """Finds main target points that each car must pass through.
        :return: list of 3 points [x,y].
        """
        targets = [[0, 0], [0, 0], [0, 0]]
        targets[0] = crossroad_entry[self.start]

        direction = self.get_dir(start_pos[self.start], targets[0])

        if self.turning_left:
            t = turning_left_point[self.start]
        else:
            t = [targets[0][0] + direction[0], targets[0][1] + direction[1]]

        targets[1] = t
        targets[2] = end_pos[self.target_loc]

        return targets

    def drive(self, target):
        """Move car on the 2D list and also move graphical representation of the car.
        :param target: target direction with 2 coordinates [x, y]
        :return: None
        """
        direction = self.get_dir(self.curr_pos, target)
        while self.curr_pos != target:
            # Wait for free road
            while self.env.road[self.curr_pos[0] + direction[0]][self.curr_pos[1] + direction[1]] != 0:
                yield self.env.timeout(self.speed / 6)
            # Move to next place on road
            idx = -self.id if self.turning_left else self.id
            self.env.road[self.curr_pos[0] + direction[0]][self.curr_pos[1] + direction[1]] = idx

            if isinstance(self.env, RealtimeCrossroad):
                for i in range(30):
                    self.env.gr.move_car(30, direction, self.id)
                    yield self.env.timeout(self.speed / 30)
            else:
                yield self.env.timeout(self.speed)

            self.env.road[self.curr_pos[0]][self.curr_pos[1]] = 0

            self.curr_pos = [self.curr_pos[0] + direction[0], self.curr_pos[1] + direction[1]]
            yield self.env.timeout(self.speed / 20)

    def lifetime(self):
        """Simulates car behaviour.
        Car has 4 main points that must pass. With simulation of traffic rules.
        1. Entering the crossroad
        2. Arrive before traffic lights
        3. Middle of the crossroad
        4. Finish
        :return: None
        """
        self.log(f"I live! [from: {self.start}, to: {self.target_loc}]")
        s = start_pos[self.start]

        self.env.cars_in_queue[self.start] += 1
        self.env.cars_before_lights[self.start] += 1
        if isinstance(self.env, RealtimeCrossroad):
            self.env.gr.change_car_queue_text(self.start, len(self.env.cars_spawn_queue[self.start]))

        if len(self.env.cars_spawn_queue[self.start]) > 1:
            yield self.spawn_event  # wait for free place in crossroads
        # 1. Get to the crossroads
        while self.env.road[s[0]][s[1]] != 0:
            yield self.env.timeout(self.speed / 2)  # else look for space
        
        self.env.cars_in_queue[self.start] -= 1

        if isinstance(self.env, RealtimeCrossroad):
            self.env.gr.display_car(self.start, "red", self.id, 'L' if self.turning_left else '')
            text = self.env.cars_in_queue[self.start] if self.env.cars_in_queue[self.start] > 0 else self.start
            self.env.gr.change_car_queue_text(self.start, text)

        
        self.env.road[s[0]][s[1]] = 1
        self.curr_pos = s

        t = self.find_targets()  # Find 3 targets the car go through

        self.progress += 1

        # look to list and awake car 1. in queue
        if len(self.env.cars_spawn_queue[self.start]) > 0:
            c = self.env.cars_spawn_queue[self.start].pop(0)
            if c is self and len(self.env.cars_spawn_queue[self.start]) > 0:
                c = self.env.cars_spawn_queue[self.start].pop(0)
            c.spawn_event.succeed()
        else:
            # if only one than remove self
            if len(self.env.cars_spawn_queue[self.start]) > 0:
                self.env.cars_spawn_queue[self.start].pop(0)

        # 2. Get to the crossroad line
        self.log(f"Going to crossroad line [from: {self.curr_pos}, to: {t[0]}]")
        yield self.env.process(self.drive(t[0]))
        self.log(f"At crossroad line: {self.curr_pos}")

        while not self.free_to_go():
            if self.env.lights[self.start] != 'g':
                yield self.env.lights_events[directions.index(self.start) - 2]  # Wait if red light
            yield self.env.timeout(self.speed)

        yield self.env.lights_events[directions.index(self.start) - 2]  # Wait if red light

        self.progress += 1
        # 3. Check traffic rules and go to the middle of the crossroad
        yield self.env.process(self.drive(t[1]))
        self.log(f"At the middle of the crossroad: {self.curr_pos}")
        self.env.cars_before_lights[self.start] -= 1

        # 4. Go to finish
        yield self.env.process(self.drive(t[2]))
        self.log(f"Finish! current_pos: {self.curr_pos}, end_loc: {end_pos[self.target_loc]}")
        self.env.road[self.curr_pos[0]][self.curr_pos[1]] = 0
        self.finish_time = self.env.now
        
        if isinstance(self.env, RealtimeCrossroad):
            self.env.gr.delete_car(self.id)

    #  Returns one of the four directions [-1, 0], [1, 0], [0, 1], [0, -1]
    def get_dir(self, from_loc, to_loc):
        direction = [1, 0] if from_loc[1] == to_loc[1] else [0, 1]
        if from_loc[0] > to_loc[0] or from_loc[1] > to_loc[1]:
            direction[0] = -1 * direction[0]
            direction[1] = -1 * direction[1]

        return direction

    def free_to_go(self):
        """Detect situation on the road if car is free to go.
        :return: bool - road is free
        """
        is_free = True
        if self.turning_left:  # Turning left so cars ahead have higher priority
            road_ahead = crossroad_entry[directions[directions.index(self.start) - 2]]
            x = road_ahead[0] - self.curr_pos[0]
            y = road_ahead[1] - self.curr_pos[1]
            if abs(x) > abs(y):
                x = 1 if x > 0 else -1
            else:
                y = 1 if y > 0 else -1
            if self.env.road[road_ahead[0]][road_ahead[1]] > 0 or self.env.road[road_ahead[0] + x][
                road_ahead[1] + y] > 0:
                self.log(f"Turning left so must wait")
                is_free = False
            dir = self.get_dir(start_pos[self.start], self.curr_pos)
            # If car 2 steps ahead than wait
            if self.env.road[2 * dir[0] + self.curr_pos[0]][2 * dir[1] + self.curr_pos[1]] != 0:
                is_free = False
        else:
            left = {'N': [1, 1], 'E': [1, -1], 'S': [-1, -1], 'W': [-1, 1]}
            crossing = {'N': 'EW', 'S': 'EW', 'E': 'NS', 'W': 'NS'}
            x = left[self.start][0] + self.curr_pos[0]
            y = left[self.start][1] + self.curr_pos[1]
            if self.env.road[x][y] < 0:
                is_free = False
            elif self.env.road[x][y] != 0:
                t_other = crossing[self.env.cars[self.env.road[x][y]].target_loc]
                if crossing[self.target_loc][0] == t_other or crossing[self.target_loc][1] == t_other:
                    is_free = False

        return is_free


class CarFactory(Entity):
    """Entity that creates cars."""

    def __init__(self, env, exp_lambda, seed, simulation_len):
        super().__init__(env)
        self.exp_lambda = exp_lambda
        self.simulation_len = simulation_len
        self.seed = seed
        self.car_count = simulation_len * 0.8

    def lifetime(self):
        """Spawns cars with exponential distributed time steps.
        Chooses uniformly where the car spawns and where is its finish.
        :return:
        """
        random.seed(self.seed)
        while True:
            start = random.randint(0, 3)
            target_loc = (start + random.randint(1, 3)) % 4
            car = Car(self.env, directions[start], directions[target_loc])
            self.env.cars[car.id] = car
            self.env.cars_spawn_queue[directions[start]].append(car)
            yield self.env.timeout(random.expovariate(self.exp_lambda))
            if len(self.env.cars) >= self.car_count:
                break


class TrafficLights(Entity):
    """Entity that switches lights."""
    def __init__(self, env, gr, mode):
        super().__init__(env)
        self.gr = gr
        self.mode = mode

    def get_wait_time(self):
        """Chooses waiting time in order to operation mode
        :return: waiting time
        """
        if self.mode == TrafficLightType.RANDOM_WAIT_TIME:
            return random.uniform(2, 9)
        elif self.mode == TrafficLightType.STATIC_WAIT_TIME:
            return 6
        elif self.mode == TrafficLightType.COUNT_PREFERRED or self.mode == TrafficLightType.TIME_SPEND_PREFERRED:
            return 0.5

    def count_submeans(self):
        """Count waiting time mean for horizontal and vertical part of crossroad.
        :return: mean for North and South, mean for West and East part
        """
        NS_mean = WE_mean = 0
        NS_cars = WE_cars = 0
        for c in self.env.cars.values():
            if c.progress <= 1:
                if c.start == 'N' or c.start == 'S':
                    NS_cars += 1
                    NS_mean += self.env.now - c.start_time
                else:
                    WE_cars += 1
                    WE_mean += self.env.now - c.start_time

        NS_mean = 0 if NS_cars == 0 else NS_mean / NS_cars
        WE_mean = 0 if WE_cars == 0 else WE_mean / WE_cars

        return NS_mean, WE_mean

    def lifetime(self):
        """Represents lifetime of traffic lights. Switches lights with given strategy.
        Traffic lights strategy.
        0 - random switching time
        1 - static time
        2 - prefer horizontal/vertical lights where is more cars
        3 - prefer horizontal/vertical lights where is higher mean waiting time
        :return: None
        """
        lights_idx = 0
        c = 'g'
        c1 = 'r'
        while True:

            if self.mode == TrafficLightType.RANDOM_WAIT_TIME or self.mode == TrafficLightType.STATIC_WAIT_TIME:
                lights_idx = random.randint(0, 1)
                c = 'r' if random.randint(0, 1) == 0 else 'g'
                c1 = 'g' if c == 'r' else 'r'
                if c == self.env.lights[directions[lights_idx]]:
                    c = 'g' if c != 'g' else 'r'
                    c1 = 'g' if c == 'r' else 'r'
            elif self.mode == TrafficLightType.COUNT_PREFERRED:
                NS = self.env.cars_before_lights['N'] + self.env.cars_before_lights['S']
                WE = self.env.cars_before_lights['W'] + self.env.cars_before_lights['E']
                if abs(NS - WE) >= 6:
                    lights_idx = 0 if NS > WE else 1
                elif NS == 0 and WE != 0:
                    lights_idx = 1
                elif NS != 0 and WE == 0:
                    lights_idx = 0

                if c == self.env.lights[directions[lights_idx]]:
                    yield self.env.timeout(self.get_wait_time() * 5)
                    continue
            elif self.mode == TrafficLightType.TIME_SPEND_PREFERRED:
                NS = self.env.cars_before_lights['N'] + self.env.cars_before_lights['S']
                WE = self.env.cars_before_lights['W'] + self.env.cars_before_lights['E']
                NS_mean, WE_mean = self.count_submeans()
                if abs(NS_mean - WE_mean) > (NS_mean + WE_mean) / 2 * 0.3:  # if diff between means is more than 20%
                    lights_idx = 0 if NS_mean > WE_mean else 1
                elif NS == 0 and WE != 0:
                    lights_idx = 1
                elif NS != 0 and WE == 0:
                    lights_idx = 0

                if c == self.env.lights[directions[lights_idx]]:
                    yield self.env.timeout(self.get_wait_time() * 2)
                    continue

            light1 = directions[lights_idx]
            light2 = directions[lights_idx - 2]

            self.log(f"Setting lights: {light1} and {light2} to {c}")

            light3 = directions[lights_idx - 1]
            light4 = directions[lights_idx - 3]

            self.log(f"Setting lights: {light3} and {light4} to {c1}")

            
            self.prepare_for_change(light1, light2, c, lights_idx)
            self.prepare_for_change(light3, light4, c1, lights_idx-1)

            yield self.env.timeout(1.2)  # orange signalization

            self.change_lights(light1, light2, c, lights_idx)
            self.change_lights(light3, light4, c1, lights_idx - 1)

            yield self.env.timeout(self.get_wait_time())

    def prepare_for_change(self, light1, light2, c, lights_idx):
        """Prepares for light change - switches traffic lights to orange value
        :param light1: character that represents light side ('N' - north, 'W','S','E')
        :param light2: character that is opposite to first position
        :param c: color that will be switched to
        :return: None
        """
        if self.env.lights[light1] == c:
            return

        if c == 'r':
            self.env.lights_events[lights_idx] = self.env.event()

        if gr is not None:
            if self.env.lights[light1] == 'r' and c == 'g':
                gr.traffic_lights[light1].light(col='ro')
                gr.traffic_lights[light2].light(col='ro')
            else:
                gr.traffic_lights[light1].light(col='o')
                gr.traffic_lights[light2].light(col='o')

        # Lights changes status, they turn to orange
        self.env.lights[light1] = 'o'
        self.env.lights[light2] = 'o'

    def change_lights(self, light1, light2, c, lights_idx):
        """Change lights color to red/green."""
        if c == 'g':
            self.env.lights_events[lights_idx].succeed()

        if self.env.lights[light1] == c:
            return

        self.env.lights[light1] = c
        self.env.lights[light2] = c
        
        if gr is not None:
            gr.traffic_lights[light1].light(col=c)
            gr.traffic_lights[light2].light(col=c)


def count_statistics(cars: list[Car]):
    """Count basic statistics

    :param cars: list of cars
    :return: string with basic statistical information
    """
    car_times = [c.finish_time - c.start_time for c in cars if c.finish_time > 0]
    
    return {"mean": np.mean(car_times), 
            "std": np.std(car_times), 
            "min": min(car_times), 
            "max": max(car_times), 
            "finished_cars_percentage": len(car_times) / len(cars)}


def get_cumulative_finished_car_count(cars: list[Car]):
    car_times = [c.finish_time - c.start_time for c in cars if c.finish_time > 0]
    sorted_finish_times = sorted(car_times)
    cumulative_counts = [i + 1 for i in range(len(sorted_finish_times))]
    
    return sorted_finish_times, cumulative_counts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Crossroad simulation with graphical or statistical mode.')
    import argparse

    parser = argparse.ArgumentParser(description='Crossroad simulation with graphical or statistical mode.')

    # Statistics mode options
    parser.add_argument("-s", "--stats", dest="count_statistics", action="store_true", default=False,
                        help="Enable statistical mode to collect simulation data.")
    parser.add_argument("-st", "--stats-sim-time", dest="st_sim_len", type=int, default=75,
                        help="Set the simulation time in seconds for statistical mode (default: 75 seconds).")
    parser.add_argument("-sn", "--stats-sim-rounds", dest="st_sim_rounds", type=int, default=300,
                        help="Set the number of simulation rounds for statistical mode (default: 300 rounds).")

    # Graphical mode options
    parser.add_argument("-gsl", "--graphical-sim-len", dest="gr_sim_len", type=int, default=30,
                        help="Set the simulation time in seconds for graphical mode (default: 30 seconds).")
    parser.add_argument("-tl", "--traffic-light-mode", dest="traffic_light_mode", type=int, choices=[mode.value for mode in TrafficLightType],
                        default=TrafficLightType.TIME_SPEND_PREFERRED.value,
                        help="Set the traffic lights mode. Choose from: 0 (Random wait time), 1 (Static wait time 6 seconds), 2 (Car count preferred), 3 (Time spend preferred). Default is 3.")
    parser.add_argument("-seed", dest="random_seed", type=int, default=random.randint(0, 10000),
                    help="Set the seed value for random number generation to generate cars. Defaults to a random integer between 0 and 10000 if not provided.")
    
    args = parser.parse_args()

    if not args.count_statistics:
        window = tk.Tk()
        gr = Graphics(window, size=50)
        sim = RealtimeCrossroad(gr)
        CarFactory(sim, exp_lambda=2, seed=args.random_seed, simulation_len=args.gr_sim_len)
        TrafficLights(sim, gr, mode=args.traffic_light_mode)
        sim.run(args.gr_sim_len)
        window.destroy()

    elif args.count_statistics:
        # Comparison between traffic lights modes
        gr = None
        simulation_len = 75
        counts = []
        rounds = 500
        seeds = [random.randint(0, rounds ** 2) for _ in range(rounds)]
        crossroad_time_spent = defaultdict(list)

        for i in track(range(rounds), description="Running crossroad simulation"):
            for mode in TrafficLightType:
                sim = FastSimulatedCrossroad(gr, 0.25, logEnabled=False)
                cf = CarFactory(sim, 2, seeds[i], simulation_len)
                tl = TrafficLights(sim, gr, mode)

                sim.run(simulation_len)
                sorted_crossroad_times = sorted([car.finish_time - car.start_time for car in sim.cars.values() if car.finish_time > 0])
                crossroad_time_spent[mode].extend(sorted_crossroad_times)

        fig1, ax1 = plt.subplots()
        fig2, ax2 = plt.subplots()
        crossroad_time_spent_mean = defaultdict(list)
        crossroad_time_spent_std = []
        
        for key, val in crossroad_time_spent.items():
            sorted_finished_times = sorted(val)
            counter = Counter(sorted_finished_times)
            times_counts = list(counter.values())
            cum_sum = np.cumsum(times_counts)
            ax1.plot(list(OrderedDict.fromkeys(sorted_finished_times)), cum_sum / rounds, label=key.name)
            crossroad_time_spent_mean[key.name] = np.mean(val)
            crossroad_time_spent_std.append(np.std(val))
        
        # Plot for the first subplot
        ax1.set_xlabel('Finish Time', fontsize=14)
        ax1.set_ylabel('Finished cars', fontsize=14)
        ax1.set_title('Cumulative time spent on crossroad', fontsize=20)
        # Include grid settings for the first subplot
        ax1.grid(True, linestyle='--', alpha=0.9, markevery=0.5)
        ax1.legend()

        # Plot mean time spent on crossroad
        colormap =  plt.cm.cividis
        ax2.bar(crossroad_time_spent_mean.keys(), crossroad_time_spent_mean.values(), yerr=crossroad_time_spent_std, ecolor="black", color=colormap(np.linspace(0, 1, len(crossroad_time_spent_mean.keys()))))
        ax2.set_xlabel('Traffic lights mode', fontsize=15)
        ax2.set_ylabel('Mean time', fontsize=15)
        ax2.set_title('Mean time spent on crossroad', fontsize=20)
        ax2.tick_params(axis='x', labelsize=12)
        ax2.grid(True, linestyle='--', alpha=0.9, markevery=0.05)
        ax2.yaxis.set_major_locator(MultipleLocator(4))

        plt.show()