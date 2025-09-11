#!/usr/bin/env python3
"""Test script to verify PAB credentials save and retrieve flow"""

import json

import requests

# Test credentials in SAP service key format
test_credentials = {
    "service_urls": {"agent_api_url": "https://test-agent-api.example.com"},
    "uaa": {"clientid": "test-client-id", "clientsecret": "test-client-secret", "url": "https://test-auth.example.com"},
}


def test_save_credentials():
    """Test saving PAB credentials"""
    print("Testing PAB credentials save...")

    url = "http://localhost:7860/api/v1/sap/pab/credentials"
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=test_credentials, headers=headers)
        print(f"Save response status: {response.status_code}")
        print(f"Save response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error saving credentials: {e}")
        return False


def test_get_credentials():
    """Test retrieving PAB credentials"""
    print("\nTesting PAB credentials retrieval...")

    url = "http://localhost:7860/api/v1/sap/pab/credentials"
    headers = {"Accept": "application/json"}

    try:
        response = requests.get(url, headers=headers)
        print(f"Get response status: {response.status_code}")
        print(f"Get response: {response.text}")

        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Parsed JSON: {json.dumps(data, indent=2)}")
                return True
            except json.JSONDecodeError:
                print("Response is not valid JSON")
                return False
        else:
            print(f"Non-200 status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error getting credentials: {e}")
        return False


if __name__ == "__main__":
    print("=== PAB Credentials Flow Test ===")

    # First test retrieval (should return 404)
    print("1. Testing retrieval before saving (should be 404):")
    test_get_credentials()

    # Test saving credentials (will fail due to invalid URLs, but should show the flow)
    print("\n2. Testing save (will fail due to invalid test URLs):")
    save_success = test_save_credentials()

    # Test retrieval after save attempt
    print("\n3. Testing retrieval after save attempt:")
    test_get_credentials()

    print("\n=== Test Complete ===")
