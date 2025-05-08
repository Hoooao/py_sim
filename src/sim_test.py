import simulator

def test_simulator():
    sim = simulator.Simulator()
    sim.config_setup("../configs/d3_b10.json")
    sim.show_tree()
    sim.run()

test_simulator()
    