#!/usr/bin/env python3
"""
Test Script for All Protocol Simulators

This script tests all the protocol simulators to ensure they work correctly.
"""

import asyncio
import json
import requests
import subprocess
import time
import threading
from datetime import datetime

def test_rest_simulator():
    """Test REST API simulator"""
    print("🧪 Testing REST Simulator...")
    
    try:
        # First, get an auth token from the backend
        login_response = requests.post(
            "http://localhost:8000/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            
            # Test sending tank data
            cmd = [
                "python3", "rest_simulator.py",
                "--url", "http://localhost:8000/api/tank-levels",
                "--tank-id", "test_tank_rest",
                "--level", "75.5",
                "--token", token
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd="simulators")
            
            if result.returncode == 0:
                print("✅ REST Simulator: PASSED")
                return True
            else:
                print(f"❌ REST Simulator: FAILED - {result.stderr}")
                return False
        else:
            print("❌ REST Simulator: FAILED - Could not get auth token")
            return False
            
    except Exception as e:
        print(f"❌ REST Simulator: FAILED - {e}")
        return False

def test_mqtt_simulator():
    """Test MQTT simulator"""
    print("🧪 Testing MQTT Simulator...")
    
    try:
        # Test MQTT simulator (assumes local broker is running)
        cmd = [
            "python3", "mqtt_simulator.py",
            "--broker", "localhost",
            "--topic-prefix", "tanks",
            "--tank-id", "test_tank_mqtt",
            "--level", "65.3"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd="simulators", timeout=10)
        
        if result.returncode == 0:
            print("✅ MQTT Simulator: PASSED")
            return True
        else:
            print(f"❌ MQTT Simulator: FAILED - {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  MQTT Simulator: TIMEOUT (broker might not be running)")
        return False
    except Exception as e:
        print(f"❌ MQTT Simulator: FAILED - {e}")
        return False

def test_graphql_simulator():
    """Test GraphQL simulator"""
    print("🧪 Testing GraphQL Simulator...")
    
    # Start GraphQL simulator in background
    simulator_process = None
    try:
        simulator_process = subprocess.Popen(
            ["python3", "graphql_simulator.py", "--port", "4001"],
            cwd="simulators",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        time.sleep(3)
        
        # Test GraphQL query
        query = {"query": "{ tanks { id name level status } }"}
        response = requests.post(
            "http://localhost:4001/graphql",
            json=query,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "tanks" in data["data"]:
                print("✅ GraphQL Simulator: PASSED")
                return True
            else:
                print(f"❌ GraphQL Simulator: FAILED - Invalid response: {data}")
                return False
        else:
            print(f"❌ GraphQL Simulator: FAILED - HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ GraphQL Simulator: FAILED - {e}")
        return False
    finally:
        if simulator_process:
            simulator_process.terminate()
            simulator_process.wait()

def test_opcua_simulator():
    """Test OPC UA simulator"""
    print("🧪 Testing OPC UA Simulator...")
    
    try:
        # Check if asyncua is available for testing
        from asyncua import Client
        
        async def test_opcua_client():
            simulator_process = None
            try:
                # Start OPC UA simulator in background
                simulator_process = subprocess.Popen(
                    ["python3", "opcua_simulator.py", "--port", "4841"],
                    cwd="simulators",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Wait for server to start
                await asyncio.sleep(5)
                
                # Connect to OPC UA server
                client = Client("opc.tcp://localhost:4841/freeopcua/server/")
                await client.connect()
                
                # Browse for tank nodes
                root = client.get_root_node()
                objects = await root.get_child("0:Objects")
                tanks = await objects.get_child("1:Tanks")
                
                # Get tank children
                tank_nodes = await tanks.get_children()
                
                if len(tank_nodes) > 0:
                    # Read level from first tank
                    first_tank = tank_nodes[0]
                    level_node = await first_tank.get_child("1:Level")
                    level_value = await level_node.read_value()
                    
                    if isinstance(level_value, (int, float)):
                        print("✅ OPC UA Simulator: PASSED")
                        return True
                    else:
                        print(f"❌ OPC UA Simulator: FAILED - Invalid level value: {level_value}")
                        return False
                else:
                    print("❌ OPC UA Simulator: FAILED - No tank nodes found")
                    return False
                    
            except Exception as e:
                print(f"❌ OPC UA Simulator: FAILED - {e}")
                return False
            finally:
                try:
                    await client.disconnect()
                except:
                    pass
                if simulator_process:
                    simulator_process.terminate()
                    simulator_process.wait()
        
        # Run async test
        return asyncio.run(test_opcua_client())
        
    except ImportError:
        print("⚠️  OPC UA Simulator: SKIPPED (asyncua not available)")
        return None
    except Exception as e:
        print(f"❌ OPC UA Simulator: FAILED - {e}")
        return False

def test_modbus_simulator():
    """Test Modbus simulator"""
    print("🧪 Testing Modbus Simulator...")
    
    try:
        # Check if pymodbus is available for testing
        from pymodbus.client.sync import ModbusTcpClient
        
        simulator_process = None
        try:
            # Start Modbus simulator in background
            simulator_process = subprocess.Popen(
                ["python3", "modbus_simulator.py", "--port", "5020"],
                cwd="simulators",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for server to start
            time.sleep(3)
            
            # Connect to Modbus server
            client = ModbusTcpClient('localhost', port=5020)
            connection = client.connect()
            
            if connection:
                # Read holding registers for first tank (registers 0-7)
                result = client.read_holding_registers(0, 8)
                
                if not result.isError():
                    registers = result.registers
                    if len(registers) >= 8:
                        print("✅ Modbus Simulator: PASSED")
                        return True
                    else:
                        print(f"❌ Modbus Simulator: FAILED - Not enough registers: {len(registers)}")
                        return False
                else:
                    print(f"❌ Modbus Simulator: FAILED - Read error: {result}")
                    return False
            else:
                print("❌ Modbus Simulator: FAILED - Could not connect")
                return False
                
        except Exception as e:
            print(f"❌ Modbus Simulator: FAILED - {e}")
            return False
        finally:
            try:
                client.close()
            except:
                pass
            if simulator_process:
                simulator_process.terminate()
                simulator_process.wait()
                
    except ImportError:
        print("⚠️  Modbus Simulator: SKIPPED (pymodbus not available)")
        return None
    except Exception as e:
        print(f"❌ Modbus Simulator: FAILED - {e}")
        return False

def main():
    """Run all simulator tests"""
    print("🚀 Starting Protocol Simulator Tests")
    print("=" * 50)
    
    results = {}
    
    # Test each simulator
    results['REST'] = test_rest_simulator()
    results['MQTT'] = test_mqtt_simulator()
    results['GraphQL'] = test_graphql_simulator()
    results['OPC UA'] = test_opcua_simulator()
    results['Modbus'] = test_modbus_simulator()
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    failed = 0
    skipped = 0
    
    for protocol, result in results.items():
        if result is True:
            print(f"✅ {protocol}: PASSED")
            passed += 1
        elif result is False:
            print(f"❌ {protocol}: FAILED")
            failed += 1
        else:
            print(f"⚠️  {protocol}: SKIPPED")
            skipped += 1
    
    print(f"\n📈 Summary: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed == 0:
        print("🎉 All available simulators are working correctly!")
        return 0
    else:
        print("⚠️  Some simulators failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit(main())
