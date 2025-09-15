#!/usr/bin/env python3
"""
Test script for virtual Ariba agents implementation.

This script tests:
1. Backend API endpoint for fetching Ariba agents
2. Dynamic component creation
3. Virtual list functionality
"""

import asyncio
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'lfx', 'src'))

async def test_backend_api():
    """Test the backend API endpoint for fetching Ariba agents."""
    print("Testing backend API endpoint...")
    
    try:
        import httpx
        
        async with httpx.AsyncClient() as client:
            # Test the ariba_agents endpoint
            response = await client.get("http://localhost:7860/api/v1/sap/ariba_agents")
            
            if response.status_code == 200:
                agents = response.json()
                print(f"✅ Successfully fetched {len(agents)} agents from backend API")
                
                # Print first few agents for verification
                for i, agent in enumerate(agents[:3]):
                    print(f"  Agent {i+1}: {agent.get('name', 'Unknown')} (ID: {agent.get('ID', 'N/A')})")
                
                return agents
            else:
                print(f"❌ Backend API returned status {response.status_code}")
                return []
                
    except Exception as e:
        print(f"❌ Error testing backend API: {e}")
        return []


async def test_dynamic_component_creation():
    """Test dynamic component creation."""
    print("\nTesting dynamic component creation...")
    
    try:
        from lfx.components.ariba_agents.dynamic_agent_fetcher import (
            fetch_ariba_agents_from_backend,
            create_dynamic_agent_component,
            get_dynamic_agent_components
        )
        
        # Test fetching agents
        agents = await fetch_ariba_agents_from_backend()
        print(f"✅ Fetched {len(agents)} agents for component creation")
        
        if agents:
            # Test creating a component for the first agent
            first_agent = agents[0]
            component_class = create_dynamic_agent_component(first_agent)
            
            print(f"✅ Created component class: {component_class.__name__}")
            print(f"   Display name: {component_class.display_name}")
            print(f"   Description: {component_class.description}")
            
            # Test getting all dynamic components
            all_components = await get_dynamic_agent_components()
            print(f"✅ Created {len(all_components)} dynamic components total")
            
            return all_components
        else:
            print("❌ No agents available for component creation")
            return {}
            
    except Exception as e:
        print(f"❌ Error testing dynamic component creation: {e}")
        return {}


async def test_ariba_agents_module():
    """Test the ariba_agents module with dynamic imports."""
    print("\nTesting ariba_agents module...")
    
    try:
        from lfx.components import ariba_agents
        
        # Test static component
        static_component = ariba_agents.AribaAgentComponent
        print(f"✅ Static component loaded: {static_component.__name__}")
        
        # Test dynamic component loading
        try:
            # This should trigger dynamic loading
            all_attrs = dir(ariba_agents)
            dynamic_components = [attr for attr in all_attrs if attr.startswith("AribaAgent_")]
            
            print(f"✅ Found {len(dynamic_components)} dynamic components in module")
            
            # Try to access a dynamic component if available
            if dynamic_components:
                first_dynamic = dynamic_components[0]
                component_class = getattr(ariba_agents, first_dynamic)
                print(f"✅ Successfully accessed dynamic component: {component_class.__name__}")
                
        except Exception as e:
            print(f"⚠️  Dynamic component access failed (this may be expected in some environments): {e}")
            
    except Exception as e:
        print(f"❌ Error testing ariba_agents module: {e}")


async def test_component_instantiation():
    """Test instantiating a dynamic component."""
    print("\nTesting component instantiation...")
    
    try:
        from lfx.components.ariba_agents.dynamic_agent_fetcher import get_dynamic_agent_components
        
        components = await get_dynamic_agent_components()
        
        if components:
            # Try to instantiate the first component
            first_component_name = list(components.keys())[0]
            first_component_class = components[first_component_name]
            
            # Create an instance
            instance = first_component_class()
            
            print(f"✅ Successfully instantiated component: {first_component_name}")
            print(f"   Agent ID: {instance.agent_id}")
            print(f"   Agent Name: {instance.agent_name}")
            print(f"   Inputs: {len(instance.inputs)}")
            print(f"   Outputs: {len(instance.outputs)}")
            
        else:
            print("❌ No components available for instantiation")
            
    except Exception as e:
        print(f"❌ Error testing component instantiation: {e}")


async def main():
    """Run all tests."""
    print("🧪 Testing Virtual Ariba Agents Implementation")
    print("=" * 50)
    
    # Test 1: Backend API
    agents = await test_backend_api()
    
    # Test 2: Dynamic component creation
    components = await test_dynamic_component_creation()
    
    # Test 3: Module integration
    await test_ariba_agents_module()
    
    # Test 4: Component instantiation
    await test_component_instantiation()
    
    print("\n" + "=" * 50)
    print("🏁 Test Summary:")
    print(f"   - Agents fetched from API: {len(agents)}")
    print(f"   - Dynamic components created: {len(components)}")
    
    if agents and components:
        print("✅ Virtual Ariba agents implementation appears to be working!")
    else:
        print("❌ Some issues detected. Check the logs above.")


if __name__ == "__main__":
    asyncio.run(main())
