#!/usr/bin/env python3
"""
Test script to check the /api/v1/all endpoint response
"""

import asyncio
import httpx
import json

async def test_api_response():
    """Test the /api/v1/all endpoint to see if ariba_agents are included."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("http://localhost:7860/api/v1/all")
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"Response status: {response.status_code}")
                print(f"Response keys: {list(data.keys())}")
                
                if "ariba_agents" in data:
                    print(f"✓ ariba_agents found with {len(data['ariba_agents'])} components")
                    print("Ariba agent component names:")
                    for name in data["ariba_agents"].keys():
                        print(f"  - {name}")
                else:
                    print("❌ ariba_agents not found in response")
                    
                # Check if there are any components at all
                total_components = sum(len(components) for components in data.values() if isinstance(components, dict))
                print(f"Total components in response: {total_components}")
                
            else:
                print(f"❌ API request failed with status: {response.status_code}")
                print(f"Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Error testing API: {e}")

if __name__ == "__main__":
    asyncio.run(test_api_response())
