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

    col = 100
    for i in range(len(result)):
        print("[{},{}]".format(result[i][0], result[i][1]), end="")
        if (i + 1) % col == 0:
            print(",")
        else:
            print(", ", end="")

# onyx paper says owd is ~50, spike 90pct is ~350
# generate_sticky_expo_dist(1000, 500.0, 3.0, 1.0)


def generate_links(branching, cur_node, cur_depth):
    # get the geometric series
    last_node_idx = (branching**(cur_depth+1) - 1) // (branching - 1) - 1
    return last_node_idx

# print(generate_links(10, 0, 3))

def generate_dependant_group(json_file, x_group):
    # we create a latency list that is "dependant" on the x_group
    with open(json_file) as f:
        config = json.load(f)
    x_lats = config["latency_groups"][x_group]["lats"]
    y_lats = [[int(lat * 0.5), sticky] for [lat,sticky] in x_lats]
    #plots both
    x = [lat for [lat, _] in x_lats]
    x = sorted(x)
    y = [lat for [lat, _] in y_lats]
    y = sorted(y)

    # plt.plot(x, label=f"Group {x_group}")
    # plt.plot(y, label=f"Group {x_group} dependant")
    # plt.legend()
    # plt.xlabel("x")
    # plt.ylabel("Latency (ms)")
    # plt.title(f"Latency group {x_group} and dependant group")
    # # save the plot
    # plt.savefig(f"latency_group_{x_group}.png")
    # plt.show()
    j = 0
    for i in range(len(y_lats)):
       print(f"[{y_lats[i][0]},{y_lats[i][1]}], ", end="")
       j += 1
       if j % 10 == 0:
        print()
#generate_dependant_group("../configs/d3_b10_dependent.json", "LG2")

def gen_link_pairs():
    i = 11
    j = 111
    x = 121
    cnt = 1
    ls = [[i,j]]
    while x <= 1101:
        print(f"[[{i},{j}], [{i},{x}]], ")
        if cnt == 1:
            j +=20
            ls.append([i,j])
            x = j
            cnt = 0
        x += 10
        cnt += 1
    
    for i, e in enumerate(ls):
        if i % 10 == 0 and i != 0:
            print()
        print(f"[{e[0]},{e[1]}], ", end="")
gen_link_pairs()

def check_mean():
    ls = []
    lats = [e for [e, _] in ls]
    print(f"Mean: {np.mean(lats)}")
# check_mean()


def gen_links():
    # generate links for a tree with branching factor 10 and depth 3
    i = 11
    j = 111
    while j <= 1101:
        for y in range(10):
            print(f"[{i},{j}], ", end="")
            j += 10
        print()
        j += 100
#gen_links()

import re
def extract_latencies(filename):
    latencies = {}
    pattern = re.compile(r"(\d+) stored (\d+) total latency (\d+)")
    
    with open(filename, "r") as f:
        for line in f:
            match = pattern.search(line)
            if match:
                rcvr = int(match.group(1))
                seq = int(match.group(2))
                lat = int(match.group(3))
                if latencies.get(seq) is None:
                    latencies[seq] = [rcvr, lat]
                else:
                    if latencies[seq][1] < lat:
                        latencies[seq] = [rcvr, lat]
                #print(f"seq: {seq}, lat: {lat}, max: {latencies[seq]}")
    latencies = sorted(latencies.values(), key=lambda x: x[0])
    for i in range(len(latencies)):
        print(f"[{latencies[i][0]},{latencies[i][1]}], ", end="")

        if i % 10 == 0:
            print()
  

#extract_latencies("./20.txt")