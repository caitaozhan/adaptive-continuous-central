"""
This module defines the centralized controller.
"""

from collections import defaultdict
from networkx.classes.graph import Graph
import numpy as np
from sequence.topology.node import ClassicalNode
from sequence.kernel.timeline import Timeline
from adaptive_continuous_central import AdaptiveContinuousController


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
    """
    def __init__(self, name: str, timeline: Timeline, seed: int):
        super().__init__(name, timeline)
        self.owner = self
        self.generator = np.random.default_rng(seed)
        self.adaptive_continuous_controller = AdaptiveContinuousController(self, f'{name}.acp', timeline)
        self.graph: Graph = None
        self.prob_tables: defaultdict[str, dict] = None

    def init(self) -> None:
        """override init method
        """
        pass

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

