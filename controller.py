"""
This module defines the centralized controller.
"""

from typing import List
from networkx.classes.graph import Graph
import numpy as np
from sequence.topology.node import ClassicalNode
from sequence.kernel.timeline import Timeline
from adaptive_continuous_central import AdaptiveContinuousController
from dqc_server import DQC_APP_Server


class Controller(ClassicalNode):
    """The centralized controller

    Need to get the global topology and traffic pattern

    Attributes:
        name (str): the name
        timeline (Timeline): the simulation timeline
        seed (int): the seed
        generator (rng): the random number generator from np
        adaptive_continuous_controller (AdaptiveContinuousController): the centralized controller
        graph (Graph): the graph topology of the network
        traffic (list): the traffic pattern, consist a list of (matrix, start_time, end_time)
    """
    def __init__(self, name: str, timeline: Timeline, seed: int):
        super().__init__(name, timeline)
        self.owner = self
        self.generator = np.random.default_rng(seed)
        self.graph: Graph = None
        self.traffic = []  # a list of tuples of (matrix, start_time, end_time)
        self.adaptive_continuous = AdaptiveContinuousController(self, f'{name}.acp')
        self.dqc_server: DQC_APP_Server = DQC_APP_Server(self)
        self.network_controller = None

    def init(self) -> None:
        """override init method
        """
        self.adaptive_continuous.init(self.graph, self.traffic)
        self.adaptive_continuous.init_prob_tables()
        self.adaptive_continuous.send_probability_table()

    def set_seed(self, seed: int) -> None:
        """Set the seed, also set the generator
        
        Args:
            seed (int): the random seed
        """
        self.seed = seed
        self.generator = np.random.default_rng(seed)
    
    def get_seed(self) -> int:
        """Get the seed"""
        return self.seed

    def add_traffic(self, matrix: List[List], start_time: float, end_time: float):
        """Inform the controller the traffic pattern

        Note: currently assuming static routing
        
        Attributes:
            matrix (List[List]): the traffic matrix
            start_time (float): the start time of this traffic matrix
            end_time (float): the end time of this traffic matrix
        """
        self.traffic.append([matrix, start_time, end_time])
