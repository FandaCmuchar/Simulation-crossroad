# Crossroad Simulation

This project implements an event-driven simulation of a crossroad using the Tkinter graphical library. The simulation allows for both graphical and statistical modes to analyze and visualize crossroad traffic.

## Installation

### Prerequisites

Make sure you have Python and Poetry installed. If not, you can install Poetry by following the instructions [here](https://python-poetry.org/docs/#installation).

### Steps

1. Clone the repository to your local machine:

   ```bash
   git clone https://github.com/your-username/crossroad-simulation.git
   ```

2. Navigate to the project directory:
   ```bash
    cd crossroad-simulation
   ```

3. Install the project dependencies using Poetry:
    ```bash
        poetry install
    ```

    This command installs all the required packages specified in the `pyproject.toml` file.

### Usage
To run the simulation, use the following command in your terminal:
```bash
    poetry run python src/crossroad.py [options]
```

#### Options
##### Statistical Mode
- `-s`, `--stats`: Enable statistical mode to collect simulation data.
- `-st`, `--stats-sim-time`: Set the simulation time in seconds for statistical mode (default: 75 seconds).
- `-sn`, `--stats-sim-rounds`: Set the number of simulation rounds for statistical mode (default: 300 rounds).
##### Graphical Mode
- `-gsl`, `--graphical-sim-len`: Set the simulation time in seconds for graphical mode (default: 30 seconds).
- `-tl`, `--traffic-light-mode`: Set the traffic lights mode. Choose from: 0 (Random wait time), 1 (Static wait time 6 seconds), 2 (Car count preferred), 3 (Time spend preferred). Default is 3.
- `-seed`: Set the seed value for random number generation to generate cars. Defaults to a random integer between 0 and 10000 if not provided.

### Examples
#### Run Statistical Mode
```bash
    poetry run python src/crossroad.py -s -st 100 -sn 500
```
This command runs the simulation in statistical mode with a simulation time of 100 seconds and 500 rounds.

#### Run Graphical Mode
```bash
    poetry run python src/crossroad.py -gsl 60 -tl 2 -seed 1234
```
This command runs the simulation in graphical mode with a simulation time of 60 seconds, traffic lights mode set to Car count preferred (2), and a specific seed value of 1234 for random number generation.