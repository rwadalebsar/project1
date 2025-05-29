#!/usr/bin/env python3
"""
OPC UA Simulator for Tank Monitoring System

This simulator creates an OPC UA server that provides tank level data.
The backend can connect to this server to read tank data via OPC UA protocol.
"""

import argparse
import asyncio
import random
import time
from datetime import datetime
from typing import Dict, Any
import logging

try:
    from asyncua import Server, ua
    from asyncua.common.node import Node
except ImportError:
    print("Error: asyncua is required. Install with:")
    print("pip install asyncua")
    exit(1)

class TankNode:
    """Represents a tank as an OPC UA node"""
    
    def __init__(self, tank_id: str, name: str, capacity: float):
        self.tank_id = tank_id
        self.name = name
        self.capacity = capacity
        self.current_level = random.uniform(20, 80)
        self.last_updated = datetime.now()
        
        # OPC UA nodes (will be set during server setup)
        self.level_node = None
        self.status_node = None
        self.capacity_node = None
        self.last_updated_node = None
    
    def update_level(self):
        """Simulate realistic tank level changes"""
        # Simulate gradual changes with some randomness
        change = random.uniform(-2, 1)  # Slight downward trend
        self.current_level = max(0, min(100, self.current_level + change))
        self.last_updated = datetime.now()
    
    def get_status(self) -> str:
        """Get tank status based on level"""
        if self.current_level < 10:
            return "LOW"
        elif self.current_level > 90:
            return "HIGH"
        else:
            return "NORMAL"

class OPCUASimulator:
    """OPC UA server simulator for tank data"""
    
    def __init__(self, port: int = 4840, endpoint: str = None):
        self.port = port
        self.endpoint = endpoint or f"opc.tcp://0.0.0.0:{port}/freeopcua/server/"
        self.server = Server()
        self.running = False
        
        # Initialize tank data
        self.tanks = {
            "tank1": TankNode("tank1", "Main Storage Tank", 10000),
            "tank2": TankNode("tank2", "Secondary Tank", 5000),
            "tank3": TankNode("tank3", "Emergency Reserve", 2000),
        }
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def setup_server(self):
        """Setup OPC UA server with tank nodes"""
        # Set server endpoint
        await self.server.init()
        self.server.set_endpoint(self.endpoint)
        
        # Set server name
        self.server.set_server_name("Tank Monitoring OPC UA Simulator")
        
        # Setup namespace
        uri = "http://tank-monitoring.simulator"
        idx = await self.server.register_namespace(uri)
        
        # Create root object for tanks
        tanks_object = await self.server.nodes.objects.add_object(idx, "Tanks")
        
        # Create tank nodes
        for tank_id, tank in self.tanks.items():
            # Create tank object
            tank_object = await tanks_object.add_object(idx, tank.name)
            
            # Add tank properties
            tank.level_node = await tank_object.add_variable(
                idx, "Level", tank.current_level, ua.VariantType.Float
            )
            await tank.level_node.set_writable()
            
            tank.status_node = await tank_object.add_variable(
                idx, "Status", tank.get_status(), ua.VariantType.String
            )
            
            tank.capacity_node = await tank_object.add_variable(
                idx, "Capacity", tank.capacity, ua.VariantType.Float
            )
            
            tank.last_updated_node = await tank_object.add_variable(
                idx, "LastUpdated", tank.last_updated.isoformat(), ua.VariantType.String
            )
            
            # Add tank ID as property
            await tank_object.add_property(idx, "TankID", tank.tank_id)
        
        self.logger.info(f"OPC UA server setup complete with {len(self.tanks)} tanks")
    
    async def update_tank_values(self):
        """Continuously update tank values"""
        while self.running:
            try:
                for tank in self.tanks.values():
                    # Update tank data
                    tank.update_level()
                    
                    # Update OPC UA nodes
                    if tank.level_node:
                        await tank.level_node.write_value(tank.current_level)
                    
                    if tank.status_node:
                        await tank.status_node.write_value(tank.get_status())
                    
                    if tank.last_updated_node:
                        await tank.last_updated_node.write_value(tank.last_updated.isoformat())
                
                # Wait before next update
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error updating tank values: {e}")
                await asyncio.sleep(5)
    
    async def start(self):
        """Start the OPC UA simulator server"""
        try:
            print(f"🚀 Starting OPC UA Tank Simulator")
            print(f"📡 Endpoint: {self.endpoint}")
            print(f"🏥 Server will provide data for {len(self.tanks)} tanks")
            print("\n📋 Available Tanks:")
            for tank_id, tank in self.tanks.items():
                print(f"  - {tank_id}: {tank.name} (Capacity: {tank.capacity}L)")
            print("\n⏹️  Press Ctrl+C to stop")
            
            # Setup server
            await self.setup_server()
            
            # Start server
            async with self.server:
                self.running = True
                self.logger.info(f"OPC UA server started on {self.endpoint}")
                
                # Start background task to update values
                update_task = asyncio.create_task(self.update_tank_values())
                
                try:
                    # Keep server running
                    while self.running:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    print("\n🛑 Stopping OPC UA simulator...")
                    self.running = False
                    update_task.cancel()
                    
        except Exception as e:
            self.logger.error(f"Error starting OPC UA server: {e}")
            print(f"❌ Failed to start OPC UA server: {e}")

def main():
    parser = argparse.ArgumentParser(description="OPC UA Tank Data Simulator")
    parser.add_argument("--port", type=int, default=4840,
                       help="Port to run OPC UA server on (default: 4840)")
    parser.add_argument("--endpoint", type=str,
                       help="Custom OPC UA endpoint URL")
    
    args = parser.parse_args()
    
    simulator = OPCUASimulator(port=args.port, endpoint=args.endpoint)
    
    # Run the async server
    try:
        asyncio.run(simulator.start())
    except KeyboardInterrupt:
        print("\n👋 OPC UA simulator stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
