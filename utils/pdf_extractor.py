"""
PDF Text Extraction Utility with Page Tracking
"""
import PyPDF2
import re


def extract_text_from_pdf(pdf_file, track_pages=True) -> dict:
    """
    Extract text from PDF file with page tracking
    
    Args:
        pdf_file: File object (from st.file_uploader or open())
        track_pages: If True, returns dict with page info
    
    Returns:
        If track_pages=True: {'text': str, 'pages': list of {page_num, text}}
        If track_pages=False: str (just text)
    """
    try:
        # Handle both file paths and file objects
        if isinstance(pdf_file, str):
            # File path
            with open(pdf_file, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                return _extract_pages(pdf_reader, track_pages)
        else:
            # File object from Streamlit
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            return _extract_pages(pdf_reader, track_pages)
    
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {e}")


def _extract_pages(pdf_reader, track_pages):
    """Internal function to extract pages"""
    if track_pages:
        pages_data = []
        full_text = ""
        
        for page_num, page in enumerate(pdf_reader.pages, start=1):
            page_text = page.extract_text()
            pages_data.append({
                'page_num': page_num,
                'text': page_text,
                'char_start': len(full_text),
                'char_end': len(full_text) + len(page_text)
            })
            full_text += page_text + "\n"
        
        return {
            'text': full_text.strip(),
            'pages': pages_data,
            'total_pages': len(pages_data)
        }
    else:
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()


def find_page_number(text_snippet: str, pages_data: list) -> int:
    """
    Find which page contains a text snippet
    
    Args:
        text_snippet: Text to search for
        pages_data: List of page dictionaries from extract_text_from_pdf
    
    Returns:
        Page number (1-indexed) or None
    """
    if not pages_data:
        return None
    
    # Clean snippet for matching
    snippet_clean = text_snippet[:100].strip()
    
    for page_info in pages_data:
        if snippet_clean in page_info['text']:
            return page_info['page_num']
    
    return None


def is_pdf(filename: str) -> bool:
    """Check if file is PDF based on extension"""
    return filename.lower().endswith('.pdf')


# Test
if __name__ == "__main__":
    print("PDF Extractor utility ready!")