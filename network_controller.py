'''The network controller takes in the entanglement requests from the quantum application servers, and talk to the workers about the requests
'''

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from controller import Controller

class NetworkController:
    '''The network controller at the centralized controller
    '''
    def __init__(self, owner: "Controller"):
        self.owner = owner
    
    def send_requests(self, request: tuple):
        # use the sequence events
        print('caitao')