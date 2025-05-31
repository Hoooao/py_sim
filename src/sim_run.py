import simulator
import logging
logging.disable(logging.DEBUG) # disable all logging

def run_simulator():
    sim = simulator.Simulator()
    sim.config_setup("../configs/d3_b10_dependent.json")
    sim.show_tree()
    sim.run()

run_simulator()
    