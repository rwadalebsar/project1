#!/usr/bin/env python3
"""
Modbus Simulator for Tank Monitoring System

This simulator creates a Modbus TCP server that provides tank level data.
The backend can connect to this server to read tank data via Modbus protocol.
"""

import argparse
import random
import time
import threading
from datetime import datetime
from typing import Dict, List
import logging

try:
    from pymodbus.server.sync import StartTcpServer
    from pymodbus.device import ModbusDeviceIdentification
    from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
    from pymodbus.constants import Endian
    from pymodbus.payload import BinaryPayloadBuilder, BinaryPayloadDecoder
except ImportError:
    print("Error: pymodbus is required. Install with:")
    print("pip install pymodbus")
    exit(1)

class TankData:
    """Represents tank data for Modbus simulation"""
    
    def __init__(self, tank_id: str, name: str, capacity: float, base_address: int):
        self.tank_id = tank_id
        self.name = name
        self.capacity = capacity
        self.base_address = base_address  # Starting Modbus address for this tank
        self.current_level = random.uniform(20, 80)
        self.last_updated = datetime.now()
        
        # Modbus register mapping (each tank uses 10 registers)
        # Address + 0: Level (float, 2 registers)
        # Address + 2: Capacity (float, 2 registers) 
        # Address + 4: Status (int, 1 register) - 0=NORMAL, 1=LOW, 2=HIGH
        # Address + 5: Tank ID (int, 1 register)
        # Address + 6: Timestamp (int, 4 registers) - Unix timestamp
    
    def update_level(self):
        """Simulate realistic tank level changes"""
        change = random.uniform(-2, 1)  # Slight downward trend
        self.current_level = max(0, min(100, self.current_level + change))
        self.last_updated = datetime.now()
    
    def get_status_code(self) -> int:
        """Get tank status as integer code"""
        if self.current_level < 10:
            return 1  # LOW
        elif self.current_level > 90:
            return 2  # HIGH
        else:
            return 0  # NORMAL
    
    def get_modbus_data(self) -> List[int]:
        """Convert tank data to Modbus register values"""
        builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Big)
        
        # Level (float, 2 registers)
        builder.add_32bit_float(self.current_level)
        
        # Capacity (float, 2 registers)
        builder.add_32bit_float(self.capacity)
        
        # Status (int, 1 register)
        builder.add_16bit_uint(self.get_status_code())
        
        # Tank ID hash (int, 1 register)
        tank_id_hash = hash(self.tank_id) % 65536
        builder.add_16bit_uint(tank_id_hash)
        
        # Timestamp (int, 2 registers for 32-bit timestamp)
        timestamp = int(self.last_updated.timestamp())
        builder.add_32bit_uint(timestamp)
        
        # Convert to register values
        payload = builder.build()
        decoder = BinaryPayloadDecoder.fromRegisters(
            [int.from_bytes(payload[i:i+2], 'big') for i in range(0, len(payload), 2)],
            byteorder=Endian.Big,
            wordorder=Endian.Big
        )
        
        # Return as list of 16-bit register values
        registers = []
        for i in range(0, len(payload), 2):
            if i + 1 < len(payload):
                reg_value = (payload[i] << 8) | payload[i + 1]
                registers.append(reg_value)
        
        return registers

class ModbusSimulator:
    """Modbus TCP server simulator for tank data"""
    
    def __init__(self, port: int = 502, host: str = "0.0.0.0"):
        self.port = port
        self.host = host
        self.running = False
        
        # Initialize tank data with Modbus addresses
        self.tanks = {
            "tank1": TankData("tank1", "Main Storage Tank", 10000, 0),    # Registers 0-9
            "tank2": TankData("tank2", "Secondary Tank", 5000, 10),       # Registers 10-19
            "tank3": TankData("tank3", "Emergency Reserve", 2000, 20),    # Registers 20-29
        }
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Setup Modbus context
        self.context = self._setup_modbus_context()
        
        # Start background thread for data updates
        self.update_thread = threading.Thread(target=self._update_tanks_continuously)
        self.update_thread.daemon = True
    
    def _setup_modbus_context(self):
        """Setup Modbus server context with tank data"""
        # Create data blocks (we'll use holding registers)
        # Reserve 100 registers for tank data
        holding_registers = ModbusSequentialDataBlock(0, [0] * 100)
        
        # Create slave context
        slave_context = ModbusSlaveContext(
            di=None,  # Discrete inputs
            co=None,  # Coils
            hr=holding_registers,  # Holding registers
            ir=None   # Input registers
        )
        
        # Create server context
        context = ModbusServerContext(slaves=slave_context, single=True)
        
        # Initialize with tank data
        self._update_modbus_registers(context)
        
        return context
    
    def _update_modbus_registers(self, context):
        """Update Modbus registers with current tank data"""
        try:
            slave_id = 0x00  # Default slave ID
            
            for tank in self.tanks.values():
                # Get tank data as Modbus registers
                tank_registers = tank.get_modbus_data()
                
                # Write to holding registers
                for i, value in enumerate(tank_registers):
                    address = tank.base_address + i
                    if address < 100:  # Stay within our allocated range
                        context[slave_id].setValues(3, address, [value])  # 3 = holding registers
                        
        except Exception as e:
            self.logger.error(f"Error updating Modbus registers: {e}")
    
    def _update_tanks_continuously(self):
        """Background thread to continuously update tank levels"""
        while self.running:
            try:
                # Update tank data
                for tank in self.tanks.values():
                    tank.update_level()
                
                # Update Modbus registers
                self._update_modbus_registers(self.context)
                
                time.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in tank update thread: {e}")
                time.sleep(5)
    
    def start(self):
        """Start the Modbus simulator server"""
        try:
            print(f"🚀 Starting Modbus Tank Simulator")
            print(f"📡 Host: {self.host}:{self.port}")
            print(f"🏥 Server will provide data for {len(self.tanks)} tanks")
            print("\n📋 Modbus Register Mapping:")
            print("Tank Data Layout (per tank, 8 registers each):")
            print("  Reg +0-1: Level (32-bit float)")
            print("  Reg +2-3: Capacity (32-bit float)")
            print("  Reg +4:   Status (16-bit int: 0=NORMAL, 1=LOW, 2=HIGH)")
            print("  Reg +5:   Tank ID Hash (16-bit int)")
            print("  Reg +6-7: Timestamp (32-bit int)")
            print("\n📍 Tank Register Addresses:")
            for tank_id, tank in self.tanks.items():
                print(f"  - {tank_id}: Registers {tank.base_address}-{tank.base_address + 7}")
            print("\n⏹️  Press Ctrl+C to stop")
            
            # Setup device identification
            identity = ModbusDeviceIdentification()
            identity.VendorName = 'Tank Monitoring Simulator'
            identity.ProductCode = 'TMS'
            identity.VendorUrl = 'https://github.com/tank-monitoring'
            identity.ProductName = 'Tank Level Modbus Simulator'
            identity.ModelName = 'TMS-MODBUS-SIM'
            identity.MajorMinorRevision = '1.0'
            
            # Start background update thread
            self.running = True
            self.update_thread.start()
            
            # Start Modbus server
            self.logger.info(f"Starting Modbus TCP server on {self.host}:{self.port}")
            StartTcpServer(
                context=self.context,
                identity=identity,
                address=(self.host, self.port)
            )
            
        except KeyboardInterrupt:
            print("\n🛑 Stopping Modbus simulator...")
            self.running = False
        except Exception as e:
            self.logger.error(f"Error starting Modbus server: {e}")
            print(f"❌ Failed to start Modbus server: {e}")

def main():
    parser = argparse.ArgumentParser(description="Modbus Tank Data Simulator")
    parser.add_argument("--port", type=int, default=502,
                       help="Port to run Modbus server on (default: 502)")
    parser.add_argument("--host", type=str, default="0.0.0.0",
                       help="Host address to bind to (default: 0.0.0.0)")
    
    args = parser.parse_args()
    
    # Note: Port 502 requires root privileges on Linux
    if args.port == 502:
        print("⚠️  Note: Port 502 requires root privileges on Linux")
        print("   Consider using a higher port (e.g., 5020) for testing")
    
    simulator = ModbusSimulator(port=args.port, host=args.host)
    simulator.start()

if __name__ == "__main__":
    main()
