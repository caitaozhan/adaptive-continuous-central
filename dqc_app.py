'''Distributed quantum computing application
'''

from qutip_qip.algorithms import qft_gate_sequence
import numpy as np


class DQC_APP:
    '''distributed quantum computing application
    
    Attributes:
        monolithic_circuit (): the monolithic quantum circuit
        start_time (float): the time when the application starts (in seconds)
        end_time (float): the time when the application ends (in seconds)
        result (): circuit result
    '''
    def __init__(self, start_time: float, end_time: float):
        self.monolithic_circuit = None
        self.start_time = start_time
        self.end_time = end_time
        self.result = None

    def quantum_fourier_transform(self, num_qubits: int, swapping: bool = False, to_cnot: bool = False):
        '''
        Args:
            num_qubits (int): the number of qubits for the qft
            swapping (int): the swapping in the end
            to_cnot (bool): decompose 1 controlled rotation gate into 2 controlled NOT gate
        '''
        self.monolithic_circuit = qft_gate_sequence(num_qubits, swapping, to_cnot)


class DQC_APP_Queue:
    '''About the queues for the distributed quantum computing application
    '''
    @classmethod
    def generate_random_queue(self, length: int, num_qubits_upper: int, start_time: float, app_period: float) -> list:
        '''generate a random queue of dqc applications
        
        Args:
            length (int): the length of the queue
            num_qubits_upper (int): the upper limit of the number of qubits
            start_time (float): the app time of the first application
            app_period (float): the time period (in seconds) for each application
        '''
        queue = []
        cur_time = start_time
        for _ in range(length):
            dqc_app = DQC_APP(start_time=cur_time, end_time=cur_time+app_period)
            num_qubits = np.random.randint(2, num_qubits_upper)
            dqc_app.quantum_fourier_transform(num_qubits, swapping=False, to_cnot=False)
            queue.append(dqc_app)
            cur_time += app_period
        return queue

