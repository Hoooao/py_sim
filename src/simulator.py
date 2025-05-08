from common import *
import json
from time import time
import heapq
from tree_components import *
import itertools
from copy import deepcopy

class Simulator:
    def __init__(self, log_file=f"sim_log_{int(time())}.txt"):
        self.event_queue = []
        self.log_file = log_file
        # make sure if two events are scheduled at the same time, 
        # they are processed in the order they were scheduled
        self._counter = itertools.count() 
        log_info("=== Simulation init ===\n")

    def config_setup(self, config_file):
        with open(config_file) as f:
            config = json.load(f)
        self.links = config["links"]
        self.latency_groups = {}
        for lat_id, latencies in config["latency_groups"].items():
            log_debug(f"Latency group {lat_id} has latencies {latencies}")
            lg = LatencyGroup(lat_id, latencies)
            self.latency_groups[lat_id] = lg

        self.branching = config["branching"]
        self.depth = config["depth"]
        self.link_to_group_id = self.get_link_to_group_id()
        self.nodes = {}
        self.frequency = config["frequency"]
        self.end_time = config["end_time"]
        if config["spray"]:
            self.spray = True
            self.build_tree_spray()
        else:
            self.spray = False
            self.build_tree_no_spray(0,0)

    def get_link_to_group_id(self):
        link_to_group = {}
        for group_id, links in self.links.items():
            log_debug(f"Group {group_id} has links {links}")
            for [src,dst] in links:
                link_to_group[(src,dst)] = group_id
                
        return link_to_group

    def build_tree_no_spray(self, cur_depth, node_idx=0):
        print(f"Building tree at depth {cur_depth} for node {node_idx}")
        if cur_depth == self.depth:
            self.nodes[node_idx] = Node(node_idx)
            return self.nodes[node_idx]
        branching = self.branching
        root = Node(node_idx)
        self.nodes[node_idx] = root
        for i in range(branching):
            child = self.build_tree_no_spray(cur_depth + 1, node_idx * branching + i + 1)
            # check if the config file specifies a link group for this connection
            # if not, use the default group ID LG0
            group_id = "LG0"
            if self.link_to_group_id.get((node_idx, child.id)):
                group_id = self.link_to_group_id[(node_idx, child.id)]
            root.connect(child, self.latency_groups[group_id])
        return root

    def build_tree_spray(self):
        nodes = [[Node(0)]]
        idx = 1
        for i in range(1,self.depth+1):
            cur_nodes = []
            for j in range(self.branching**i):
                n = Node(idx)   
                n.cur_childrent_set_idx = j
                self.nodes[idx] = n
                cur_nodes.append(n)
                idx += 1
            nodes.append(cur_nodes)
        
        # connect all nodes in level i to all nodes in level i+1
        for i in range(self.depth):
            for j in range(len(nodes[i])):
                for k in range(len(nodes[i+1])):
                    group_id = "LG0"
                    if self.link_to_group_id.get((nodes[i][j].id, nodes[i+1][k].id)):
                        group_id = self.link_to_group_id[(nodes[i][j].id, nodes[i+1][k].id)]
                    nodes[i][j].connect(nodes[i+1][k], self.latency_groups[group_id])

        # flatten nodes to self.nodes
        for i in range(len(nodes)):
            for j in range(len(nodes[i])):
                self.nodes[nodes[i][j].id] = nodes[i][j]


    def schedule(self, delay, callback, *args):
        count = next(self._counter)
        heapq.heappush(self.event_queue, (timer.get_time() + delay, count, callback, args))

    def generate_request(self, seq_num):
        if timer.get_time() > self.end_time:
            return
        msg = Message(seq_num)
        msg.hops = [0]
        msg.start_time = timer.get_time()
        self.send_msg_to_all_children(self.nodes[0], msg)
        self.schedule(self.frequency, self.generate_request, seq_num + 1)


    def send_msg_to_all_children(self, node: Node, msg: Message): 
        msg_latency = msg.latency
        for child in node.children:
            latency = node.links[child.id].get_latency()
            log_debug(f"Node {node.id} -> {child.id} link lat: {latency}")
            msg.latency = latency + msg_latency
            self.schedule(latency, self.rcv_msg, node.id, child.id, deepcopy(msg))

    def send_msg_to_spray_children(self, node, msg):
        start = node.cur_childrent_set_idx * self.branching
        end = start + self.branching
        msg_latency = msg.latency
        for child in node.children[start:end]:
            latency = node.links[child.id].get_latency()
            log_debug(f"Node {node.id} -> {child.id} lat: {latency}")
            msg.latency = latency + msg_latency
            self.schedule(latency, self.rcv_msg, node.id, child.id, deepcopy(msg))
        node.cur_childrent_set_idx += 1
        node.cur_childrent_set_idx %= len(node.children) // self.branching


    def rcv_msg(self, src, dst, msg):    
        log_debug(f"Node {dst} rcvd from {src} msg {msg.seq_num} latency {msg.latency} ")
        node = self.nodes[dst]
        msg.hops.append(dst)
        if node.children == []:
            node.msgs.append(msg)
            log_info(f"Node {node.id} stored {msg.seq_num} total latency {msg.latency}")
            #log_info(f"Hops: {msg.hops}")
            assert msg.latency == timer.current_time - msg.start_time, f"Node {node.id} has latency {msg.latency} but current time is {timer.get_time()} and start time is {msg.start_time}"
            return
        if self.spray:
            self.send_msg_to_spray_children(node, msg)
        else:
            self.send_msg_to_all_children(node, msg)

    def show_tree(self):
        for node in self.nodes.values():
            log_debug(f"Node {node.id} has children {[child.id for child in node.children]} and messages {node.msgs}")
    
    def run(self):
        log_info("\n\n=== Simulation start ===\n")
        self.generate_request(0)
        while self.event_queue or timer.get_time() < self.end_time:
            time,_, cb, args = heapq.heappop(self.event_queue)
            timer.set_to(time)
            cb(*args)

