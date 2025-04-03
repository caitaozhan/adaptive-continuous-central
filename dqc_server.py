'''Distributed quantum computing server
'''

from qutip_qip.circuit import QubitCircuit
from typing import TYPE_CHECKING
import numpy as np
from collections import defaultdict, Counter

from networkx.classes.coreviews import AdjacencyView
from sequence.constants import EPSILON
import sequence.utils.log as log

from dqc_app import DQC_APP

if TYPE_CHECKING:
    from controller import Controller



class DQC_APP_Server:
    '''receive a queue of DQC applications, then turn them into quantum network requests

    Args:
        owner (Controller): the owner of the DQC_APP_Server is the centralized controller
        app_queue (list): a list of dqc applications
        num_qubit_per_worker (int): number of qubits per worker
        request_queue (list): a queue of requests
    '''
    def __init__(self, owner: "Controller"):
        self.owner = owner
        self.app_queue = []
        self.num_qubit_per_worker = 0
        self.request_queue = []

    def load(self, app_queue: list):
        '''load the DQC application queue
        '''
        self.app_queue.extend(app_queue)

    def generate_network_request(self):
        '''Given the DQC application queue, generate the network requests. 
           Also, create the events that initiate the requests
        '''
        for app in self.app_queue:
            # 1. Horizontal partition the circuit
            partitions = self.partition_simple(app.monolithic_circuit)
            # 2. select a subset of the network nodes, i.e. workers
            num_workers = len(partitions)  # one partition goes to one worker
            workers = self.select_workers_dijkstra(num_workers)
            # 3. Create the network requests given the partition and workers
            request_queue = self.generate_requests(app, partitions, workers)
            # 4. pass the request queue to the network controller
            self.owner.network_controller.send_requests(request_queue)

    def partition_simple(self, circuit: QubitCircuit) -> defaultdict[list]:
        '''a simple partition given the number of qubit per worker

        Args:
            circuit (QubitCircuit): the monolithic quantum circuit
        Return:
            paritions (defaultdict): the partitions
        '''
        partitions = defaultdict(list)
        partition = -1
        num_qubits = circuit.N
        for i in range(num_qubits):
            if i % self.num_qubit_per_worker == 0:
                partition += 1
            partitions[partition].append(i)
        return partitions

    def select_workers_dijkstra(self, num_workers: int) -> list:
        '''select a group of workers that has a smallest total distance

        Args:
            num_workers (int): number of workers/nodes in the network
        Return:
            best_workers (list): a list of workers/nodes in the network
        '''
        g = self.owner.graph.adj  # may use partial g if some nodes are not available
        best_total_distance = np.inf
        best_workers = None
        for node in self.owner.graph.nodes:
            workers, dist = self.dijkstra(g, node, num_workers)
            total_dist = 0
            for worker in workers:
                total_dist += dist[worker]
            if total_dist < best_total_distance:
                best_workers = workers
                best_total_distance = total_dist
        return best_workers
    
    def dijkstra(self, g: AdjacencyView, start: str, num_workers: int) -> tuple:
        '''do a dijkstra on a single node

        Args:
            g (AdjacencyView): the graph
            start (str): the starting node of dijkstra
        Return:
            visited (list): a list of workers
            dist (dict): distance dictionary
        '''
        assert num_workers <= len(g), f'num_workers={num_workers}, len(g)={len(g)}'
        visited = []
        non_visited = []
        dist = {}
        for node in g:
            non_visited.append(node)
            dist[node] = np.inf
        dist[start] = 0
        while len(visited) < num_workers:
            min_dist = np.inf
            closest_node = None     # each round, one new node is added to the visited
            for u in non_visited:
                if dist[u] < min_dist:
                    closest_node = u
                    min_dist = dist[u]
            u = closest_node
            for v in g[u]:
                u_v_weight = g[u][v]['weight']
                if dist[u] + u_v_weight < dist[v]:
                    dist[v] = dist[u] + u_v_weight
            visited.append(u)
            non_visited.remove(u)
        return visited, dist

    def generate_requests(self, app: DQC_APP, partitions: defaultdict[list], workers: list[str]) -> list:
        '''Generate the network request, which are sent to the network controller
           the mapping of partitions to workers is a "direct index mapping"

        Args:
            circuit (QubitCircuit): the monolithic circuit
            partitions (defaultdict[list]): partition dictionary
            workers (list[str]): the workers
        Return:
            (list): a list of requests. Each request is represented by a tuple (src name, dst name, start time, end time, memory size, fidelity, entanglement number)
        '''
        # 1. map the qubit to the workers
        qubit2worker = {}
        for partition, qubits in partitions.items():
            for qubit in qubits:
                qubit2worker[qubit] = workers[partition]  # both parition and workers are 0-indexed
        # 2. go over the gates
        circuit = app.monolithic_circuit
        counter = Counter()
        for gate in circuit.gates:
            if gate.controls is not None:
                if len(gate.controls) > 1 or len(gate.targets) > 1:
                    log.logger.info(f'Not 2-qubit gate: {gate}')
                q1 = gate.targets[0]
                q2 = gate.controls[0]
                worker1 = qubit2worker[q1]
                worker2 = qubit2worker[q2]
                if worker1 != worker2:
                    counter[(worker1, worker2)] += 1
        # 3. the requests
        request_queue = []
        memory_size = 1
        fidelity = 0.7
        for (src, dst), count in counter.items():
            request = (src, dst, app.start_time, app.end_time, memory_size, fidelity, count)
            request_queue.append(request)
        return request_queue
