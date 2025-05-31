from common import *
from typing import List, Dict, Tuple


class LatencyGroup:
    def __init__(self, group_id: int, latencies:int):
        self.id = group_id
        # latencies are a list of tuples (latency, rep_factor)
        self.latencies:List[List] = latencies
        # key is link (src, dst) and value is a tuple of (latency_ptr, cur_rep_factor)
        self.member_to_ptr:Dict[int, Tuple] = {}

    def add_member(self, src_dst: Tuple, start_idx: int):
        assert src_dst not in self.member_to_ptr, f"Latency group {self.id} already has a latency for {src_dst}"
        self.member_to_ptr[src_dst] = (start_idx % len(self.latencies), 0)

    def get_latency(self, src_dst):
        [ptr, cur_rep] = self.member_to_ptr.get(src_dst)
        assert ptr is not None, f"Latency group {self.id} does not have a latency for {src_dst}"
        [lat, rep] = self.latencies[ptr]
        if rep-1 == cur_rep:
            # if the rep factor is the same, move to the next latency
            ptr = (ptr + 1) % len(self.latencies)
            self.member_to_ptr[src_dst] = (ptr, 0)
        else:
            # if the rep factor is different, move to the next rep factor
            cur_rep += 1
            self.member_to_ptr[src_dst] = (ptr, cur_rep)
        return lat
    def get_latency_with_ptr(self, ptr_rep):
        [ptr, _] = ptr_rep
        [lat, _] = self.latencies[ptr]
        return lat

    def get_ptr(self, src_dst):
        return self.member_to_ptr.get(src_dst)

class Link:
    def __init__(self, src: 'Node', dst: 'Node', latency_group: LatencyGroup):
        self.src = src
        self.dst = dst
        self.switch:Switch = None
        self.latency_group:LatencyGroup = latency_group
        self.dependent_latency_links:List[Link] = []
        self.dependent_latency_groups:List[LatencyGroup] = []
        # starting latency ptr as simply the sum of the ids
        self.latency_group.add_member((src.id, dst.id), src.id + dst.id)
    def __str__(self):
        return f"Link {self.src.id} -> {self.dst.id}"
    def get_latency(self):
        lat = 0
        if self.switch:
            lat += self.switch.access(self, CONGESTION_DELAY_TIME)
        for i, link in enumerate(self.dependent_latency_links):
            ptr = link.latency_group.get_ptr((link.src.id, link.dst.id))
            lat += self.dependent_latency_groups[i].get_latency_with_ptr(ptr)
        lat += self.latency_group.get_latency((self.src.id, self.dst.id))
        return lat

class Node:
    def __init__(self, node_id):
        self.id = node_id
        self.children:List['Node'] = []
        self.links:Dict[int, Link] = {}
        self.msgs:List[MemoryError] = []
        # one # of branching children per set
        self.cur_childrent_set_idx = 0

    def connect(self, child: 'Node', latency_group: LatencyGroup, simulator: 'Simulator'):
        link = Link(self, child, latency_group)
        self.links[child.id] = link
        log_debug(f"Node {self.id} connected to {child.id} with latency group {latency_group.id}")
        # uni-direction for now
        self.children.append(child)
        simulator.links[(link.src.id, link.dst.id)] = link
        return link




