import json
import requests
import os
import sys
from pathlib import Path
from requests_toolbelt.multipart.encoder import MultipartEncoder

def test_document_upload():
    # Configuration
    base_url = "http://localhost:8031"
    test_file = "test_document.txt"
    
    # Create test file if it doesn't exist
    test_content = "This is a test document content for upload testing."
    if not os.path.exists(test_file):
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
    else:
        with open(test_file, 'r', encoding='utf-8') as f:
            if f.read() != test_content:
                with open(test_file, 'w', encoding='utf-8') as f_write:
                    f_write.write(test_content)
    
    print(f"Using test file: {os.path.abspath(test_file)}")
    print(f"File exists: {os.path.exists(test_file)}")
    print(f"File size: {os.path.getsize(test_file)} bytes")
    
    # Prepare the request with file
    print("\nSending document to parse endpoint...")
    try:
        # Read file content
        with open(test_file, 'rb') as f:
            file_content = f.read()
        
        # Prepare multipart form data
        m = MultipartEncoder(
            fields={
                'file': (os.path.basename(test_file), file_content, 'text/plain')
            }
        )
        
        # Send the request
        headers = {'Content-Type': m.content_type}
        response = requests.post(
            f"{base_url}/parse",
            data=m,
            headers=headers,
            timeout=30
        )
        
        # Print the response
        print(f"\nStatus Code: {response.status_code}")
        print("Response Headers:")
        for header, value in response.headers.items():
            print(f"  {header}: {value}")
            
        print("\nResponse Body:")
        try:
            print(json.dumps(response.json(), indent=2))
        except ValueError:
            print(response.text)
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting document upload test...")
    success = test_document_upload()
    print("\nTest completed successfully!" if success else "\nTest failed!")
