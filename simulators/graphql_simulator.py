#!/usr/bin/env python3
"""
GraphQL Simulator for Tank Monitoring System

This simulator creates a GraphQL server that provides tank level data.
The backend can connect to this server to fetch tank data via GraphQL queries.
"""

import argparse
import json
import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import threading

try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
except ImportError:
    print("Error: Flask and flask-cors are required. Install with:")
    print("pip install flask flask-cors")
    exit(1)

class TankData:
    """Represents tank data with realistic simulation"""
    
    def __init__(self, tank_id: str, name: str, capacity: float):
        self.tank_id = tank_id
        self.name = name
        self.capacity = capacity
        self.current_level = random.uniform(20, 80)  # Start with random level
        self.last_updated = datetime.now()
        self.readings_history = []
        
    def update_level(self):
        """Simulate realistic tank level changes"""
        # Simulate gradual changes with some randomness
        change = random.uniform(-2, 1)  # Slight downward trend (consumption)
        self.current_level = max(0, min(100, self.current_level + change))
        self.last_updated = datetime.now()
        
        # Add to history
        reading = {
            "timestamp": self.last_updated.isoformat(),
            "level": round(self.current_level, 2),
            "tank_id": self.tank_id
        }
        self.readings_history.append(reading)
        
        # Keep only last 100 readings
        if len(self.readings_history) > 100:
            self.readings_history = self.readings_history[-100:]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tank data to dictionary for GraphQL response"""
        return {
            "id": self.tank_id,
            "name": self.name,
            "capacity": self.capacity,
            "level": round(self.current_level, 2),
            "lastUpdated": self.last_updated.isoformat(),
            "status": self.get_status(),
            "readings": self.readings_history[-10:]  # Last 10 readings
        }
    
    def get_status(self) -> str:
        """Get tank status based on level"""
        if self.current_level < 10:
            return "LOW"
        elif self.current_level > 90:
            return "HIGH"
        else:
            return "NORMAL"

class GraphQLSimulator:
    """GraphQL server simulator for tank data"""
    
    def __init__(self, port: int = 4000):
        self.port = port
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Initialize tank data
        self.tanks = {
            "tank1": TankData("tank1", "Main Storage Tank", 10000),
            "tank2": TankData("tank2", "Secondary Tank", 5000),
            "tank3": TankData("tank3", "Emergency Reserve", 2000),
        }
        
        # Start background thread to update tank levels
        self.running = True
        self.update_thread = threading.Thread(target=self._update_tanks_continuously)
        self.update_thread.daemon = True
        
        self._setup_routes()
    
    def _update_tanks_continuously(self):
        """Background thread to continuously update tank levels"""
        while self.running:
            for tank in self.tanks.values():
                tank.update_level()
            time.sleep(30)  # Update every 30 seconds
    
    def _setup_routes(self):
        """Setup Flask routes for GraphQL endpoint"""
        
        @self.app.route('/graphql', methods=['POST', 'GET'])
        def graphql_endpoint():
            if request.method == 'GET':
                # Return GraphQL schema for introspection
                return jsonify({
                    "data": {
                        "__schema": {
                            "types": [
                                {
                                    "name": "Tank",
                                    "fields": [
                                        {"name": "id", "type": "String"},
                                        {"name": "name", "type": "String"},
                                        {"name": "capacity", "type": "Float"},
                                        {"name": "level", "type": "Float"},
                                        {"name": "lastUpdated", "type": "String"},
                                        {"name": "status", "type": "String"},
                                        {"name": "readings", "type": "[Reading]"}
                                    ]
                                }
                            ]
                        }
                    }
                })
            
            # Handle GraphQL queries
            data = request.get_json()
            if not data or 'query' not in data:
                return jsonify({"errors": [{"message": "No query provided"}]}), 400
            
            query = data['query']
            variables = data.get('variables', {})
            
            return self._execute_query(query, variables)
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})
        
        @self.app.route('/', methods=['GET'])
        def index():
            return jsonify({
                "message": "GraphQL Tank Simulator",
                "endpoints": {
                    "graphql": "/graphql",
                    "health": "/health"
                },
                "sample_queries": {
                    "get_all_tanks": "{ tanks { id name level status } }",
                    "get_tank_by_id": "{ tank(id: \"tank1\") { id name level lastUpdated readings { timestamp level } } }"
                }
            })
    
    def _execute_query(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute GraphQL query and return response"""
        try:
            # Simple query parsing (in production, use a proper GraphQL library)
            if "tanks" in query and "tank(" not in query:
                # Query for all tanks
                return jsonify({
                    "data": {
                        "tanks": [tank.to_dict() for tank in self.tanks.values()]
                    }
                })
            
            elif "tank(" in query:
                # Query for specific tank
                tank_id = variables.get('tankId') or self._extract_tank_id_from_query(query)
                if tank_id and tank_id in self.tanks:
                    return jsonify({
                        "data": {
                            "tank": self.tanks[tank_id].to_dict()
                        }
                    })
                else:
                    return jsonify({
                        "data": {"tank": None},
                        "errors": [{"message": f"Tank with id '{tank_id}' not found"}]
                    })
            
            else:
                return jsonify({
                    "errors": [{"message": "Unsupported query"}]
                })
                
        except Exception as e:
            return jsonify({
                "errors": [{"message": f"Query execution error: {str(e)}"}]
            })
    
    def _extract_tank_id_from_query(self, query: str) -> str:
        """Extract tank ID from GraphQL query string"""
        import re
        match = re.search(r'tank\s*\(\s*id\s*:\s*["\']([^"\']+)["\']', query)
        return match.group(1) if match else None
    
    def start(self):
        """Start the GraphQL simulator server"""
        print(f"🚀 Starting GraphQL Tank Simulator on port {self.port}")
        print(f"📡 GraphQL endpoint: http://localhost:{self.port}/graphql")
        print(f"🏥 Health check: http://localhost:{self.port}/health")
        print(f"📖 API info: http://localhost:{self.port}/")
        print("\n📋 Sample GraphQL Queries:")
        print("  All tanks: { tanks { id name level status } }")
        print("  Specific tank: { tank(id: \"tank1\") { id name level lastUpdated } }")
        print("\n⏹️  Press Ctrl+C to stop")
        
        self.update_thread.start()
        
        try:
            self.app.run(host='0.0.0.0', port=self.port, debug=False)
        except KeyboardInterrupt:
            print("\n🛑 Stopping GraphQL simulator...")
            self.running = False
        except Exception as e:
            print(f"❌ Error starting server: {e}")

def main():
    parser = argparse.ArgumentParser(description="GraphQL Tank Data Simulator")
    parser.add_argument("--port", type=int, default=4000, 
                       help="Port to run GraphQL server on (default: 4000)")
    
    args = parser.parse_args()
    
    simulator = GraphQLSimulator(port=args.port)
    simulator.start()

if __name__ == "__main__":
    main()
