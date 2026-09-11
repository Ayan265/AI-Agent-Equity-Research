# 📈 AI Agent for Equity Research

An intelligent, document-driven AI agent designed to automate the extraction, analysis, and comparison of complex financial documents. Designed specifically for Equity Research, this agent processes massive PDFs (Earnings Call Transcripts, Annual Reports, Screeners) into structured, queryable data without hallucination or data loss.

## 🌟 Key Features
- **Zero-Loss Data Extraction**: Employs robust extraction techniques using developer APIs (`pdfplumber` + AI) instead of hacky browser automation, ensuring no critical footnotes or figures are dropped.
- **Document-Driven Architecture**: Highly modular design. Each data source (e.g., `concalls`, `annual_reports`) operates in complete isolation with its own parser, analyzer, and formatter.
- **Token-Efficient Processing**: Automatically compresses whitespace and uses strict regex chunking to prevent large language models from wasting context tokens on empty space.
- **Production-Ready Core Engine**: Features built-in exponential backoff (via `tenacity`) for handling API rate limits gracefully, making it reliable for free-tier and production environments alike.

## 🏗️ Architecture

The codebase strictly adheres to a separation-of-concerns philosophy:
- **`src/core/`**: Shared services (e.g., API clients with robust retry logic, PDF processors).
- **`src/documents/`**: Isolated modules for specific financial documents.
  - `concalls/`
  - `screener/`
  - `annual_reports/`
  Each module has a dedicated `parser.py`, `analyzer.py`, and `formatter.py`.
- **Unified Execution**: A single `src/main.py` CLI acts as the unified entry point (e.g., running tasks like `--task deep_qa`).

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- API Keys for the respective AI models (Gemini / OpenAI).

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/equity-research-ai.git
   cd equity-research-ai
   ```

2. **Set up Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements_agent.txt
   ```

4. **Environment Variables**
   Create a `.env` file in the root directory and add your API keys:
   ```env
   AI_API_KEY=your_api_key_here
   ```

### Usage
Run the unified CLI to execute document analysis:
```bash
python src/main.py --task deep_qa --doc_type concalls --file path/to/transcript.pdf
```

## 🔒 Security
All sensitive information, such as `.env` files, cache data, and the `private/` workspace directory, are excluded via `.gitignore` to ensure they are never published publicly.

---
*Built with precision for modern Equity Research.*
