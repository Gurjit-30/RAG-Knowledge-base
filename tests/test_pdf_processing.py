import os
import io
import shutil
import pytest
from fastapi.testclient import TestClient
from fastapi import UploadFile

# Import our app and the services we want to test
from app.main import app
from app.services.pdf_extractor import extract_text_from_uploaded_pdf
from services.text_chunker import chunk_text

# Set up the FastAPI test client
# This allows us to make requests to our API without actually starting a live server
client = TestClient(app)

# --- Helper Functions ---

def get_sample_pdf_path():
    """
    Gets the path to a sample PDF for our tests.
    If it doesn't exist, we create a very basic text file disguised as a PDF
    so the upload endpoint doesn't complain, though the parsing test might need a real PDF.
    """
    # We want to keep our test files in a neat 'data' folder next to this test script
    test_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(test_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    pdf_path = os.path.join(data_dir, "dummy_test_file.pdf")
    
    # Only create it if it's missing
    if not os.path.exists(pdf_path):
        with open(pdf_path, "wb") as f:
            # This isn't a valid PDF structure, but it passes the extension check
            # For a true parsing test, you should replace this with a real PDF file!
            f.write(b"%PDF-1.4\n%Dummy PDF for testing\n")
            
    return pdf_path


# --- The Tests ---

def test_api_can_upload_pdf():
    """
    Test 1: Verification that our /upload endpoint works correctly.
    We'll pretend to be a user uploading a file.
    """
    sample_pdf_path = get_sample_pdf_path()
    
    # Open the file and send it to our FastAPI app
    with open(sample_pdf_path, "rb") as file_data:
        # The key "file" must match what the endpoint expects in UploadFile=File(...)
        files = {"file": ("uploaded_test_file.pdf", file_data, "application/pdf")}
        response = client.post("/upload", files=files)
        
    # Did the server accept it?
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
    
    response_data = response.json()
    assert response_data["message"] == "File uploaded successfully"
    assert response_data["filename"] == "uploaded_test_file.pdf"
    
    # Make sure it actually landed on the hard drive where we expected
    saved_file_path = response_data["path"]
    assert os.path.exists(saved_file_path), "The file wasn't saved to disk!"
    
    # Clean up so we don't clutter the raw directory after testing
    os.remove(saved_file_path)


@pytest.mark.asyncio
async def test_extractor_can_parse_pdf(mocker):
    """
    Test 2: Verification that our parsing logic works.
    Because our dummy PDF isn't a real PDF, pdfplumber would normally crash.
    Here, we'll use a 'mock' to fake pdfplumber's behavior, which lets us 
    test our logic in isolation without needing a real PDF file.
    """
    # 1. We mock the UploadFile that FastAPI usually provides
    mock_file_content = b"fake pdf bytes"
    mock_upload_file = UploadFile(filename="fake.pdf", file=io.BytesIO(mock_file_content))
    
    # 2. We mock pdfplumber so it pretends to extract text successfully
    # We simulate a PDF with 2 pages
    mock_page_1 = mocker.MagicMock()
    mock_page_1.extract_text.return_value = "This is the first page of text."
    
    mock_page_2 = mocker.MagicMock()
    mock_page_2.extract_text.return_value = "And here is the second page."
    
    mock_pdf_doc = mocker.MagicMock()
    mock_pdf_doc.pages = [mock_page_1, mock_page_2]
    
    # Patch pdfplumber.open to return our fake document
    mocker.patch("app.services.pdf_extractor.pdfplumber.open", return_value=mock_pdf_doc)
    
    # We also need to mock the context manager behavior (__enter__ and __exit__)
    mock_pdf_doc.__enter__.return_value = mock_pdf_doc
    
    # 3. Actually run our function
    extracted_text = await extract_text_from_uploaded_pdf(mock_upload_file)
    
    # 4. Check the results! Did it combine the pages with a newline?
    assert "This is the first page of text." in extracted_text
    assert "And here is the second page." in extracted_text
    assert extracted_text == "This is the first page of text.\n\nAnd here is the second page."


def test_chunker_splits_cleanly():
    """
    Test 3: Verification that the text chunker breaks down text properly.
    We don't need any mocks here because the chunker is pure Python logic.
    """
    # Let's create a decently long string that represents an extracted PDF
    paragraph_1 = "RAG stands for Retrieval-Augmented Generation. " * 10
    paragraph_2 = "It is very useful for chatting with your documents. " * 10
    
    # We join them with double newlines, mimicking our pdf_extractor's output
    full_document_text = f"{paragraph_1}\n\n{paragraph_2}"
    
    # Let's set a small chunk size so we can easily test the breaks
    # We want chunks of max 150 characters, with 20 characters of overlap
    test_chunk_size = 150
    test_overlap = 20
    
    resulting_chunks = chunk_text(full_document_text, chunk_size=test_chunk_size, overlap=test_overlap)
    
    # Did we get multiple pieces back?
    assert len(resulting_chunks) > 1, "The text wasn't chunked into pieces!"
    
    # Verify that no chunk exceeded our max size limit
    for i, chunk in enumerate(resulting_chunks):
        assert len(chunk) <= test_chunk_size, f"Chunk {i} is too large: {len(chunk)} characters"
        
    # A hallmark of a good chunker is that it didn't return empty strings
    for chunk in resulting_chunks:
        assert chunk.strip() != "", "Found an empty chunk!"
