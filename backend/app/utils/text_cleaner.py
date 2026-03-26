import re

def clean_text(text: str) -> str:
    """
    Cleans raw text extracted from PDF.
    - Removes repeated whitespaces
    - Removes noisy line breaks that don't indicate a new paragraph
    """
    if not text:
        return ""
    
    # Replace multiple newlines with a unique token to preserve paragraphs
    text = re.sub(r'\n{2,}', '<PARAGRAPH_BREAK>', text)
    
    # Replace single newlines with a space
    text = text.replace('\n', ' ')
    
    # Restore paragraph breaks
    text = text.replace('<PARAGRAPH_BREAK>', '\n\n')
    
    # Remove excessive spaces
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Remove zero-width chars and standard control chars
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    return text.strip()
