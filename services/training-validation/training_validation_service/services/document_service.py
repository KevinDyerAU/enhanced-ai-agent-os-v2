import os
import tempfile
import nltk
from fastapi import UploadFile
from unstructured.partition.auto import partition
from typing import List
from schemas.document_schema import ProcessedElement

def check_for_nltk_package(package_name: str, package_category: str) -> bool:
    """Checks to see if the specified NLTK package exists on the image."""
    paths: list[str] = []
    for path in nltk.data.path:
        if not path.endswith("nltk_data"):
            path = os.path.join(path, "nltk_data")
        paths.append(path)

    try:
        nltk.find(f"{package_category}/{package_name}", paths=paths)
        return True
    except (LookupError, OSError):
        return False

def download_nltk_packages():
    """If required NLTK packages are not available, download them."""
    tagger_available = check_for_nltk_package(
        package_category="taggers",
        package_name="averaged_perceptron_tagger_eng",
    )
    tokenizer_available = check_for_nltk_package(
        package_category="tokenizers", package_name="punkt_tab"
    )

    if (not tokenizer_available) or (not tagger_available):
        nltk.download("averaged_perceptron_tagger_eng", quiet=True)
        nltk.download("punkt_tab", quiet=True)

if os.getenv("AUTO_DOWNLOAD_NLTK", "True").lower() == "true":
    download_nltk_packages()

class DocumentService:
    """
    A service to handle document processing tasks, primarily using the 'unstructured' library.
    """
    async def process_document(self, file: UploadFile) -> List[ProcessedElement]:
        """
        Processes an uploaded file to extract structured content.

        Args:
            file: The file uploaded via a FastAPI endpoint.

        Returns:
            A list of ProcessedElement schemas representing the document's content.
        """
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                tmp_file_path = tmp_file.name

            os.environ["UNSTRUCTURED_API_KEY"] = ""
            os.environ["UNSTRUCTURED_API_URL"] = ""
            os.environ["AUTO_DOWNLOAD_NLTK"] = "True"
            
            download_nltk_packages()
            
            elements = partition(
                filename=tmp_file_path,
                strategy="fast"
            )

            processed_elements = [
                ProcessedElement(
                    type=element.category,
                    text=element.text,
                    metadata=element.metadata.to_dict()
                )
                for element in elements
            ]
            
            return processed_elements

        finally:
            if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
            await file.seek(0)

document_service = DocumentService()
