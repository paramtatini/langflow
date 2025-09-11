#!/usr/bin/env python3
"""
Test script for automatic Ariba agent fetching when PAB credentials are saved.
"""

import asyncio
import json
import httpx
from typing import Dict, Any

# Test PAB credentials (actual working credentials)
TEST_CREDENTIALS = {
    "service_urls": {
        "agent_api_url": "https://business-agent-foundation-srv-unified-agent.d44b0b9.kyma.ondemand.com/"
    },
    "saasregistryenabled": True,
    "uaa": {
        "tenantmode": "shared",
        "sburl": "https://internal-xsuaa.authentication.us10.hana.ondemand.com",
        "subaccountid": "3b2f51f0-1dee-413d-8f06-1022b07e2639",
        "credential-type": "binding-secret",
        "clientid": "sb-ef73847b-dd1c-46ab-ba7d-2ebd3e251fe0!b416210|business-agent-foundation!b271516",
        "xsappname": "ef73847b-dd1c-46ab-ba7d-2ebd3e251fe0!b416210|business-agent-foundation!b271516",
        "clientsecret": "d8375052-3c6d-4ffa-b9de-8daef9824a22$wYFN0tiJTQZRPob_9e_1EzALkdj2jmuyibZZQAgx9mk=",
        "serviceInstanceId": "ef73847b-dd1c-46ab-ba7d-2ebd3e251fe0",
        "url": "https://sourcing-rfp-builder-us10-dev.authentication.us10.hana.ondemand.com",
        "uaadomain": "authentication.us10.hana.ondemand.com",
        "verificationkey": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAq9KoWyMKVSoo+1gTU9hr\njWqKklagIxlf4Wc9Gd16Ua7JCMzMey+29V3IC/C/NDx8Gi1Gx3bBmbuNPtVFpmQc\n97TKllcI7l50AW/DTvRAPrUG99YYlZFx93v6QLHc9lJqy+5C/KpSrfU0DYmdhJ6o\nsrHPahh2EszgV/ZPasXCgGXZ7K1k7Xs4FcR3TCrdHIKF8uEekPpaD780Uvtf+fGM\nJ3GlyoQx8tnyBqc7dXVGfRqrPVowbt/SyTS24hCHByRmqEdO/Dhc69+P4yz5juRR\ngkzzu1JneBtbHd57qhNbEeZWyVC80H+VTXeVhPDdaVdwkiau0JOOByiL3WfNT8vv\nOwIDAQAB\n-----END PUBLIC KEY-----",
        "apiurl": "https://api.authentication.us10.hana.ondemand.com",
        "identityzone": "sourcing-rfp-builder-us10-dev",
        "identityzoneid": "3b2f51f0-1dee-413d-8f06-1022b07e2639",
        "tenantid": "3b2f51f0-1dee-413d-8f06-1022b07e2639",
        "zoneid": "3b2f51f0-1dee-413d-8f06-1022b07e2639"
    }
}

LANGFLOW_BASE_URL = "http://localhost:7860"

async def test_auto_agent_fetch():
    """Test the automatic agent fetching when saving PAB credentials."""
    
    async with httpx.AsyncClient() as client:
        try:
            print("🔐 Testing automatic Ariba agent fetching...")
            
            # Step 1: Save PAB credentials (should automatically fetch agents)
            print("\n1. Saving PAB credentials...")
            response = await client.post(
                f"{LANGFLOW_BASE_URL}/api/v1/sap/pab/credentials",
                json=TEST_CREDENTIALS,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Credentials saved: {result['message']}")
                
                # Check if agents were automatically fetched
                if "agents fetched successfully" in result['message']:
                    print("✅ Agents were automatically fetched!")
                else:
                    print("⚠️ Agents were not fetched automatically")
                    
            else:
                print(f"❌ Failed to save credentials: {response.status_code} - {response.text}")
                return
            
            # Step 2: Verify agents were stored in database
            print("\n2. Verifying agents were stored...")
            response = await client.get(
                f"{LANGFLOW_BASE_URL}/api/v1/sap/ariba_agents",
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                agents = response.json()
                print(f"✅ Found {len(agents)} agents in database")
                
                if agents:
                    print("\n📋 Agent details:")
                    for i, agent in enumerate(agents[:3]):  # Show first 3 agents
                        print(f"  {i+1}. {agent.get('name', 'Unknown')} - {agent.get('description', 'No description')}")
                    
                    if len(agents) > 3:
                        print(f"  ... and {len(agents) - 3} more agents")
                else:
                    print("⚠️ No agents found in database")
            else:
                print(f"❌ Failed to retrieve agents: {response.status_code} - {response.text}")
            
            # Step 3: Test credentials retrieval
            print("\n3. Verifying credentials were stored...")
            response = await client.get(
                f"{LANGFLOW_BASE_URL}/api/v1/sap/pab/credentials",
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                credentials = response.json()
                print("✅ Credentials successfully retrieved from database")
                print(f"   - Agent API URL: {credentials.get('agent_api_url', 'Not found')}")
                print(f"   - UAA URL: {credentials.get('uaa', {}).get('url', 'Not found')}")
            else:
                print(f"❌ Failed to retrieve credentials: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")

async def test_oauth_flow():
    """Test OAuth token retrieval separately."""
    print("\n🔑 Testing OAuth token flow...")
    
    try:
        # This would normally be done internally by the API
        from src.backend.base.langflow.api.v1.sap import get_oauth_token
        
        token = await get_oauth_token(TEST_CREDENTIALS)
        print(f"✅ OAuth token obtained: {token[:20]}...")
        
    except Exception as e:
        print(f"❌ OAuth test failed: {str(e)}")

async def main():
    """Run all tests."""
    print("🚀 Starting Ariba Agent Auto-Fetch Tests")
    print("=" * 50)
    
    # Note: These tests require valid PAB credentials
    print("⚠️ Note: Update TEST_CREDENTIALS with valid PAB credentials to run these tests")
    
    await test_auto_agent_fetch()
    await test_oauth_flow()
    
    print("\n" + "=" * 50)
    print("✅ Tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
