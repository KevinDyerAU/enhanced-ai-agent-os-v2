import httpx
import logging
from typing import Dict, Any, Optional
import aiofiles

logger = logging.getLogger(__name__)

class DocumentProcessingClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        
    async def process_document(self, file_path: str, filename: str) -> Optional[Dict[str, Any]]:
        """Process a document using the Document Processing Engine"""
        try:
            async with aiofiles.open(file_path, 'rb') as file:
                file_content = await file.read()
                
            files = {"file": (filename, file_content, "application/octet-stream")}
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/parse",
                    files=files
                )
                
                if response.status_code == 200:
                    parsed_data = response.json()
                    return self._extract_training_content(parsed_data)
                else:
                    logger.error(f"Failed to process document {filename}: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error processing document {filename}: {e}")
            return None
    
    def _extract_training_content(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract training-specific content from parsed document"""
        elements = parsed_data.get("elements", [])
        
        text_content = ""
        sections = {}
        page_numbers_set = set()
        
        for element in elements:
            element_dict = element if isinstance(element, dict) else element
            text = element_dict.get("text", "")
            element_type = element_dict.get("type", "")
            
            text_content += text + "\n"
            # capture page number if available
            page_no = element_dict.get("metadata", {}).get("page_number")
            if page_no is not None:
                page_numbers_set.add(page_no)
            
            if element_type == "Title" or "assessment" in text.lower():
                sections[text.strip()] = []
        
        return {
            "text_content": text_content.strip(),
            "sections": sections,
            "elements": elements,
            "metadata": {
                "total_elements": len(elements),
                "processing_timestamp": parsed_data.get("timestamp"),
                "page_numbers": sorted(list(page_numbers_set)),
                "total_pages": len(page_numbers_set)
            }
        }
