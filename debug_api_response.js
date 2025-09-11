// Debug script to test the API response directly
const axios = require('axios');

async function testAPIResponse() {
    try {
        console.log('Testing direct API call...');
        
        // First get access token
        const authResponse = await axios.get('http://localhost:7860/api/v1/auto_login');
        const accessToken = authResponse.data.access_token;
        console.log('Got access token:', accessToken.substring(0, 20) + '...');
        
        // Test the credentials endpoint
        const response = await axios.get('http://localhost:7860/api/v1/sap/pab/credentials', {
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Accept': 'application/json'
            }
        });
        
        console.log('Response status:', response.status);
        console.log('Response data:', response.data);
        
    } catch (error) {
        console.log('Error status:', error.response?.status);
        console.log('Error data:', error.response?.data);
        console.log('Error headers:', error.response?.headers);
        
        // Check if we're getting HTML instead of JSON
        if (typeof error.response?.data === 'string' && error.response.data.includes('<html>')) {
            console.log('ERROR: Received HTML instead of JSON!');
            console.log('First 200 chars:', error.response.data.substring(0, 200));
        }
    }
}

// Test via frontend proxy
async function testFrontendProxy() {
    try {
        console.log('\nTesting frontend proxy...');
        
        const response = await axios.get('http://localhost:3000/api/v1/sap/pab/credentials', {
            headers: {
                'Accept': 'application/json'
            }
        });
        
        console.log('Proxy response status:', response.status);
        console.log('Proxy response data:', response.data);
        
    } catch (error) {
        console.log('Proxy error status:', error.response?.status);
        console.log('Proxy error data:', error.response?.data);
        
        // Check if we're getting HTML instead of JSON
        if (typeof error.response?.data === 'string' && error.response.data.includes('<html>')) {
            console.log('ERROR: Frontend proxy returned HTML instead of JSON!');
            console.log('First 200 chars:', error.response.data.substring(0, 200));
        }
    }
}

testAPIResponse().then(() => testFrontendProxy());
