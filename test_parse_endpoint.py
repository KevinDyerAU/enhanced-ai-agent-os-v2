import http.client
import json
import os

def test_parse_endpoint():
    print("Testing /parse endpoint with raw HTTP request...")
    
    # Prepare test file
    test_file = "test_document.txt"
    test_content = b"This is a test document content for upload testing."
    
    # Write test file if it doesn't exist or has different content
    if not os.path.exists(test_file) or open(test_file, 'rb').read() != test_content:
        with open(test_file, 'wb') as f:
            f.write(test_content)
    
    # Read file content
    with open(test_file, 'rb') as f:
        file_content = f.read()
    
    # Prepare the multipart form data
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="{test_file}"\r\n'
        'Content-Type: text/plain\r\n\r\n'
        f'{file_content.decode()}\r\n'
        f'--{boundary}--\r\n'
    )
    
    # Set up the connection
    conn = http.client.HTTPConnection("localhost", 8031)
    headers = {
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'Accept': 'application/json'
    }
    
    try:
        # Send the request
        print("Sending request to /parse endpoint...")
        conn.request("POST", "/parse", body=body, headers=headers)
        
        # Get the response
        response = conn.getresponse()
        
        # Print response details
        print(f"Status: {response.status} {response.reason}")
        print("Headers:")
        for header, value in response.getheaders():
            print(f"  {header}: {value}")
        
        # Read and print response body
        response_body = response.read().decode()
        print("\nResponse Body:")
        try:
            print(json.dumps(json.loads(response_body), indent=2))
        except json.JSONDecodeError:
            print(response_body)
        
        return response.status == 200
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = test_parse_endpoint()
    print("\nTest completed successfully!" if success else "\nTest failed!")
