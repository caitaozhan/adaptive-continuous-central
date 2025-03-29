'''Distributed quantum computing server
'''
from controller import Controller


class DQC_APP_Server:
    '''receive a queue of DQC applications, then turn them into quantum network requests

    Args:
        owner (Controller): the owner of the DQC_APP_Server is the centralized controller
    '''
    def __init__(self, owner: Controller):
        self.owner: Controller = owner
        self.app_queue = []
        self.request_queue = []

    def load(self, app_queue: list):
        '''load the DQC application queue
        '''
        self.app_queue.extend(app_queue)

    def generate_network_request(self):
        '''Given the DQC application queue, generate the network requests. 
           Also, create the events that initiate the requests
        '''
        # 1. Horizontal partition the circuit, select a subset of the network nodes
        # 2. Create the network requests
        pass