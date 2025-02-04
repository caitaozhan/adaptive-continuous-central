'''The centralized version of AC Protocol
'''

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from node import QuantumRouterAdaptiveWorker
    from controller import Controller
    

from sequence.kernel.timeline import Timeline
from reservation import ResourceReservationProtocolAdaptive 


class AdaptiveContinuousController:
    """The central controller of the adaptive continuous entanglement generation.
    There is only controller for the whole quantum network. Located at one arbitrary node.
    """
    def __init__(self, owner: "Controller", name: str, tl: Timeline):
        pass


class AdaptiveContinuousWorker:
    """The worker of the adaptive continuous entanglement generation.
    If not the controller, the rest of the nodes are all workers.
    """
    def __init__(self, owner: "QuantumRouterAdaptiveWorker", name: str, tl: Timeline, adaptive_max_memory: int, resource_reservation: ResourceReservationProtocolAdaptive):
        pass

