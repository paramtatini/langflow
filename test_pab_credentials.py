#!/usr/bin/env python3

import requests

# Test data based on the sample provided by the user
test_credentials = {
    "service_urls": {"agent_api_url": "https://business-agent-foundation-srv-unified-agent.d44b0b9.kyma.ondemand.com/"},
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
        "zoneid": "3b2f51f0-1dee-413d-8f06-1022b07e2639",
    },
}


def test_pab_credentials():
    url = "http://localhost:7860/api/v1/sap/pab/credentials"

    print("Testing PAB credentials endpoint...")
    print(f"URL: {url}")
    print(f"Payload keys: {list(test_credentials.keys())}")
    print(f"UAA keys: {list(test_credentials['uaa'].keys())}")
    print(f"Service URLs: {test_credentials['service_urls']}")
    print()

    try:
        response = requests.post(url, json=test_credentials, timeout=30)
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response body: {response.text}")

        if response.status_code == 200:
            data = response.json()
            print(f"Success! Found {len(data.get('agents', []))} agents")
        else:
            print(f"Error: {response.status_code}")

    except Exception as e:
        print(f"Request failed: {e!s}")


if __name__ == "__main__":
    test_pab_credentials()
