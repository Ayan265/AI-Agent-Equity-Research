# Equity Research Agent Rules

These rules govern the development of the AI Agent For Equity Research. Strictly adhere to these constraints to ensure a robust, professional, and token-efficient architecture.

## 1. Architectural Philosophy
- **Separation of Concerns:** Never mix UI logic, extraction logic, and processing logic in the same file. Each Python file must serve a distinct, singular purpose.
- **Production-Ready Base:** All production code lives exclusively in `src/`. The root directory is strictly for environment configuration (`venv/`, `requirements.txt`).
- **Focus:** "Do only this one thing well before expanding." Complete and perfect one module before touching the next.

## 2. Text Extraction & Data Handling (PDFs)
- **Zero-Loss Extraction:** Do NOT aggressively delete or remove text using Regex when pulling from PDFs (financial data is sensitive; a wrong Regex could delete critical footnotes or numbers). 
- **Filtering Noise Later:** Extract everything faithfully first. We will build separate, intelligent downstream programs to determine what text is "useless."
- **Use Developer APIs over Hacky Workarounds:** NotebookLM and browser-automation are officially **deprecated** for data-extraction tasks. Always use fast, invisible Python scripts (like `pdfplumber`) and standard AI developer APIs (like Gemini/OpenAI) to generate strict JSON.

## 3. Token Efficiency Optimization
- **Whitespace Compression:** Always strip out massive white spaces. When joining PDF pages or paragraphs, use a single newline (`\n`) instead of massive multiline breaks. This prevents the downstream AI API from chewing through thousands of useless blank-space tokens.

## 4. Architecture: The Document-Driven Base Layer
To ensure the AI Agent does not waste context tokens when editing code, the architecture is strictly modularized by **Document Type**.
- **The Core Engine (`src/core/`):** Contains `api_client.py` (which MUST use `tenacity` for exponential backoff to handle free-tier API rate limits) and `pdf_processor.py`. This code is shared across all documents.
- **The Document Logic (`src/documents/`):** Contains isolated folders for each data source (e.g., `concalls/`, `screener/`, `annual_reports/`). 
  - Each isolated folder contains its own `parser.py` (regex chunking), `analyzer.py` (Pydantic AI extraction), and `formatter.py` (Markdown output).
- **The Execution Scripts:** All execution goes through a unified CLI `src/main.py` using arguments like `--task deep_qa`. Never create duplicate `main.py` files.
