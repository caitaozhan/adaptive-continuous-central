'''The network controller takes in the entanglement requests from the quantum application servers, 
   and talk to the workers about the requests
'''

from enum import Enum, auto
from typing import TYPE_CHECKING
from sequence.message import Message
from sequence.kernel.event import Event
from sequence.kernel.process import Process
from sequence.constants import SECOND
import sequence.utils.log as log


if TYPE_CHECKING:
    from controller import Controller


class NetControllerMsgType(Enum):
    '''Defines possible message types between the network controller (at the centralized controller) and the application (at the node/worker)
    '''
    REQUEST = auto()   # request a worker to start EP generation
    RESPOND = auto()   # worker finish the EP generation and respond to the network controller


class NetControllerMessage(Message):
    '''Message used by the network controller (centralized controller) and the application (worker)
    '''
    def __init__(self, msg_type: NetControllerMsgType, receiver: str, **kwargs):
        super().__init__(msg_type, receiver=receiver)
        self.string = f'type={msg_type.name}, receiver={receiver}'

        if self.msg_type == NetControllerMsgType.REQUEST:
            self.request = kwargs['request']
            self.request_counter = kwargs['request_counter']
            self.string += f', request={self.request}, request_counter={self.request_counter}'
        elif self.msg_type == NetControllerMsgType.RESPOND:
            self.respond = kwargs['respond']
            self.string += f', respond={self.respond}'
    
    def __str__(self):
        return self.string
    


class NetworkController:
    '''The network controller at the centralized controller
    '''
    def __init__(self, owner: "Controller"):
        self.owner = owner
        self.request_counter = 0
        self.entanglement_routing_time = 0.01 * SECOND  # Time for entanglement routing

    
    def send_requests(self, requests: list[tuple]):
        '''
        Args:
            requests (list[tuple]): each request in the list is a tuple: (src name, dst name, start time, end time, memory size, fidelity, entanglement number)
        '''
        # use the sequence events to send the message
        for request in requests:
            worker = request[0]
            time = request[2] - self.entanglement_routing_time
            msg = NetControllerMessage(NetControllerMsgType.REQUEST, receiver='application', request=request, request_counter=self.request_counter)
            process = Process(self.owner, 'send_message', [worker, msg])
            event = Event(time, process)
            self.owner.timeline.schedule(event)
            self.request_counter += 1

    def received_message(self, src: str, msg: NetControllerMessage):
        '''Received classical message from the workers
        '''
        log.logger.debug(f'{self.owner.name} receive message from {src}: {msg}')
         # TODO
