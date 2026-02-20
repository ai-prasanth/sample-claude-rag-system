import os
from dotenv import load_dotenv

import anthropic
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader

# Load ANTHROPIC_API_KEY (and any other vars) from the .env file into os.environ
load_dotenv()


def load_pdf(file_path):
    """
    Read a PDF file and return all of its text as a single string.

    Parameters
    ----------
    file_path : str
        Absolute or relative path to the PDF file.

    Returns
    -------
    str
        All text extracted from every page, joined with newlines.

    Example
    -------
    # text = load_pdf("data/report.pdf")
    # print(text[:200])  # preview first 200 characters
    """
    reader = PdfReader(file_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def chunk_text(text, chunk_size=500, overlap=50):
    """
    Split a long string into overlapping fixed-size chunks.

    Overlap lets each chunk share some context with its neighbours so that
    sentences near a boundary are not lost when searching the vector store.

    Parameters
    ----------
    text : str
        The full document text to be split.
    chunk_size : int, optional
        Number of characters per chunk (default: 500).
    overlap : int, optional
        Number of characters to repeat from the end of the previous chunk
        at the start of the next one (default: 50).

    Returns
    -------
    list[str]
        Ordered list of text chunks, each at most chunk_size characters long.

    Example
    -------
    # chunks = chunk_text(text, chunk_size=500, overlap=50)
    # print(f"{len(chunks)} chunks created")
    # print(chunks[0])  # first chunk
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap  # step back by overlap before next chunk
    return chunks


def index_documents(data_folder, embedding_model, qdrant_client):
    """
    Scan a folder for PDF files, embed their text chunks, and store them in Qdrant.

    For each PDF found:
      1. Extract all text with load_pdf()
      2. Split into overlapping chunks with chunk_text()
      3. Embed each chunk with the sentence transformer model
      4. Upsert into the Qdrant "documents" collection with metadata

    Each point stored in Qdrant has:
      - A unique integer ID  (global across all files)
      - A 384-dim vector     (the embedding of the chunk text)
      - Payload metadata:    {"filename": "...", "chunk_index": N, "text": "..."}

    Parameters
    ----------
    data_folder : str
        Path to the folder containing PDF files to index.
    embedding_model : SentenceTransformer
        Initialised sentence-transformer model used to create embeddings.
    qdrant_client : QdrantClient
        Initialised Qdrant client with the "documents" collection already created.

    Returns
    -------
    int
        Total number of chunks indexed across all PDF files.

    Example
    -------
    # total = index_documents("data/", embedding_model, qdrant_client)
    # print(f"Indexed {total} chunks into Qdrant")
    """
    pdf_files = [f for f in os.listdir(data_folder) if f.endswith(".pdf")]

    if not pdf_files:
        print("No PDF files found in data/ folder.")
        return 0

    chunk_id = 0  # globally unique ID for every chunk across all files

    for filename in pdf_files:
        file_path = os.path.join(data_folder, filename)
        print(f"\nIndexing: {filename}")

        # Step 1: extract text from the PDF
        text = load_pdf(file_path)

        # Step 2: split into overlapping chunks
        chunks = chunk_text(text)
        print(f"  {len(chunks)} chunks created")

        # Step 3 & 4: embed each chunk and upsert into Qdrant
        points = []
        for chunk_index, chunk in enumerate(chunks):
            embedding = embedding_model.encode(chunk).tolist()
            points.append(
                PointStruct(
                    id=chunk_id,
                    vector=embedding,
                    payload={
                        "filename": filename,
                        "chunk_index": chunk_index,
                        "text": chunk,
                    },
                )
            )
            chunk_id += 1

        qdrant_client.upsert(collection_name="documents", points=points)
        print(f"  Stored {len(points)} vectors for '{filename}'")

    print(f"\nIndexing complete. Total chunks indexed: {chunk_id}")
    return chunk_id


def ask_question(question, embedding_model, qdrant_client, anthropic_client):
    """
    Answer a question using RAG: retrieve relevant chunks, then ask Claude.

    Steps:
      1. Embed the question with the same model used to embed the documents.
      2. Search Qdrant for the 3 most similar chunks (cosine similarity).
      3. Concatenate those chunks into a context block.
      4. Build a prompt that instructs Claude to answer from the context only.
      5. Call the Claude API and return the text response.

    Parameters
    ----------
    question : str
        The natural-language question to answer.
    embedding_model : SentenceTransformer
        The same model used when indexing — ensures vectors are comparable.
    qdrant_client : QdrantClient
        Qdrant client holding the indexed document chunks.
    anthropic_client : anthropic.Anthropic
        Authenticated Anthropic client for calling Claude.

    Returns
    -------
    str
        Claude's answer, grounded in the retrieved context.

    Example
    -------
    # answer = ask_question("What was the Q3 revenue?", ...)
    # print(answer)
    """
    # Step 1: embed the question into the same vector space as the documents
    question_embedding = embedding_model.encode(question).tolist()

    # Step 2: retrieve the top 3 most similar chunks from Qdrant
    results = qdrant_client.query_points(
        collection_name="documents",
        query=question_embedding,
        limit=3,
        with_payload=True,
    ).points

    # Step 3: build context string from retrieved chunk texts
    context_chunks = [hit.payload["text"] for hit in results]
    context = "\n\n---\n\n".join(context_chunks)

    # Step 4: assemble the augmented prompt
    # "Answer based only on the context" keeps Claude from hallucinating
    # facts that aren't in the indexed documents.
    prompt = (
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer based only on the context above. "
        "If the answer is not in the context, say \"I don't know.\""
    )

    # Step 5: send to Claude and return the answer
    response = anthropic_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def main():
    # ── Embedding model ───────────────────────────────────────────────────────
    # all-MiniLM-L6-v2 is a lightweight model that runs locally and produces
    # 384-dimensional vectors — no external API needed for embedding.
    print("Loading embedding model...")
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    # ── Qdrant vector store (in-memory) ───────────────────────────────────────
    # Passing ":memory:" keeps everything in RAM — no disk setup required.
    # We create a collection called "documents" with:
    #   - size=384  → matches the all-MiniLM-L6-v2 output dimensions
    #   - COSINE    → measures similarity by angle between vectors (best for text)
    print("Initializing Qdrant client...")
    qdrant_client = QdrantClient(":memory:")
    qdrant_client.create_collection(
        collection_name="documents",
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )

    # ── Anthropic client ──────────────────────────────────────────────────────
    # The Anthropic client uses the API key from .env to call Claude,
    # which will generate answers from the retrieved document context.
    print("Initializing Anthropic client...")
    anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    print("\nAll systems ready!")
    print("- Embedding model : all-MiniLM-L6-v2")
    print("- Vector store    : Qdrant in-memory / collection='documents'")
    print("- LLM             : Claude (Anthropic)")

    # ── Index all PDFs in the data/ folder ───────────────────────────────────
    total_chunks = index_documents("data", embedding_model, qdrant_client)
    print(f"\nIndexed {total_chunks} chunks total.")

    # ── Sample verification — print the first stored chunk ────────────────────
    if total_chunks > 0:
        first_point = qdrant_client.retrieve(
            collection_name="documents",
            ids=[0],
            with_payload=True,
        )[0]
        payload = first_point.payload
        print("\n--- Sample: chunk 0 ---")
        print(f"File       : {payload['filename']}")
        print(f"Chunk index: {payload['chunk_index']}")
        print(f"Text preview:\n{payload['text'][:300]}")
        print("-----------------------")

    # ── Test question ─────────────────────────────────────────────────────────
    if total_chunks > 0:
        test_question = "How much did revenue grow year-over-year?"
        print(f"\nTest question: {test_question}")
        print("Asking Claude...\n")
        answer = ask_question(
            test_question, embedding_model, qdrant_client, anthropic_client
        )
        print(f"Answer: {answer}")


if __name__ == "__main__":
    main()
