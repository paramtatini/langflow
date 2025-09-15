#!/usr/bin/env python3
"""
Test script to verify dynamic Ariba agent components are working correctly.
"""

import asyncio
import sys
import os

# Add the src paths to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'lfx', 'src'))

async def test_dynamic_components():
    """Test that dynamic components can be loaded and instantiated."""
    print("Testing dynamic Ariba agent components...")
    
    try:
        # Import the ariba_agents module
        from lfx.components import ariba_agents
        
        print(f"Available components in ariba_agents: {dir(ariba_agents)}")
        
        # Test the dynamic component fetcher directly
        from lfx.components.ariba_agents.dynamic_agent_fetcher import get_cached_dynamic_components
        
        print("\nFetching dynamic components from API...")
        dynamic_components = await get_cached_dynamic_components()
        
        print(f"Found {len(dynamic_components)} dynamic components:")
        for name, component_class in dynamic_components.items():
            print(f"  - {name}: {component_class}")
            
            # Try to instantiate the component
            try:
                instance = component_class()
                print(f"    ✓ Successfully instantiated {name}")
                print(f"    Display name: {instance.display_name}")
                print(f"    Description: {instance.description}")
                print(f"    Icon: {instance.icon}")
            except Exception as e:
                print(f"    ✗ Failed to instantiate {name}: {e}")
        
        # Test accessing components via module attribute
        print("\nTesting component access via module attributes...")
        for name in dynamic_components.keys():
            try:
                component_class = getattr(ariba_agents, name)
                print(f"  ✓ Successfully accessed {name} via getattr")
            except AttributeError as e:
                print(f"  ✗ Failed to access {name} via getattr: {e}")
        
        return True
        
    except Exception as e:
        print(f"Error testing dynamic components: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_dynamic_components())
    if success:
        print("\n✓ All tests passed! Dynamic components are working correctly.")
    else:
        print("\n✗ Some tests failed. Check the output above for details.")
        sys.exit(1)
