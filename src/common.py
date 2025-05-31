import logging
import heapq

CONGESTION_DELAY_TIME = 3 # the time that an entity reside within a switch
TESTING = False # if true, run the test cases
TESTING_SPRAY = False # if true, run the test cases with spray

def log_info(message, no_time=False):
    if not no_time:
        message = f"T: {timer.get_time()} - {message}"
    logger.info(message)
def log_debug(message, no_time=False):
    if not no_time:
        message = f"T: {timer.get_time()} - {message}"
    logger.debug(message)
def log_error(message, no_time=False):
    if not no_time: 
        message = f"T: {timer.get_time()} - {message}"
    logger.error(message)


class Message:
    def __init__(self, seq_num):
        self.seq_num = seq_num
        self.timestamp = timer.get_time()
        self.latency = 0
        self.start_time = 0
        self.hops = []
        
    def __lt__(self, other):
        return self.latency < other.latency

class ActiveEntity:
    def __init__(self, length):
        self.start_time = timer.get_time()
        self.end_time = self.start_time + length

    def __lt__(self, other):
        return self.end_time < other.end_time
    
class ActiveLinkInSwitchState(ActiveEntity):
    def __init__(self, link, length):
        super().__init__(length)
        self.enabled = False
        self.link = link
    
class ActivePktInSwitchState(ActiveEntity):
    def __init__(self, length):
        super().__init__(length)
        
    
class Switch:
    def __init__(self, switch_id, congestion_delay, base_latency, link_pairs, per_link = True):
        self.id = switch_id
        link_tuples = []
        for pair in link_pairs:
            link_tuples.append((pair[0], pair[1]))
        self.raw_links = set(link_tuples)
        self.links_to_state = {}
        self.queue:list[ActiveEntity] = []
        self.active_count = 0 # number of active links or pkts
        self.base_latency = base_latency # a distribution of latencies
        self.base_latency_ptr = [0,0]
        self.congestion_delay = congestion_delay 

        self.per_link = per_link # if false, latency is incurred per pkt.

    def register_link(self, link):
        self.links_to_state[link] = ActiveLinkInSwitchState(link, 0)
        link.switch = self

    def get_latency(self):
        [lat, stickiness] = self.base_latency[self.base_latency_ptr[0]]
        self.base_latency_ptr[1] += 1
        if stickiness == self.base_latency_ptr[1]:
            # if the stickyness is the same, move to the next latency
            self.base_latency_ptr[0] = (self.base_latency_ptr[0] + 1) % len(self.base_latency)
            self.base_latency_ptr[1] = 0
        lat = lat + self.congestion_delay * max(self.active_count-1,0) # exponential or linear?
        log_debug(f"Switch {self.id} latency {lat} with {self.active_count} active entities")
        return lat     

    def access_per_link(self, link, length):
        log_debug(f"Accessing switch {self.id} with {link} per link")
        assert (link.src.id, link.dst.id) in self.raw_links, f"Link {link} not registered in switch {self.id}"
        # pop any expired links
        while self.queue and self.queue[0].end_time <= timer.get_time():
            state = heapq.heappop(self.queue)
            state.enabled = False
            self.active_count -= 1
        # update the link state when the link accesses the switch
        self.links_to_state[link].start_time = timer.get_time()
        self.links_to_state[link].end_time = self.links_to_state[link].start_time + length
        if not self.links_to_state[link].enabled:
            self.links_to_state[link].enabled = True
            self.active_count += 1
        return self.get_latency()
    
    def access_per_pkt(self, link, length):
        log_debug(f"Accessing switch {self.id} with {link} per pkt")
        # pop any expired pkts
        while self.queue and self.queue[0].end_time <= timer.get_time():
            state = heapq.heappop(self.queue)
            self.active_count -= 1
        # update the link state when the link accesses the switch
        state = ActivePktInSwitchState(length)
        heapq.heappush(self.queue, state)
        self.active_count += 1
        return self.get_latency()
    
    def access(self, link, length):
        if self.per_link:
            return self.access_per_link(link, length)
        else:
            return self.access_per_pkt(link, length)
        
            
        
class Timer:
    def __init__(self):
        self.start_time = 0
        self.current_time = 0

    def set_to_zero(self):
        self.start_time = 0
    
    def set_to(self, time):
        self.current_time = time

    def get_time(self):
        return self.current_time
    def reset(self):
        self.current_time = 0

timer = Timer()

logging.basicConfig(level=logging.DEBUG,
                    format='%(message)s')
logger = logging.getLogger("sim")





