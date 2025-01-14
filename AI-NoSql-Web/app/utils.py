import zipfile
import io
from PyPDF2 import PdfReader
import re
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
import google.generativeai as genai
import numpy as np

def extract_zip_in_memory(file_stream):
    """
    Extract the contents of a ZIP file from an in-memory stream.

    Args:
        file_stream (BytesIO): In-memory stream of the uploaded ZIP file.

    Returns:
        dict: A dictionary with file names as keys and file contents (bytes) as values.
    """
    extracted_files = {}
    try:
        with zipfile.ZipFile(file_stream) as zip_ref:
            for file_name in zip_ref.namelist():
                # Skip directories
                if not file_name.endswith("/"):
                    extracted_files[file_name] = zip_ref.read(file_name)
    except zipfile.BadZipFile:
        raise ValueError("Invalid ZIP file")

    return extracted_files

def extract_text_from_pdf(pdf_content):
    """
    Extract text from a PDF file provided as in-memory bytes.

    Args:
        pdf_content (bytes): The content of the PDF file in bytes.

    Returns:
        str: The extracted text from the PDF.
    """
    try:
        pdf_stream = io.BytesIO(pdf_content)
        reader = PdfReader(pdf_stream)
        text = " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

# Initialize Pinecone instance
pc = Pinecone(api_key="pcsk_uRWBd_9d9dj1Y23zC6WzU6uC1iZJWqKXhCVUEECGtquP7JmJPTNzzhQd2Cgs7k2HpBNYe")  # Replace with your actual API key

# Index configuration
index_name = "txt-document-vectors"  # Use the name from your Pinecone UI

# Create Pinecone index if it doesn't exist
if index_name not in pc.list_indexes().names():
    # Recreate the Pinecone index with a larger dimension
    pc.create_index(
        name=index_name,
        dimension=384,
        metric="cosine",  # Similarity metric (cosine)
        spec=ServerlessSpec(
            cloud="aws",  # Cloud provider
            region="us-east-1"  # Region from the Pinecone UI
        )
    )

# Connect to the Pinecone index
index = pc.Index(index_name)


# Initialize SentenceTransformer for embedding
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def split_text(text, chunk_size=500):
    """
    Split the text into smaller chunks, ensuring chunks do not split sentences
    or paragraphs unnecessarily.

    Parameters:
    - text (str): The input text to split.
    - chunk_size (int): Target chunk size in characters (default: 500).

    Returns:
    - List[str]: A list of text chunks.
    """
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        sentence_length = len(sentence)

        if current_length + sentence_length > chunk_size:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_length = 0

        current_chunk.append(sentence)
        current_length += sentence_length

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return [chunk.strip() for chunk in chunks if chunk.strip()]


def index_text_in_pinecone(file_name, text):
    """
    Index text content into Pinecone after splitting it into chunks.

    Parameters:
    - file_name (str): The name of the file being indexed.
    - text (str): The text content to index.
    """
    text_chunks = split_text(text)

    for i, chunk in enumerate(text_chunks):
        safe_file_name = re.sub(r'[^a-zA-Z0-9]', '_', f"{file_name}_{i}")
        try:
            # Generate embedding for the chunk
            vector = model.encode(chunk).tolist()

            # Upsert vector into Pinecone
            response = index.upsert(vectors=[{
                "id": safe_file_name,
                "values": vector,
                "metadata": {
                    "file_name": file_name,
                    "chunk_index": i,
                    "text": chunk
                }
            }])

            if response:
                print(f"Successfully indexed: {safe_file_name}")
            else:
                print(f"Failed to index: {safe_file_name}")

        except Exception as e:
            print(f"Error indexing chunk {i} of {file_name}: {e}")


def process_text_streams_and_store_in_pinecone(txt_streams):
    """
    Process text streams in memory and store their content in Pinecone.

    Parameters:
    - txt_streams (list of tuple): List of tuples with file name and in-memory text stream.
    """
    for file_name, text_stream in txt_streams:
        try:
            # Read the text content from the in-memory stream
            text = text_stream.getvalue().decode("utf-8")  # Use `getvalue()` to avoid file operations
            if text.strip():
                index_text_in_pinecone(file_name, text)
            else:
                print(f"Empty or whitespace-only content in {file_name}")
        except Exception as e:
            print(f"Error processing {file_name}: {e}")


# Configure Google Generative AI with the API key
genai_api_key = "AIzaSyD_bmrFMFMTISMu0160udu474ZOdxMoR7A"
genai.configure(api_key=genai_api_key)

# Initialize the GenerativeModel
genai_model = genai.GenerativeModel('gemini-1.5-flash')  # Replace with the desired model name


# Function to generate an answer based on user-provided key points
def generate_answer(key_points, num_key_points=3):
    answers = []
    
    for i in range(num_key_points):
        prompt = key_points[i]
        
        # Generate and normalize the query vector
        query_vector = model.encode([prompt])
        query_vector = query_vector / np.linalg.norm(query_vector)  # Normalize to unit vector

        # Flatten the query_vector (ensure it's 1D)
        query_vector = query_vector.flatten().tolist()

        if len(query_vector) != 384:
            print(f"Error: Query vector dimension is incorrect (expected 384, got {len(query_vector)})")
            continue

        try:
            # Search for relevant chunks based on the prompt
            results = index.query(namespace="", vector=query_vector, top_k=40, include_values=True, includeMetadata=True)
            if not results or 'matches' not in results or len(results['matches']) == 0:
                print(f"No results found for the prompt: {prompt}")
                context = "No relevant text found."
            else:
                context = results['matches'][0]['metadata']['text']
            
            # Use Google Generative AI to generate the summary for the key point
            full_prompt = f"Answer to the following question'{prompt}':\n using these documents{context}"
            
            # Use the GenerativeModel instance to generate the content
            response = genai_model.generate_content(full_prompt)
            answer = response.text.strip()  # Extract and clean the response text
        except Exception as e:
            answer = f"Error generating answer: {str(e)}"

        answers.append({"key_point": prompt, "answer": answer})
    
    return answers
