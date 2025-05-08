import numpy as np

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

print(generate_links(10, 0, 2))