#!/usr/bin/env python3
"""
Test script to debug dynamic Ariba agent loading
"""

import asyncio
import sys
import os

# Add the src paths to Python path
sys.path.insert(0, os.path.join(os.getcwd(), 'src', 'lfx', 'src'))

async def test_dynamic_loading():
    """Test the dynamic loading functionality step by step."""
    print("Testing dynamic Ariba agent loading...")
    
    try:
        # Test 1: Import the dynamic fetcher module
        print("\n1. Testing import of dynamic_agent_fetcher...")
        from lfx.components.ariba_agents.dynamic_agent_fetcher import (
            fetch_ariba_agents_from_backend,
            create_dynamic_agent_component
        )
        print("✓ Successfully imported dynamic_agent_fetcher")
        
        # Test 2: Fetch agents from backend
        print("\n2. Testing fetch_ariba_agents_from_backend...")
        agents = await fetch_ariba_agents_from_backend()
        print(f"✓ Successfully fetched {len(agents)} agents")
        
        if agents:
            print(f"First agent: {agents[0].get('name', 'Unknown')} (ID: {agents[0].get('ID', 'Unknown')})")
        
        # Test 3: Create a dynamic component
        if agents:
            print("\n3. Testing create_dynamic_agent_component...")
            first_agent = agents[0]
            component_class = create_dynamic_agent_component(first_agent)
            print(f"✓ Successfully created component class: {component_class.__name__}")
            
            # Test 4: Instantiate the component
            print("\n4. Testing component instantiation...")
            component_instance = component_class()
            print(f"✓ Successfully instantiated component: {component_instance.display_name}")
            
            # Test 5: Test create_component_template
            print("\n5. Testing create_component_template...")
            from lfx.custom.utils import create_component_template
            
            component_template, _ = create_component_template(
                component_extractor=component_instance,
                module_name=f"lfx.components.ariba_agents.dynamic_agent_fetcher.{component_class.__name__}"
            )
            print(f"✓ Successfully created component template")
            print(f"Template keys: {list(component_template.keys())}")
        
        # Test 6: Test the full _load_dynamic_ariba_agents function
        print("\n6. Testing _load_dynamic_ariba_agents function...")
        from lfx.interface.components import _load_dynamic_ariba_agents
        
        dynamic_components = await _load_dynamic_ariba_agents()
        print(f"✓ Successfully loaded {len(dynamic_components)} dynamic components")
        
        if dynamic_components:
            print("Dynamic component names:")
            for name in dynamic_components.keys():
                print(f"  - {name}")
        
        print("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_dynamic_loading())
    sys.exit(0 if success else 1)
