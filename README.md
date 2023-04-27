# eee4121f-b Lab 1

This README includes the steps needed to run the tcp.py experiments.

## Installation

Install the python statistics module
```
sudo apt-get install update
sudo apt-get install python-statistics
```

## Running TCP experiments
There are three experiments run for each TCP algorithm. For each experiment, changes are made in the *run.sh* bash script. Changes are made to this section of code:
```python
# You can change these parameters:
bwhost=1000
qsize=100
cong=cubic
```
### TCP Reno
#### Experiment 1: No changes need to be made
#### Experiment 2: Uncomment `--cong=$cong \` under the comment `#Now start the experiment and load the parameters`
#### Experiment 3: Change `qsize` to 20

### TCP Cubic
#### Experiment 1: No changes need to be made
#### Experiment 2: Uncomment `--cong=$cong \` under the comment `#Now start the experiment and load the parameters`
#### Experiment 3: Change `qsize` to 20

### TCP BBR
#### Experiment 1: No changes need to be made
#### Experiment 2: Uncomment `--cong=$cong \` under the comment `#Now start the experiment and load the parameters`
#### Experiment 3: Change `qsize` to 20
