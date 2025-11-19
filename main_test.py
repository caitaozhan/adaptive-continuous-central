'''
Implement the paper titled "Adaptive, Continuous Entanglement Generation for Quantum Networks" 
in SeQUeNCe and conduct experiments with a large number of nodes.
'''

from collections import defaultdict
import numpy as np
from sequence.topology.router_net_topo import RouterNetTopo
from sequence.constants import MILLISECOND, SECOND
import sequence.utils.log as log
from request_app import RequestAppThroughput, RequestAppTimeToServe
from router_net_topo_adaptive import RouterNetTopoAdaptive
from traffic import TrafficMatrix
from dqc_app import DQC_APP_Queue
from controller import Controller
from breaking_link import BreakingLink





# the request type-2 (time-to-serve) app, testing on a two node linear network, for time-to-serve, distributed quantum computing
def line_2_node_dqc():

    REQUEST_PERIOD = 0.1 # seconds, request incoming rate, assuming reqeust arrives one by one
    DELTA = 0.02         # seconds, time for EP pre-generation

    purify = False
    strategy = 'freshest'
    # log_filename = f'log/queue_tts/line2,ma=1,up=False,{strategy},pf={purify}'
    log_filename = 'log/tmp/line2,qmem=2,central'
    
    network_config = 'config/line_2.json'

    network_topo = RouterNetTopoAdaptive(network_config)
    
    tl = network_topo.get_timeline()

    log.set_logger(__name__, tl, log_filename)
    # log.set_logger_level('DEBUG')
    log.set_logger_level('INFO')
    # modules = ['adaptive_continuous_c', 'request_app', 'rule_manager', 'timeline', 'resource_manager', 'generation', 'main_test', 'memory', 'purification']
    modules = ['controller', 'network_controller', 'node', 'timeline',  'main_test',]
    # modules = ['main_test']
    for module in modules:
        log.track_module(module)

    name_to_apps = {}
    for router in network_topo.get_nodes_by_type(RouterNetTopo.QUANTUM_ROUTER):
        app = RequestAppTimeToServe(router)
        name_to_apps[router.name] = app
        # if router.name not in ['router_4', 'router_5']:
        #     router.active = False
        router.adaptive_continuous.has_empty_neighbor = True
        router.adaptive_continuous.update_prob = True
        router.adaptive_continuous.strategy = strategy
        router.adaptive_continuous.update_period(REQUEST_PERIOD * SECOND)
        router.resource_manager.purify = purify

    controller: Controller = None
    for con in network_topo.get_nodes_by_type(RouterNetTopo.CONTROLLER):
        controller = con
        break

    controller.dqc_server.num_qubit_per_worker = 5
    queue_length = 10
    num_qubits_lower = 6
    num_qubits_upper = 8
    start_time = 0.1
    app_period = REQUEST_PERIOD
    dqc_app_queue = DQC_APP_Queue.generate_random_queue(queue_length, num_qubits_lower, num_qubits_upper, start_time, app_period)
    controller.dqc_server.load(dqc_app_queue)
    controller.dqc_server.generate_network_request()

    # num_nodes = len(name_to_apps)
    # traffic_matrix = TrafficMatrix(num_nodes)
    # traffic_matrix.line_2()
    # request_queue = []
    # # TODO put the traffic matrix in the controller
    # request_queue = traffic_matrix.get_request_queue_tts(request_queue=request_queue, request_period=REQUEST_PERIOD, delta=DELTA, \
    #                                                      start_time=0, end_time=1, memo_size=1, fidelity=0.6, entanglement_number=1, controller=controller)
    # for request in request_queue:
    #     id, src_name, dst_name, start_time, end_time, memo_size, fidelity, entanglement_number = request
    #     app = name_to_apps[src_name]
    #     app.start(dst_name, start_time, end_time, memo_size, fidelity, entanglement_number, id)

    tl.init()
    tl.run()

    time_to_serve_dict = defaultdict(float)
    fidelity_dict = defaultdict(list)
    for _, app in name_to_apps.items():
        time_to_serve_dict |= app.time_to_serve
        fidelity_dict |= app.entanglement_fidelities

    for reservation, time_to_serve in sorted(time_to_serve_dict.items()):
        fidelity = fidelity_dict[reservation][0]
        log.logger.info(f'reservation={reservation}, time to serve={time_to_serve / MILLISECOND}, fidelity={fidelity:.6f}')


# the request type-2 app, testing on a five node linear network, for time-to-serve
def line_5_node():

    purify = True

    network_config = 'config/line_5.json'

    # log_filename = 'log/linear_adaptive'
    log_filename = 'log/queue_tts/line5,qmem=1,update=true'

    network_topo = RouterNetTopoAdaptive(network_config)
    
    tl = network_topo.get_timeline()

    log.set_logger(__name__, tl, log_filename)
    log.set_logger_level('DEBUG')
    # modules = ['request_app', 'swapping', 'rule_manager', 'resource_manager', 'generation', 'memory', 'main_test', 'purification', 'bsm']
    modules = ['main_test']
    for module in modules:
        log.track_module(module)

    name_to_apps = {}
    for router in network_topo.get_nodes_by_type(RouterNetTopo.QUANTUM_ROUTER):
        app = RequestAppTimeToServe(router)
        name_to_apps[router.name] = app
        # if router.name not in ['router_4', 'router_5']:
        #     router.active = False
        router.adaptive_continuous.has_empty_neighbor = True
        router.adaptive_continuous.update_prob = True
        router.resource_manager.purify = purify

    mem_size = 1
    num_nodes = len(name_to_apps)
    traffic_matrix = TrafficMatrix(num_nodes)
    traffic_matrix.line_5()
    request_queue = traffic_matrix.get_request_queue_tts(request_period=1, end_time=10, memo_size=mem_size, fidelity=0.7, entanglement_number=1)
    for request in request_queue[:]:
        id, src_name, dst_name, start_time, end_time, memo_size, fidelity, entanglement_number = request
        app = name_to_apps[src_name]
        app.start(dst_name, start_time, end_time, memo_size, fidelity, entanglement_number, id)

    tl.init()
    tl.run()

    time_to_serve_dict = defaultdict(float)
    fidelity_dict = defaultdict(list)
    for _, app in name_to_apps.items():
        time_to_serve_dict |= app.time_to_serve
        fidelity_dict |= app.entanglement_fidelities

    for reservation, time_to_serve in sorted(time_to_serve_dict.items()):
        fidelity = fidelity_dict[reservation][0]
        log.logger.info(f'reservation={reservation}, time to serve={time_to_serve / MILLISECOND}, fidelity={fidelity:.6f}')


# the request type-2 app, testing on a ten node bottleneck network, for time-to-serve
def bottleneck_10_node():

    network_config = 'config/bottleneck_10.json'

    # log_filename = 'log/queue_tts/bottleneck,qmem=0'
    log_filename = 'log/queue_tts/bottleneck,qmem=5,update=true'

    network_topo = RouterNetTopoAdaptive(network_config)
    
    tl = network_topo.get_timeline()

    log.set_logger(__name__, tl, log_filename)
    log.set_logger_level('INFO')
    # modules = ['timeline', 'network_manager', 'resource_manager', 'rule_manager', 'generation', 
    #            'purification', 'swapping', 'bsm', 'adaptive_continuous', 'memory_manager']
    modules = ['adaptive_continuous', 'request_app', 'swap_memory', 'swapping', 'rule_manager', 'timeline', 'resource_manager', 'generation', 'main']
    # modules = ['adaptive_continuous', 'request_app', 'swap_memory', 'reservation', 'resource_manager', 'rule_manager', 'generation', 'swapping']
    for module in modules:
        log.track_module(module)

    name_to_apps = {}
    for router in network_topo.get_nodes_by_type(RouterNetTopo.QUANTUM_ROUTER):
        app = RequestAppTimeToServe(router)
        name_to_apps[router.name] = app
        # if router.name not in ['router_4', 'router_5']:
        #     router.active = False
        router.adaptive_continuous.has_empty_neighbor = True
        router.adaptive_continuous.update_prob = True

    num_nodes = len(name_to_apps)
    traffic_matrix = TrafficMatrix(num_nodes)
    traffic_matrix.bottleneck_10()
    request_queue = traffic_matrix.get_request_queue_tts(request_period=1, end_time=200, memo_size=1, fidelity=0.6, entanglement_number=1)
    for request in request_queue:
        id, src_name, dst_name, start_time, end_time, memo_size, fidelity, entanglement_number = request
        app = name_to_apps[src_name]
        app.start(dst_name, start_time, end_time, memo_size, fidelity, entanglement_number, id)

    tl.init()
    tl.run()

    time_to_serve_dict = defaultdict(float)
    for _, app in name_to_apps.items():
        time_to_serve_dict |= app.time_to_serve

    for reservation, time_to_serve in sorted(time_to_serve_dict.items()):
        log.logger.info(f'reservation={reservation}, time to serve={time_to_serve / MILLISECOND}')


# the request type-2 (time-to-serve) app, testing on a 10 node random network, for time-to-serve, distributed quantum computing
def random_10_node_dqc_central():

    np.random.seed(0)
    REQUEST_PERIOD = 1 # seconds, request incoming rate, assuming reqeust arrives one by one
    DELTA = 0.02         # seconds, time for EP pre-generation

    purify = False
    strategy = 'freshest'
    log_filename = 'log/tmp/random10,numqubit=10,central'
    # log_filename = 'tmp/log/random10,numqubit=10,breaking_1-9'
    
    network_config = 'config/random_10.json'
    network_topo = RouterNetTopoAdaptive(network_config)
    
    tl = network_topo.get_timeline()

    log.set_logger(__name__, tl, log_filename)
    log.set_logger_level('DEBUG')
    # log.set_logger_level('INFO')
    # modules = ['controller', 'network_controller', 'node', 'timeline',  'main_test', 'routing', 'generation']
    modules = ['main_test']
    for module in modules:
        log.track_module(module)

    name_to_apps = {}
    for router in network_topo.get_nodes_by_type(RouterNetTopo.QUANTUM_ROUTER):
        app = RequestAppTimeToServe(router)
        name_to_apps[router.name] = app
        # if router.name not in ['router_4', 'router_5']:
        #     router.active = False
        router.adaptive_continuous.has_empty_neighbor = True
        router.adaptive_continuous.update_prob = True
        router.adaptive_continuous.strategy = strategy
        router.adaptive_continuous.update_period(REQUEST_PERIOD * SECOND)
        router.resource_manager.purify = purify

    controller: Controller = None
    for con in network_topo.get_nodes_by_type(RouterNetTopo.CONTROLLER):
        controller = con
        break

    controller.dqc_server.num_qubit_per_worker = 4
    queue_length = 10
    num_qubits_lower = 10
    num_qubits_upper = 11
    start_time = 0.1
    app_period = REQUEST_PERIOD
    dqc_app_queue = DQC_APP_Queue.generate_random_queue(queue_length, num_qubits_lower, num_qubits_upper, start_time, app_period)
    controller.dqc_server.load(dqc_app_queue)
    controller.dqc_server.generate_network_request()

    # breaking_link = BreakingLink('breaking_link', tl, network_topo.get_qchannels(), network_topo.get_cchannels())
    # breaking_link_queue = [(0.5*MILLISECOND, 'router_9', 'router_1')]
    # breaking_link.load(breaking_link_queue)

    # num_nodes = len(name_to_apps)
    # traffic_matrix = TrafficMatrix(num_nodes)
    # traffic_matrix.line_2()
    # request_queue = []
    # # TODO put the traffic matrix in the controller
    # request_queue = traffic_matrix.get_request_queue_tts(request_queue=request_queue, request_period=REQUEST_PERIOD, delta=DELTA, \
    #                                                      start_time=0, end_time=1, memo_size=1, fidelity=0.6, entanglement_number=1, controller=controller)
    # for request in request_queue:
    #     id, src_name, dst_name, start_time, end_time, memo_size, fidelity, entanglement_number = request
    #     app = name_to_apps[src_name]
    #     app.start(dst_name, start_time, end_time, memo_size, fidelity, entanglement_number, id)

    tl.init()
    tl.run()

    time_to_serve_dict = defaultdict(float)
    fidelity_dict = defaultdict(list)
    for _, app in name_to_apps.items():
        time_to_serve_dict |= app.time_to_serve
        fidelity_dict |= app.entanglement_fidelities

    for reservation, time_to_serve in sorted(time_to_serve_dict.items()):
        fidelities = fidelity_dict[reservation]
        fidelity = np.average(fidelities)
        tts = time_to_serve / MILLISECOND
        avg_ep = tts / reservation.entanglement_number
        log.logger.info(f'reservation={reservation}, time_to_serve={tts:.4f}, avg_ep_latency={avg_ep:.4f}, avg_fidelity={fidelity:.4f}')


# the request type-2 (time-to-serve) app, testing on a 10 node random network, for time-to-serve, distributed quantum computing
def random_10_node_dqc_decentral():

    np.random.seed(0)
    REQUEST_PERIOD = 1 # seconds, request incoming rate, assuming reqeust arrives one by one
    DELTA = 0.02         # seconds, time for EP pre-generation

    purify = False
    strategy = 'freshest'
    log_filename = 'log/tmp/random10,numqubit=10,decentral'
    # log_filename = 'tmp/log/random10,numqubit=10,breaking_1-9'
    
    network_config = 'config/random_10.json'
    network_topo = RouterNetTopoAdaptive(network_config)
    
    tl = network_topo.get_timeline()

    log.set_logger(__name__, tl, log_filename)
    log.set_logger_level('DEBUG')
    # log.set_logger_level('INFO')
    # modules = ['controller', 'network_controller', 'node', 'timeline',  'main_test', 'routing', 'generation']
    modules = ['main_test']
    for module in modules:
        log.track_module(module)

    name_to_apps = {}
    for router in network_topo.get_nodes_by_type(RouterNetTopo.QUANTUM_ROUTER):
        app = RequestAppTimeToServe(router)
        name_to_apps[router.name] = app
        # if router.name not in ['router_4', 'router_5']:
        #     router.active = False
        router.adaptive_continuous.has_empty_neighbor = True
        router.adaptive_continuous.update_prob = True
        router.adaptive_continuous.strategy = strategy
        router.adaptive_continuous.update_period(REQUEST_PERIOD * SECOND)
        router.resource_manager.purify = purify

    controller: Controller = None
    for con in network_topo.get_nodes_by_type(RouterNetTopo.CONTROLLER):
        controller = con
        controller.routing = False
        break

    controller.dqc_server.num_qubit_per_worker = 4
    queue_length = 10
    num_qubits_lower = 10
    num_qubits_upper = 11
    start_time = 0.1
    app_period = REQUEST_PERIOD
    dqc_app_queue = DQC_APP_Queue.generate_random_queue(queue_length, num_qubits_lower, num_qubits_upper, start_time, app_period)
    controller.dqc_server.load(dqc_app_queue)
    controller.dqc_server.generate_network_request()

    # breaking_link = BreakingLink('breaking_link', tl, network_topo.get_qchannels(), network_topo.get_cchannels())
    # breaking_link_queue = [(0.5*MILLISECOND, 'router_9', 'router_1')]
    # breaking_link.load(breaking_link_queue)

    # num_nodes = len(name_to_apps)
    # traffic_matrix = TrafficMatrix(num_nodes)
    # traffic_matrix.line_2()
    # request_queue = []
    # # TODO put the traffic matrix in the controller
    # request_queue = traffic_matrix.get_request_queue_tts(request_queue=request_queue, request_period=REQUEST_PERIOD, delta=DELTA, \
    #                                                      start_time=0, end_time=1, memo_size=1, fidelity=0.6, entanglement_number=1, controller=controller)
    # for request in request_queue:
    #     id, src_name, dst_name, start_time, end_time, memo_size, fidelity, entanglement_number = request
    #     app = name_to_apps[src_name]
    #     app.start(dst_name, start_time, end_time, memo_size, fidelity, entanglement_number, id)

    tl.init()
    tl.run()

    time_to_serve_dict = defaultdict(float)
    fidelity_dict = defaultdict(list)
    for _, app in name_to_apps.items():
        time_to_serve_dict |= app.time_to_serve
        fidelity_dict |= app.entanglement_fidelities

    for reservation, time_to_serve in sorted(time_to_serve_dict.items()):
        fidelities = fidelity_dict[reservation]
        fidelity = np.average(fidelities)
        tts = time_to_serve / MILLISECOND
        avg_ep = tts / reservation.entanglement_number
        log.logger.info(f'reservation={reservation}, time_to_serve={tts:.4f}, avg_ep_latency={avg_ep:.4f}, avg_fidelity={fidelity:.4f}')



# the request type-2 app, testing on a twenty node bottleneck network, for time-to-serve
def as_20_node():

    update_prob = True

    network_config = 'config/as_20.json'

    # log_filename = 'log/queue_tts/as20,qmem=0'
    log_filename = f'log/queue_tts/as20,qmem=5,update={update_prob}'

    network_topo = RouterNetTopoAdaptive(network_config)
    
    tl = network_topo.get_timeline()

    log.set_logger(__name__, tl, log_filename)
    log.set_logger_level('INFO')
    # modules = ['timeline', 'network_manager', 'resource_manager', 'rule_manager', 'generation', 
    #            'purification', 'swapping', 'bsm', 'adaptive_continuous', 'memory_manager']
    modules = ['adaptive_continuous', 'request_app', 'swapping', 'network_manager', 'resource_manager', 'main', 'rule_manager', 'generation', 'swapping', 'timeline']
    # modules = ['adaptive_continuous', 'request_app', 'swap_memory', 'reservation', 'resource_manager', 'rule_manager', 'generation', 'swapping']
    for module in modules:
        log.track_module(module)

    name_to_apps = {}
    for router in network_topo.get_nodes_by_type(RouterNetTopo.QUANTUM_ROUTER):
        app = RequestAppTimeToServe(router)
        name_to_apps[router.name] = app
        # if router.name not in ['router_4', 'router_5']:
        #     router.active = False
        router.adaptive_continuous.has_empty_neighbor = True
        router.adaptive_continuous.update_prob = update_prob

    num_nodes = len(name_to_apps)
    traffic_matrix = TrafficMatrix(num_nodes)
    traffic_matrix.as_20()
    request_queue = traffic_matrix.get_request_queue_tts(request_period=1, end_time=200, memo_size=1, fidelity=0.6, entanglement_number=1)
    for request in request_queue:
        id, src_name, dst_name, start_time, end_time, memo_size, fidelity, entanglement_number = request
        app = name_to_apps[src_name]
        app.start(dst_name, start_time, end_time, memo_size, fidelity, entanglement_number, id)

    tl.init()
    tl.run()

    time_to_serve_dict = defaultdict(float)
    for _, app in name_to_apps.items():
        time_to_serve_dict |= app.time_to_serve

    for reservation, time_to_serve in sorted(time_to_serve_dict.items()):
        log.logger.info(f'reservation={reservation}, time to serve={time_to_serve / MILLISECOND}')


# the request type-2 app, testing on a twenty node bottleneck network, for time-to-serve
def as_100_node():

    update_prob = True
    memory_adaptive = 5

    network_config = 'config/as_100.json'
    log_filename = f'log/queue_tts/as100,qmem={memory_adaptive},update={update_prob}'

    network_topo = RouterNetTopoAdaptive(network_config)
    
    tl = network_topo.get_timeline()
    log.set_logger(__name__, tl, log_filename)
    log.set_logger_level('DEBUG')
    # modules = ['timeline', 'network_manager', 'resource_manager', 'rule_manager', 'generation', 
    #            'purification', 'swapping', 'bsm', 'adaptive_continuous', 'memory_manager']
    modules = ['adaptive_continuous', 'request_app', 'network_manager', 'resource_manager', 'main_test', 'memory', 'swapping', 'generation']
    # modules = ['adaptive_continuous', 'request_app', 'swap_memory', 'reservation', 'resource_manager', 'rule_manager', 'generation', 'swapping']
    for module in modules:
        log.track_module(module)

    name_to_apps = {}
    for router in network_topo.get_nodes_by_type(RouterNetTopo.QUANTUM_ROUTER):
        app = RequestAppTimeToServe(router)
        name_to_apps[router.name] = app
        # if router.name not in ['router_4', 'router_5']:
        #     router.active = False
        router.adaptive_continuous.has_empty_neighbor = True
        router.adaptive_continuous.update_prob = update_prob
        router.adaptive_continuous.set_adaptive_max_memory(memory_adaptive)      

    num_nodes = len(name_to_apps)
    traffic_matrix = TrafficMatrix(num_nodes)
    traffic_matrix.as_100()
    # traffic_matrix.as_100_()
    request_queue = traffic_matrix.get_request_queue_tts(request_period=1, end_time=10, memo_size=1, fidelity=0.6, entanglement_number=1)
    print(request_queue)
    for request in request_queue[:1]:
        id, src_name, dst_name, start_time, end_time, memo_size, fidelity, entanglement_number = request
        app = name_to_apps[src_name]
        app.start(dst_name, start_time, end_time, memo_size, fidelity, entanglement_number, id)

    tl.init()
    tl.run()

    time_to_serve_dict = defaultdict(float)
    fidelity_dict      = defaultdict(list)
    for _, app in name_to_apps.items():
        time_to_serve_dict |= app.time_to_serve
        fidelity_dict |= app.entanglement_fidelities

    for reservation, time_to_serve in sorted(time_to_serve_dict.items()):
        fidelity = fidelity_dict[reservation][0]
        log.logger.info(f'reservation={reservation}, time to serve={time_to_serve / MILLISECOND}, fidelity={fidelity:.6f}')



if __name__ == '__main__':


    # line_2_node_dqc()
    # line_5_node()

    random_10_node_dqc_central()

    random_10_node_dqc_decentral()

    # bottleneck_10_node()
    # as_20_node()
    # as_100_node()

