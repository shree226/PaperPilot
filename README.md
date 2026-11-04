# PaperPilot

PaperPilot is a source-grounded research assistant for uploading and comparing academic papers. It uses LangGraph research workflows, Hugging Face embeddings, Chroma vector collections, OpenRouter LLMs, and optional Tavily web search.

## The problem

Researchers often need to search, compare, synthesize, and verify evidence across multiple papers. Standard chat interfaces lose document boundaries, do not preserve uploaded collections reliably, and produce answers that are difficult to trace or verify.

## The solution

PaperPilot gives each research chat its own document collection. Uploaded files are indexed automatically, relevant chunks are retrieved for each question, and answers can be generated in controlled formats with source excerpts. Each collection remains reusable across follow-up questions.

## Features

- Automatic PDF, TXT, CSV, and Markdown indexing
- Separate Chroma vector collections for each research chat
- Persistent chat titles, messages, and indexed document metadata
- Follow-up questions with recent conversation context
- Source excerpts with filename and page metadata when available
- Document and collection removal
- Optional Tavily web search
- Report formats including standard report, comparison table, literature synthesis, gap analysis, methodology audit, evidence table, and executive brief
- Markdown and PDF answer export
- Markdown chat export
- Automatic bounded retries for LLM requests

## Technology

- Streamlit for the web interface
- LangGraph and LangChain for research orchestration
- Hugging Face sentence-transformer embeddings
- Chroma for persistent vector storage
- OpenRouter for model access
- Tavily for optional web search
- ReportLab for PDF export

## Requirements

- Linux, macOS, or Windows WSL
- Python 3.11 or 3.12
- At least 12 GB of free disk space for the embedding stack
- OpenRouter API access
- Optional Tavily API access
- Optional read-only Hugging Face token

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/PaperPilot.git
cd PaperPilot

python3.11 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

## Configuration

Copy the environment template:

```bash
cp .env.example .env
```

Set the required values in `.env`:

```dotenv
OPENROUTER_API_KEY="your_openrouter_key"
TAVILY_API_KEY="your_tavily_key"
HF_TOKEN=""

LANGCHAIN_TRACING_V2="false"
LANGCHAIN_API_KEY=""
LANGCHAIN_PROJECT="PaperPilot"
```

API keys are required as follows:

- `OPENROUTER_API_KEY`: required for generated answers
- `TAVILY_API_KEY`: required only if web search is enabled
- `HF_TOKEN`: optional; a fine-grained read-only token avoids unauthenticated Hugging Face download warnings
- LangSmith variables: optional

Do not commit `.env` or API keys.

## Run

```bash
source .venv/bin/activate
streamlit run app.py
```

Open the URL shown by Streamlit, normally:

```text
http://localhost:8501
```

In GitHub Codespaces, open the forwarded `8501` or configured Streamlit port from the Ports panel.

## Usage

1. Create a research chat.
2. Upload one or more PDF, TXT, CSV, or Markdown files.
3. Documents index automatically.
4. Select an answer format from the sidebar.
5. Ask about findings, compare papers, identify gaps, or audit methodology.
6. Expand Sources Used to inspect retrieved evidence.
7. Export the answer as Markdown or PDF.

Each chat has an isolated collection in `database/<collection-id>/`. Chat metadata is stored locally in `.paperpilot/chats.json`. These paths are generated locally and ignored by Git.

## Tests

```bash
source .venv/bin/activate
python -m pytest -q tests
python -m py_compile app.py src/assistant/*.py
```

Current tests cover document provenance formatting, collection isolation, and PDF generation.

## Custom report formats

Add `.md` or `.txt` files to `report_structures/`. Each filename becomes a selectable answer format. The file content is supplied to the final-report prompt.

## Troubleshooting

### Hugging Face warning

Add a fine-grained Hugging Face token with read-only public repository access to `HF_TOKEN`. The project can work without it when public model downloads remain available.

### Missing OpenRouter API key

Set `OPENROUTER_API_KEY` in `.env`, then restart Streamlit.

### Web search is disabled

Enable web search only after setting `TAVILY_API_KEY`.

### Streamlit does not update

Restart the process with:

```bash
Ctrl+C
streamlit run app.py
```

Clear only generated application data if needed:

```bash
rm -rf .paperpilot database files temp_files
```

The next run creates fresh local state. Do not remove `.venv` unless dependencies also need reinstalling.

## Security note

If API credentials were previously committed, rotate them immediately in OpenRouter, Tavily, Hugging Face, and LangSmith. Removing a secret from the latest commit does not invalidate it.

To stop tracking an already committed local environment file while preserving it locally:

```bash
git rm --cached .env
git add .gitignore .env.example README.md
```

## Limitations

- Generated answers should be verified against source documents.
- Retrieved page numbers depend on the PDF loader and document metadata.
- Semantic chunking can be slow for large collections.
- Web evidence and indexed-paper evidence should be interpreted separately.
- Chat persistence is local and not synchronized across devices.

## License

Add a LICENSE file before publishing the repository publicly.
