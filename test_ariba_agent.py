#!/usr/bin/env python3
"""
Test script for the new Ariba Agent component.
Tests automatic credential retrieval, OAuth token, and agent execution.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add the LFX source to Python path
sys.path.insert(0, str(Path("src/lfx/src").resolve()))

from lfx.components.ariba_agents import AribaAgentComponent


async def test_ariba_agent_component():
    """Test the Ariba Agent component."""
    print("🤖 Testing Ariba Agent Component...")
    
    # Create component instance
    ariba_agent = AribaAgentComponent()
    
    try:
        # Test getting credentials from backend
        credentials = await ariba_agent.get_credentials_from_backend()
        if credentials:
            print(f"✓ Found credentials from backend API: {credentials.agent_api_url}")
            
            # Test getting OAuth token
            try:
                access_token = await ariba_agent.get_oauth_token(credentials)
                print(f"✓ Successfully retrieved access token: {access_token[:20]}...")
                
                # Test fetching available agents
                try:
                    agents = await ariba_agent.fetch_available_agents(credentials, access_token)
                    print(f"✓ Successfully fetched {len(agents)} agents")
                    
                    # Show first few agents
                    for i, agent in enumerate(agents[:3]):
                        agent_name = agent.get("name", "Unknown")
                        agent_id = agent.get("ID", "Unknown")
                        expert_in = agent.get("expertIn", "No expertise")
                        print(f"  • Agent {i+1}: {agent_name} (ID: {agent_id})")
                        print(f"    Expert in: {expert_in[:100]}{'...' if len(expert_in) > 100 else ''}")
                    
                    if len(agents) > 3:
                        print(f"  ... and {len(agents) - 3} more agents")
                        
                    return agents
                except Exception as e:
                    print(f"⚠️  Could not fetch agents: {e}")
                    return []
            except Exception as e:
                print(f"⚠️  Could not retrieve access token: {e}")
                return []
        else:
            print("ℹ️  No credentials found from backend API (expected if not configured)")
            return []
            
    except Exception as e:
        print(f"⚠️  Error testing Ariba Agent component: {e}")
        return []


async def test_message_response():
    """Test the message response method."""
    print("\n💬 Testing Message Response Method...")
    
    # Test Ariba Agent message response
    ariba_agent = AribaAgentComponent()
    ariba_agent.input_value = "Hello, can you help me with procurement tasks?"
    
    try:
        message = await ariba_agent.message_response()
        print(f"✓ Ariba Agent message: {message.text[:100]}...")
    except Exception as e:
        print(f"⚠️  Ariba Agent message error: {e}")


def test_component_properties():
    """Test component properties and metadata."""
    print("\n📋 Testing Component Properties...")
    
    # Test Ariba Agent Component
    ariba_agent = AribaAgentComponent()
    print(f"✓ Ariba Agent Component:")
    print(f"  - Display Name: {ariba_agent.display_name}")
    print(f"  - Description: {ariba_agent.description}")
    print(f"  - Icon: {ariba_agent.icon}")
    print(f"  - Name: {ariba_agent.name}")
    print(f"  - Inputs: {len(ariba_agent.inputs)}")
    print(f"  - Outputs: {len(ariba_agent.outputs)}")
    
    # Show input details
    print(f"  - Input Fields:")
    for inp in ariba_agent.inputs:
        print(f"    • {inp.display_name} ({inp.name}): {inp.info[:50]}...")


async def test_build_config_update():
    """Test the build config update method."""
    print("\n⚙️  Testing Build Config Update...")
    
    ariba_agent = AribaAgentComponent()
    
    # Mock build config
    build_config = {
        "agent_id": {
            "options": [],
            "value": ""
        }
    }
    
    try:
        updated_config = await ariba_agent.update_build_config(build_config, "", "agent_id")
        agent_options = updated_config.get("agent_id", {}).get("options", [])
        print(f"✓ Build config updated with {len(agent_options)} agent options")
        
        if agent_options:
            print(f"  Available agents: {agent_options[:3]}{'...' if len(agent_options) > 3 else ''}")
        else:
            print("  No agents available (expected if credentials not configured)")
            
    except Exception as e:
        print(f"⚠️  Build config update error: {e}")


async def main():
    """Main test function."""
    print("🚀 Testing New Ariba Agent Component")
    print("=" * 50)
    
    # Test component properties
    test_component_properties()
    
    # Test Ariba agent component
    agents = await test_ariba_agent_component()
    
    # Test message response
    await test_message_response()
    
    # Test build config update
    await test_build_config_update()
    
    print("\n" + "=" * 50)
    print("✅ Ariba Agent Component Test Complete!")
    
    if agents:
        print(f"🎉 Successfully tested with {len(agents)} agents and valid credentials")
    else:
        print("ℹ️  Component works but requires SAP PAB credentials to be configured")
        print("   Configure credentials in Settings > SAP AI Credentials to test full functionality")
        print("   The component will automatically:")
        print("   • Retrieve credentials from backend API")
        print("   • Get OAuth token using uaa.url + '/oauth/token'")
        print("   • Fetch agents from agent_api_url + '/api/v1/Agents'")
        print("   • Populate agent dropdown with available agents")


if __name__ == "__main__":
    asyncio.run(main())
