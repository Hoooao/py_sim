import logging

class Message:
    def __init__(self, seq_num):
        self.seq_num = seq_num
        self.timestamp = timer.get_time()
        self.latency = 0
        self.start_time = 0
        self.hops = []

        
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

timer = Timer()

logging.basicConfig(level=logging.INFO,
                    format='%(message)s')
logger = logging.getLogger("sim")

def log_info(message):
    message = f"T: {timer.get_time()} - {message}"
    logger.info(message)
def log_debug(message):
    message = f"T: {timer.get_time()} - {message}"
    logger.debug(message)
def log_error(message):
    message = f"T: {timer.get_time()} - {message}"
    logger.error(message)



