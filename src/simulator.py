import common
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
        self.links = {}
        self.receiver_number = 0
        # seq:count of received
        self.log = {}
        # make sure if two events are scheduled at the same time, 
        # they are processed in the order they were scheduled
        self._counter = itertools.count() 
        log_info("=== Simulation init ===\n", True)
        timer.reset()

    def setup_switches(self, config):
        if not config.get("switch_settings"):
            return
        switch_settings = config["switch_settings"]
        if switch_settings["enable_switch"]:
            # get the links in each switch
            switches_links = switch_settings["switches"]
            per_link = switch_settings["switch_latency_incur_by_per_link"]
            self.switch_latency_groups = {}
            for switch_id, switch_lats in switch_settings["switch_latency_groups"].items():
                log_debug(f"Switch {switch_id} has latencies {switch_lats}")
                switch = Switch(switch_id, 2, switch_lats, switches_links[switch_id], per_link)
                log_debug(f"Switch {switch_id} has links {switches_links[switch_id]}")
                self.switches[switch_id] = switch

    def setup_dependent_links(self, config):
        if not config.get("dependent_groups") or not config["dependent_groups_enabled"]:
            return
        dep_groups = config["dependent_groups"]
        for group_id, group in dep_groups.items():
            depend_on = group["dependent_group"]
            lats = group["lats"]
            log_debug(f"Group {group_id} depends on {depend_on}")
            log_debug(f"Group {group_id} has latencies {lats}")
            dep_group = LatencyGroup(group_id, lats)
            for [[depee_src,depee_dst], [dep_src,dep_dst]] in group["link_pairs"]:
                if self.links.get((dep_src, dep_dst)) is None:
                    log_debug(f"Link {dep_src} -> {dep_dst} not found")
                    continue
                log_debug(f"Link {dep_src} -> {dep_dst} depends on {depee_src} -> {depee_dst}")
                self.links[(dep_src, dep_dst)].dependent_latency_links.append(self.links[(depee_src, depee_dst)])
                self.links[(dep_src, dep_dst)].dependent_latency_groups.append(dep_group)
                

    def config_setup(self, config_file):
        with open(config_file) as f:
            config = json.load(f)
        self.nodes = {}
        self.latency_groups = {}
        self.lat_group_to_links = {}
        self.switches: dict[str, Switch] = {}
        self.branching = config["branching"]
        self.depth = config["depth"]
        self.frequency = config["frequency"]
        self.end_time = config["end_time"]
        self.receiver_number = self.branching ** self.depth
        for lat_id, info in config["latency_groups"].items():
            lat = info["lats"]
            self.lat_group_to_links[lat_id] = info["links"]
            log_debug(f"Latency group {lat_id} has latencies {lat}")
            lg = LatencyGroup(lat_id, lat)
            self.latency_groups[lat_id] = lg

        self.setup_switches(config)
        
        self.link_to_group_id = self.get_link_to_group_id()
        
        if (not common.TESTING and config["spray"]) or (common.TESTING and common.TESTING_SPRAY):
            self.spray = True
            self.build_tree_spray()
        else:
            self.spray = False
            self.build_tree_no_spray(0,0)

        self.setup_dependent_links(config)

    def get_link_to_group_id(self):
        link_to_group = {}
        for group_id, links in self.lat_group_to_links.items():
            log_debug(f"Group {group_id} has links {links}")
            for [src,dst] in links:
                link_to_group[(src,dst)] = group_id
                
        return link_to_group

    def register_link_to_switch(self, link:Link):
        for switch_id, switch in self.switches.items():
            if (link.src.id, link.dst.id) in switch.raw_links:
                switch.register_link(link)
                log_info(f"{link} registered to switch {switch_id}", True)
                
    def build_tree_no_spray(self, cur_depth, node_idx=0):
        log_info(f"Building tree at depth {cur_depth} for node {node_idx}")
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
            link = root.connect(child, self.latency_groups[group_id], simulator = self)
            self.register_link_to_switch(link)
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
                    link = nodes[i][j].connect(nodes[i+1][k], self.latency_groups[group_id], simulator = self)
                    self.register_link_to_switch(link)

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
            log_debug(f"Node {node.id} stored {msg.seq_num} total latency {msg.latency}")
            if self.log.get(msg.seq_num) is None:
                self.log[msg.seq_num] = 1
            else:
                self.log[msg.seq_num] += 1
            if self.log[msg.seq_num] == self.receiver_number:
                log_info(f"Node {node.id} stored {msg.seq_num} total max latency {msg.latency}")

            #log_info(f"Hops: {msg.hops}")
            assert msg.latency == timer.current_time - msg.start_time, f"Node {node.id} has latency {msg.latency} but current time is {timer.get_time()} and start time is {msg.start_time}"
            return
        if self.spray:
            self.send_msg_to_spray_children(node, msg)
        else:
            self.send_msg_to_all_children(node, msg)

    def show_tree(self):
        for node in self.nodes.values():
            log_debug(f"Node {node.id} has children {[child.id for child in node.children]}")
    
    def run(self):
        log_info("\n\n=== Simulation start ===\n")
        self.generate_request(0)
        while self.event_queue or timer.get_time() < self.end_time:
            time,_, cb, args = heapq.heappop(self.event_queue)
            timer.set_to(time)
            cb(*args)

    def aggergate_results(self):
        # get the results from all nodes
        results = {}
        for node in self.nodes.values():
            res = []
            for msg in node.msgs:
                res.append([msg.seq_num, msg.latency, msg.hops])
            results[node.id] = res
        return results
