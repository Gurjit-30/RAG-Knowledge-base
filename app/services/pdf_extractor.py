import pdfplumber
from fastapi import UploadFile
import io
import logging

# Set up a simple logger so we can see what's happening behind the scenes
logger = logging.getLogger(__name__)

async def extract_text_from_uploaded_pdf(uploaded_file: UploadFile) -> str:
    """
    Takes an uploaded PDF file from the user and extracts all the text from it.
    It automatically reads through every page and combines the text.
    
    Args:
        uploaded_file (UploadFile): The PDF file uploaded via FastAPI.
        
    Returns:
        str: The full extracted text from all pages.
    """
    extracted_text_pieces = []
    
    try:
        # Read the raw bytes from the uploaded file
        file_content = await uploaded_file.read()
        
        # Turn the bytes into a file-like object so pdfplumber can read it natively
        pdf_stream = io.BytesIO(file_content)
        
        # Open the PDF and go through it page by page
        with pdfplumber.open(pdf_stream) as pdf_document:
            total_pages = len(pdf_document.pages)
            logger.info(f"Successfully opened the PDF. Found {total_pages} pages to process.")
            
            for page_num, page in enumerate(pdf_document.pages, start=1):
                # Try to extract the text from the current page
                page_text = page.extract_text()
                
                # Sometimes a page might be blank or just contain scanned images
                if page_text:
                    # Clean up the text a bit by removing extra whitespace at the ends
                    cleaned_text = page_text.strip()
                    extracted_text_pieces.append(cleaned_text)
                else:
                    # Good to log this so we know why some pages might be missing text
                    logger.warning(f"Looks like page {page_num} is empty or just an image.")
                    
        # Bring all the pages together into one long text string, separated by newlines
        final_document_text = "\n\n".join(extracted_text_pieces)
        
        return final_document_text
        
    except Exception as error:
        logger.error(f"Uh oh, something went wrong while extracting text: {error}")
        # Re-raise it so the caller knows something failed
        raise ValueError(f"Could not process the PDF file: {error}")
