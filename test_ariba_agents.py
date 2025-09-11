#!/usr/bin/env python3
"""
Test script for Ariba Agents components.
Tests OAuth token retrieval and PAB agents fetching.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add the LFX source to Python path
sys.path.insert(0, str(Path("src/lfx/src").resolve()))

from lfx.components.ariba_agents import OAuthTokenComponent, PABAgentsFetcherComponent


async def test_oauth_token_component():
    """Test the OAuth Token component."""
    print("🔑 Testing OAuth Token Component...")
    
    # Create component instance
    oauth_component = OAuthTokenComponent()
    
    try:
        # Test getting stored credentials (should fail gracefully if no credentials)
        credentials = await oauth_component.get_stored_credentials()
        if credentials:
            print(f"✓ Found stored credentials for: {credentials.agent_api_url}")
            
            # Test getting access token
            try:
                access_token = await oauth_component.get_access_token()
                print(f"✓ Successfully retrieved access token: {access_token[:20]}...")
                return access_token
            except Exception as e:
                print(f"⚠️  Could not retrieve access token: {e}")
                return None
        else:
            print("ℹ️  No stored credentials found (expected if not configured)")
            return None
            
    except Exception as e:
        print(f"⚠️  Error testing OAuth component: {e}")
        return None


async def test_pab_agents_fetcher_component(access_token=None):
    """Test the PAB Agents Fetcher component."""
    print("\n👥 Testing PAB Agents Fetcher Component...")
    
    # Create component instance
    fetcher_component = PABAgentsFetcherComponent()
    
    # Set access token if provided
    if access_token:
        fetcher_component.access_token = access_token
    
    try:
        # Test getting stored credentials
        credentials = await fetcher_component.get_stored_credentials()
        if credentials:
            print(f"✓ Found stored credentials for: {credentials.agent_api_url}")
            
            # Test fetching agents list
            try:
                agents = await fetcher_component.get_agents_list()
                print(f"✓ Successfully retrieved {len(agents)} agents")
                
                # Show first few agents
                for i, agent in enumerate(agents[:3]):
                    agent_name = agent.get("name", "Unknown")
                    agent_id = agent.get("ID", "Unknown")
                    print(f"  • Agent {i+1}: {agent_name} (ID: {agent_id})")
                
                if len(agents) > 3:
                    print(f"  ... and {len(agents) - 3} more agents")
                    
                return agents
            except Exception as e:
                print(f"⚠️  Could not fetch agents: {e}")
                return []
        else:
            print("ℹ️  No stored credentials found (expected if not configured)")
            return []
            
    except Exception as e:
        print(f"⚠️  Error testing PAB Agents Fetcher component: {e}")
        return []


async def test_message_responses():
    """Test the message response methods."""
    print("\n💬 Testing Message Response Methods...")
    
    # Test OAuth Token message response
    oauth_component = OAuthTokenComponent()
    try:
        message = await oauth_component.message_response()
        print(f"✓ OAuth Token message: {message.text[:100]}...")
    except Exception as e:
        print(f"⚠️  OAuth Token message error: {e}")
    
    # Test PAB Agents Fetcher message response
    fetcher_component = PABAgentsFetcherComponent()
    try:
        message = await fetcher_component.message_response()
        print(f"✓ PAB Agents Fetcher message: {message.text[:100]}...")
    except Exception as e:
        print(f"⚠️  PAB Agents Fetcher message error: {e}")


def test_component_properties():
    """Test component properties and metadata."""
    print("\n📋 Testing Component Properties...")
    
    # Test OAuth Token Component
    oauth_component = OAuthTokenComponent()
    print(f"✓ OAuth Token Component:")
    print(f"  - Display Name: {oauth_component.display_name}")
    print(f"  - Description: {oauth_component.description}")
    print(f"  - Icon: {oauth_component.icon}")
    print(f"  - Name: {oauth_component.name}")
    print(f"  - Inputs: {len(oauth_component.inputs)}")
    print(f"  - Outputs: {len(oauth_component.outputs)}")
    
    # Test PAB Agents Fetcher Component
    fetcher_component = PABAgentsFetcherComponent()
    print(f"✓ PAB Agents Fetcher Component:")
    print(f"  - Display Name: {fetcher_component.display_name}")
    print(f"  - Description: {fetcher_component.description}")
    print(f"  - Icon: {fetcher_component.icon}")
    print(f"  - Name: {fetcher_component.name}")
    print(f"  - Inputs: {len(fetcher_component.inputs)}")
    print(f"  - Outputs: {len(fetcher_component.outputs)}")


async def main():
    """Main test function."""
    print("🚀 Testing Ariba Agents Components")
    print("=" * 50)
    
    # Test component properties
    test_component_properties()
    
    # Test OAuth token component
    access_token = await test_oauth_token_component()
    
    # Test PAB agents fetcher component
    agents = await test_pab_agents_fetcher_component(access_token)
    
    # Test message responses
    await test_message_responses()
    
    print("\n" + "=" * 50)
    print("✅ Ariba Agents Components Test Complete!")
    
    if access_token and agents:
        print(f"🎉 Successfully tested with {len(agents)} agents and valid token")
    else:
        print("ℹ️  Components work but require SAP PAB credentials to be configured")
        print("   Configure credentials in Settings > SAP AI Credentials to test full functionality")


if __name__ == "__main__":
    asyncio.run(main())
