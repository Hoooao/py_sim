import simulator
import common
import logging
import json

logging.disable(logging.CRITICAL) # disable all logging
common.TESTING = True

def compare_results(res, res_file):
    with open(res_file) as f:
        expected = json.load(f)
        # make key ints
        res_expected = {}
        for key, value in expected.items():
            res_expected[int(key)] = value
    base_name = res_file.split("/")[-1].split(".")[0]
    # turn to json format
    if res == res_expected:
        print(f"{base_name}: PASSED")
    else:
        print(f"{base_name}: FAILED")
        print(f"Expected: {res_expected}")
        print(f"Got: {res}")
    
def test_simulator_simple_no_spray():
    common.TESTING_SPRAY = False
    sim = simulator.Simulator()
    sim.config_setup("../configs/tests/test_simple/test_simple.json")
    sim.run()
    res = sim.aggergate_results()
    compare_results(res, "../configs/tests/test_simple/test_simple_res_no_spray.json")
    

def test_simulator_simple_spray():
    common.TESTING_SPRAY = True
    sim = simulator.Simulator()
    sim.config_setup("../configs/tests/test_simple/test_simple.json")
    sim.run()
    res = sim.aggergate_results()
    compare_results(res, "../configs/tests/test_simple/test_simple_res_spray.json")

TEST_LIST = {
    "test_simulator_simple_no_spray": {
        "config": "../configs/tests/test_simple/test_simple.json",
        "res": "../configs/tests/test_simple/test_simple_res_no_spray.json",
        "function": test_simulator_simple_no_spray
    },
    "test_simulator_simple_spray": {
        "config": "../configs/tests/test_simple/test_simple.json",
        "res": "../configs/tests/test_simple/test_simple_res_spray.json",
        "function": test_simulator_simple_spray
    }
}


def run_tests():
    for test_name, test in TEST_LIST.items():
        print(f"Running {test_name}...")
        test["function"]()
        print(f"{test_name} done.")
    print("All tests done.")
    print("=== Simulation done ===")
run_tests()