# PDF Chat RAG

A Retrieval-Augmented Generation (RAG) application that lets you chat with PDF documents using Claude AI. Drop PDFs into the `data/` folder, run the script, and ask questions — Claude answers using only the content from your documents.

## How It Works

```
PDF files → extract text → chunk → embed → Qdrant (vector store)
Question  → embed → similarity search → top 3 chunks → Claude → Answer
```

## Prerequisites

- **Python 3.12+** — the project uses modern Python features and libraries
- **Anthropic API key** — get one free at [console.anthropic.com](https://console.anthropic.com)

## Setup

**1. Clone the repository**
```bash
git clone <your-repo-url>
cd pdf-chat-rag
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Configure your API key**
```bash
cp .env.example .env
```
Open `.env` and replace `your_api_key_here` with your actual Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-...
```

**4. Add PDFs to the data/ folder**
```bash
cp /path/to/your/document.pdf data/
```
You can add as many PDFs as you like — all of them will be indexed automatically.

**5. Run the application**
```bash
python main.py
```

## Project Structure

```
pdf-chat-rag/
├── main.py              # RAG pipeline (load, chunk, embed, search, answer)
├── create_sample_pdf.py # Generates a sample PDF for testing
├── requirements.txt     # Python dependencies
├── .env                 # Your API key (not committed to git)
├── .env.example         # Template for .env
├── data/                # Place your PDF files here
└── README.md
```

## Troubleshooting

**`ANTHROPIC_API_KEY` not set or invalid**
- Make sure you copied `.env.example` to `.env` (not `.env.example` itself)
- Verify the key starts with `sk-ant-` and has no extra spaces
- Get a valid key at [console.anthropic.com](https://console.anthropic.com)

**`No PDF files found in data/ folder`**
- Ensure your files have a `.pdf` extension (lowercase)
- Check you placed them inside the `data/` folder, not the project root

**Embedding model download is slow on first run**
- `all-MiniLM-L6-v2` (~90 MB) is downloaded from Hugging Face on first use
- Subsequent runs use the cached model and start instantly

**`chromadb` import error**
- This project uses `qdrant-client` instead of ChromaDB (ChromaDB is not compatible with Python 3.14+)
- Run `pip install -r requirements.txt` to ensure the correct packages are installed

**Answers seem incorrect or vague**
- The model answers *only* from your indexed documents — it will say "I don't know" if the answer isn't in any PDF
- Try adding more relevant PDFs to the `data/` folder
- Chunk size (default 500 chars) can be tuned in `chunk_text()` if context is being cut off

## Getting an Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up or log in
3. Navigate to **API Keys** in the sidebar
4. Click **Create Key**, give it a name, and copy it
5. Paste it into your `.env` file as `ANTHROPIC_API_KEY=sk-ant-...`
