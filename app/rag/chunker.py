import re

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50):
    """
    Semantic chunker that splits text by sentence boundaries.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text.replace('\n', ' '))
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk += (" " if current_chunk else "") + sentence
            
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    if not chunks and text.strip():
        chunks = [text.strip()]
        
    return chunks