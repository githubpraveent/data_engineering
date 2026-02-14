"""
API Simulation for downstream services
"""
import json
import logging
from typing import Dict, Any, Optional, Callable, List
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
from framework.config import get_config

logger = logging.getLogger(__name__)


class APISimulator:
    """Simulates downstream API services"""
    
    def __init__(self, port: int = 8080):
        self.app = Flask(__name__)
        CORS(self.app)
        self.port = port
        self.server_thread: Optional[threading.Thread] = None
        self.routes: Dict[str, Dict[str, Callable]] = {}
        self.request_history: List[Dict[str, Any]] = []
        self._setup_default_routes()
    
    def _setup_default_routes(self):
        """Setup default routes"""
        @self.app.route('/health', methods=['GET'])
        def health():
            return jsonify({"status": "healthy"}), 200
        
        @self.app.route('/requests', methods=['GET'])
        def get_requests():
            return jsonify(self.request_history), 200
        
        @self.app.route('/requests', methods=['DELETE'])
        def clear_requests():
            self.request_history.clear()
            return jsonify({"message": "Request history cleared"}), 200
    
    def register_endpoint(
        self,
        path: str,
        method: str = "GET",
        handler: Callable = None,
        response: Dict[str, Any] = None,
        status_code: int = 200,
        delay: float = 0
    ):
        """
        Register an endpoint
        
        Args:
            path: Endpoint path
            method: HTTP method
            handler: Custom handler function (takes request, returns response)
            response: Static response to return
            status_code: HTTP status code
            delay: Response delay in seconds
        """
        method = method.upper()
        
        if path not in self.routes:
            self.routes[path] = {}
        
        def endpoint_handler():
            # Log request
            request_data = {
                "method": method,
                "path": path,
                "headers": dict(request.headers),
                "args": dict(request.args),
                "json": request.get_json(silent=True),
                "data": request.get_data(as_text=True)
            }
            self.request_history.append(request_data)
            logger.info(f"Simulated {method} {path}: {request_data}")
            
            # Add delay if specified
            if delay > 0:
                import time
                time.sleep(delay)
            
            # Use custom handler if provided
            if handler:
                try:
                    return handler(request)
                except Exception as e:
                    logger.error(f"Handler error: {e}")
                    return jsonify({"error": str(e)}), 500
            
            # Use static response
            if response:
                return jsonify(response), status_code
            
            return jsonify({"message": f"Simulated {method} {path}"}), 200
        
        # Register route
        endpoint_handler.__name__ = f"handle_{method.lower()}_{path.replace('/', '_')}"
        self.app.add_url_rule(
            path,
            endpoint_handler.__name__,
            endpoint_handler,
            methods=[method]
        )
        
        self.routes[path][method] = endpoint_handler
        logger.info(f"Registered simulated endpoint: {method} {path}")
    
    def start(self):
        """Start the simulation server"""
        if self.server_thread and self.server_thread.is_alive():
            logger.warning("Simulator already running")
            return
        
        def run_server():
            self.app.run(port=self.port, debug=False, use_reloader=False)
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        logger.info(f"API Simulator started on port {self.port}")
    
    def stop(self):
        """Stop the simulation server"""
        # Flask doesn't have a clean shutdown, so we'll just mark it
        logger.info("API Simulator stopped")
    
    def get_request_history(self, path: str = None, method: str = None) -> List[Dict[str, Any]]:
        """Get request history, optionally filtered"""
        history = self.request_history
        if path:
            history = [r for r in history if r["path"] == path]
        if method:
            history = [r for r in history if r["method"] == method.upper()]
        return history
    
    def clear_history(self):
        """Clear request history"""
        self.request_history.clear()
        logger.info("Request history cleared")

