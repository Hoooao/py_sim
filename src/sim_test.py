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

def test_simulator_simple_spray():
    common.TESTING_SPRAY = True

def test_simulator_test_dependent_no_spray():
    common.TESTING_SPRAY = False

def test_simulator_test_dependent_spray():
    common.TESTING_SPRAY = True
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
    },
    "test_simulator_test_dependent_no_spray": {
        "config": "../configs/tests/test_dependent/test_dependent.json",
        "res": "../configs/tests/test_dependent/test_dependent_res_no_spray.json",
        "function": test_simulator_test_dependent_no_spray
    },
    "test_simulator_test_dependent_spray": {
        "config": "../configs/tests/test_dependent/test_dependent.json",
        "res": "../configs/tests/test_dependent/test_dependent_res_spray.json",
        "function": test_simulator_simple_spray
    },
}

def run_test(config_f, res_f, func):
    SAVE_RESULT = False
    func()
    sim = simulator.Simulator()
    sim.config_setup(config_f)
    sim.run()
    res = sim.aggergate_results()
    if SAVE_RESULT:
        with open(res_f, "w") as f:
            json.dump(res, f, indent=4)
        print(f"Results saved to {res_f}")
    else:
        compare_results(res, res_f)

def run_tests():
    for test_name, test in TEST_LIST.items():
        print(f"Running {test_name}...")
        run_test(test["config"], test["res"], test["function"])
    print("All tests done.")
    print("=== Simulation done ===")
run_tests()