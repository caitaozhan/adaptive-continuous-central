"""The network controller takes in the entanglement requests from the quantum application servers, 
   and talk to the workers about the requests
"""

from enum import Enum, auto
from typing import TYPE_CHECKING
from networkx import Graph, dijkstra_path
from sequence.message import Message
from sequence.kernel.event import Event
from sequence.kernel.process import Process
from sequence.constants import SECOND
from sequence.protocol import Protocol
import sequence.utils.log as log



if TYPE_CHECKING:
    from controller import Controller


class NetControllerMsgType(Enum):
    """Defines possible message types between the network controller (at the centralized controller) and the application (at the node/worker)
    """
    REQUEST = auto()   # request a worker to start EP generation
    RESPOND = auto()   # worker finish the EP generation and respond to the network controller
    FORWARDING_TABLE = auto()  # forwarding table for the worker


class NetControllerMessage(Message):
    """Message used by the network controller (centralized controller) and the application (worker)
    """
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
        elif self.msg_type == NetControllerMsgType.FORWARDING_TABLE:
            self.forwarding_table = kwargs['forwarding_table']
            self.string += f', forwarding_table={self.forwarding_table}'

    def __str__(self):
        return self.string



class NetworkController(Protocol):
    """The network controller at the centralized controller
       This controller is responsible for 
         1) sending entanglement requests to the workers and receiving responses.
         2) computing the forwarding table for each quantum node/worker

        The network controller has access to the global topology via the controller.

        Attributes:
            owner (Controller): the owner controller
            name (str): the name of the network controller
            request_counter (int): the request counter
            entanglement_routing_time (int): the time reserved for entanglement routing, assume the entanglement routing completes before the App's start time
    """
    def __init__(self, owner: "Controller"):
        self.owner = owner
        self.name: str = owner.name + '.network_controller'
        self.request_counter: int = 0
        self.entanglement_routing_time: int = int(0.01 * SECOND)  # Time for entanglement routing

    def init(self):
        """Initialize the network controller with the graph topology
        Args:
            graph (Graph): the graph topology of the network
        """
        # self.graph = graph # TODO confirm the graph is the same as the one in the controller
        # log.logger.info(f'{self.owner.name} initialized with graph: {self.graph}')
        pass

    def send_requests(self, requests: list[tuple]):
        """
        Args:
            requests (list[tuple]): each request in the list is a tuple: (src name, dst name, start time, end time, memory size, fidelity, entanglement number)
        """
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
        """Received classical message from the workers
        """
        log.logger.debug(f'{self.owner.name} receive message from {src}: {msg}')
         # TODO

    def compute_forwarding_table_for_all_nodes(self, graph: Graph) -> dict:
        """Compute the forwarding table for all quantum nodes/workers in the network
        
        Args:
            graph (Graph): the graph topology of the network
        Return:
            all_forwarding_tables (dict): a dictionary of forwarding tables, where the key is the source node name 
                                          and the value is a dictionary of destination node names and their next hops
        """ 
        log.logger.info(f'{self.owner.name} compute forwarding table for all nodes')
        all_forwarding_tables = {}
        for src in graph.nodes:
            all_forwarding_tables[src] = {}
            for dst in graph.nodes:
                if src == dst:
                    continue
                elif dst > src:
                    path = dijkstra_path(graph, src, dst)
                else: # src > dst
                    path = dijkstra_path(graph, dst, src)[::-1]
                next_hop = path[1]
                all_forwarding_tables[src][dst] = next_hop
        return all_forwarding_tables

    def send_forwarding_table_to_one_node(self, node_name: str, forwarding_table: dict):
        """Send the forwarding table to one quantum node/worker in the network
        
        Args:
            node_name (str): the name of the quantum node/worker
            forwarding_table (dict): the forwarding table for this node, where the key is the destination node name
                                     and the value is the next hop
        """
        log.logger.info(f'{self.name} send forwarding table to {node_name}')
        msg = NetControllerMessage(NetControllerMsgType.FORWARDING_TABLE, receiver='application', forwarding_table=forwarding_table)
        process = Process(self.owner, 'send_message', [node_name, msg])
        event = Event(self.owner.timeline.now(), process)
        self.owner.timeline.schedule(event)

    def send_forwarding_table_to_all_nodes(self, all_forwarding_tables: dict):
        """Send the forwarding table to all quantum nodes/workers in the network
        
        Args:
            graph (Graph): the graph topology of the network
            all_forwarding_tables (dict): a dictionary of forwarding tables, where the key is the source node name
                                          and the value is a dictionary of destination node names and their next hops
        """
        log.logger.info(f'{self.owner.name} send forwarding table to all nodes')
        for node_name, forwarding_table in all_forwarding_tables.items():
            self.send_forwarding_table_to_one_node(node_name, forwarding_table)
