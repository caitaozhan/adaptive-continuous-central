"""A class that breaks the quantum link.
Increase the attenuation of the two quantum channels of a link to a very large value -- effectively breaking the link.
"""
import random
from collections import defaultdict
from sequence.kernel.timeline import Timeline
from sequence.kernel.entity import ClassicalEntity
from sequence.components.optical_channel import QuantumChannel, ClassicalChannel
from sequence.kernel.event import Event
from sequence.kernel.process import Process
from sequence.utils import log
from sequence.constants import MILLISECOND


class BreakingLink(ClassicalEntity):
    """A class that breaks the quantum link.
        1) Increase the attenuation of the two quantum channels of a link to a very large value -- effectively breaking the link.
        2) Assume physical layer monitoring of the quantum channels and the latency of detecting the broken link is in the order of 10s ms.
        3) Assume the breaking of quantum channel and classical channel are independent. For the channels between two nodes:
           i) only breaks the quantum channel, ii) only breaks the classical channel, and iii) breaks both quantum and classical channels.
    """

    DETECTION_LATENCY = 10 * MILLISECOND  # latency of detecting the broken link

    def __init__(self, name: str, tl: Timeline, qchannels: list[QuantumChannel], cchannels: list[ClassicalChannel]):
        super().__init__(name, tl)
        self.qchannels = qchannels
        self.cchannels = cchannels
        self.node_to_qchannel = defaultdict(list) # mapping of a link's two node name to list of two quantum channels in of the link (node -- bsm -- node)
        self.node_to_cchannel = defaultdict(list) # mapping of a link's two node name to list of four classical channels in of the link (node -- bsm -- node)

    def init(self):
        """Initialize the link breaker.
        """
        bsm_to_node_qchannel = defaultdict(list) # mapping of bsm node name to the connected node and qchannel
        for qchannel in self.qchannels:
            node = qchannel.sender.name  # node
            bsm = qchannel.receiver      # bsm
            bsm_to_node_qchannel[bsm].append((node, qchannel))
        for bsm, node_qchannel in bsm_to_node_qchannel.items():
            (node1, qchannel1), (node2, qchannel2) = node_qchannel # there are two qchannels for a link 
            node1, node2 = sorted([node1, node2])
            self.node_to_qchannel[(node1, node2)].append(qchannel1)
            self.node_to_qchannel[(node1, node2)].append(qchannel2)

    def break_quantum_link(self, node1: str, node2: str) -> None:
        """Break the quantum link between node1 and node2 by increasing the attenuation of the two quantum channels

        Args:
            node1 (str): name of one end node of the link
            node2 (str): name of the other end node of the link
        """
        node1, node2 = sorted([node1, node2])
        if (node1, node2) in self.node_to_qchannel:
            for qc in self.node_to_qchannel[(node1, node2)]:
                qc.attenuation = 1e3  # effectively break the link
                qc.init()             # re-initialize the quantum channel to update the attenuation
                log.logger.info(f'{self.name} breaks the quantum link between {node1} and {node2} by increasing the attenuation to {qc.attenuation} dB/m')
                # the two nodes will detect the broken link after the detection latency
                noticed_time = self.timeline.now() + self.DETECTION_LATENCY
            for node in [node1, node2]:
                # the two nodes will inform the controller of the broken link
                process = Process(node, "noticed_broken_quantum_link", [node1, node2])
                event = Event(noticed_time, process)
                self.timeline.schedule(event)
        else:
            log.logger.warning(f'No quantum link between {node1} and {node2}')

    def notify_broken_link(self, node1: str, node2: str) -> None:
        log.logger.info(f'{self.name} notified of broken link between {node1} and {node2}')

    def load(self, queue: list[tuple]) -> None:
        """Load a queue of breaking events.

        Args:
            queue (list[tuple]): each tuple in the list is (time, node1 name, node2 name)
        """
        for time, node1, node2 in queue:
            process = Process(self, "break_quantum_link", [node1, node2])
            event = Event(time, process)
            self.timeline.schedule(event)

    def generate_random_breaking_queue(self, break_prob: float, interval: int, stop_time: int) -> list:
        """Generate a random queue of breaking events.

        Args:
            break_prob (float): probability of breaking a link in each interval
            interval (int): time interval for checking the breaking of links
            stop_time (int): time to stop the scheduling
        Returns:
            queue (list[tuple]): each tuple in the list is (time, node1 name, node2 name)
        """
        node_pairs = list(self.node_to_qchannel.keys())
        time = 0
        queue = []
        while time < stop_time:
            for node1, node2 in node_pairs:
                if random.random() < break_prob:
                    queue.append((time, node1, node2))
            time += interval
        return queue
