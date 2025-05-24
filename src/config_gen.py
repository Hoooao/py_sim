import numpy as np
import json
import matplotlib.pyplot as plt
from scipy.stats import spearmanr, pearsonr

def generate_sticky_expo_dist(
    num_samples=100,
    expo_scale=1.0,
    norm_mean=3.0,
    norm_std=1.0
):
    result = []
    expo_dist = np.random.exponential(scale=expo_scale, size=num_samples)

    rep_factors = np.random.normal(loc=norm_mean, scale=norm_std, size=num_samples)
    for x,y in zip(expo_dist, rep_factors):
        result.append([int(round(x)),max(1, int(round(y)))])

    return result

# onyx paper says owd is ~50
# print(generate_sticky_expo_dist(1000, 1000.0, 6.0, 1.0))


def generate_links(branching, cur_node, cur_depth):
    # get the geometric series
    last_node_idx = (branching**(cur_depth+1) - 1) // (branching - 1) - 1
    return last_node_idx

# print(generate_links(10, 0, 2))

def generate_dependant_group(json_file, x_group):
    # we create a latency list that is "dependant" on the x_group
    with open(json_file) as f:
        config = json.load(f)
    x_lats = config["latency_groups"][x_group]["lats"]
    y_lats = [[int(lat * 0.2), sticky] for [lat,sticky] in x_lats]
    #plots both
    x = [lat for [lat, _] in x_lats]
    x = sorted(x)
    y = [lat for [lat, _] in y_lats]
    y = sorted(y)

    plt.plot(x, label=f"Group {x_group}")
    plt.plot(y, label=f"Group {x_group} dependant")
    plt.legend()
    plt.xlabel("x")
    plt.ylabel("Latency (ms)")
    plt.title(f"Latency group {x_group} and dependant group")
    # save the plot
    plt.savefig(f"latency_group_{x_group}.png")
    plt.show()
    return y_lats
print(generate_dependant_group("../configs/d2_b3.json", "LG1"))

