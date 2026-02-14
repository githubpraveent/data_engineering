"""
Mock server manager
"""
import logging
from typing import Dict, Any, Optional
from framework.simulation.simulator import APISimulator
from framework.config import get_config

logger = logging.getLogger(__name__)


class MockServer:
    """Manages mock servers for downstream services"""
    
    def __init__(self):
        self.config = get_config()
        self.simulators: Dict[str, APISimulator] = {}
    
    def start_service_simulation(self, service_name: str) -> Optional[APISimulator]:
        """Start simulation for a downstream service"""
        service_config = self.config.downstream_services.get(service_name)
        if not service_config:
            logger.warning(f"Service {service_name} not found in config")
            return None
        
        if not service_config.get("use_simulation", False):
            logger.info(f"Service {service_name} is not configured for simulation")
            return None
        
        port = service_config.get("simulation_port", 8080)
        
        if service_name in self.simulators:
            logger.info(f"Simulator for {service_name} already exists")
            return self.simulators[service_name]
        
        simulator = APISimulator(port=port)
        simulator.start()
        self.simulators[service_name] = simulator
        
        logger.info(f"Started simulation for service {service_name} on port {port}")
        return simulator
    
    def stop_service_simulation(self, service_name: str):
        """Stop simulation for a downstream service"""
        if service_name in self.simulators:
            self.simulators[service_name].stop()
            del self.simulators[service_name]
            logger.info(f"Stopped simulation for service {service_name}")
    
    def get_simulator(self, service_name: str) -> Optional[APISimulator]:
        """Get simulator for a service"""
        return self.simulators.get(service_name)
    
    def start_all_simulations(self):
        """Start all configured service simulations"""
        for service_name in self.config.downstream_services.keys():
            self.start_service_simulation(service_name)
    
    def stop_all_simulations(self):
        """Stop all service simulations"""
        for service_name in list(self.simulators.keys()):
            self.stop_service_simulation(service_name)

