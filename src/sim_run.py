import simulator

def test_simulator():
    sim = simulator.Simulator()
    sim.config_setup("../configs/d2_b3.json")
    sim.show_tree()
    sim.run()

test_simulator()
    