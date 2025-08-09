import os
import logging
from typing import Dict, Any, Optional
from unstructured_client import UnstructuredClient
from unstructured_client.models import shared
from unstructured_client.models.errors import SDKError

class DocumentParser:
    def __init__(self):
        server_url = os.getenv("UNSTRUCTURED_API_URL", "http://unstructured_api:8000")
        api_key = os.getenv("UNSTRUCTURED_API_KEY", "")
        self.client = UnstructuredClient(server_url=server_url, api_key_auth=api_key)
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"DocumentParser initialized for local Unstructured API at: {server_url}")

    async def parse_document(self, file_path: str, strategy: str = "auto") -> Optional[Dict[str, Any]]:
        self.logger.info(f"Parsing document: {file_path} with strategy: {strategy}")
        try:
            with open(file_path, "rb") as f:
                files = shared.Files(content=f.read(), file_name=os.path.basename(file_path))
            
            req = shared.PartitionParameters(files=files, strategy=strategy)
            res = self.client.general.partition(req)
            
            if res.elements:
                # Convert elements to a serializable format
                elements = []
                for element in res.elements:
                    if hasattr(element, 'to_dict') and callable(element.to_dict):
                        elements.append(element.to_dict())
                    elif hasattr(element, '__dict__'):
                        elements.append(element.__dict__)
                    else:
                        elements.append(str(element))
                return {"elements": elements}
                
            return None
            
        except SDKError as e:
            self.logger.error(f"SDKError parsing {file_path}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error parsing {file_path}: {str(e)}")
            return None
