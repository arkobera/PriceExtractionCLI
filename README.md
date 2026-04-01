# QuantityExtractionCLI

A local CLI tool for extracting product quantities from images using a Vision Language Model (VLM) powered by llama.cpp.

## Features

- Extract item names, quantities, and units from product images
- Watch a directory for new images and process them automatically
- One-time batch processing of multiple images or directories
- Export results to CSV
- Pretty-print results in a formatted table
- Runs entirely locally using llama-server

## Requirements

- Python >= 3.10
- llama.cpp built with server support
- A GGUF vision model (e.g., LLaVA, Bakllava)

## Installation

```bash
# Clone the repo
git clone <repo-url>
cd PriceExtractionCLI

# Install dependencies
make install
# or
uv sync
```

## Usage

### Start the LLM Server

```bash
make server
# or manually
./build/bin/llama-server -m models/model.gguf --port 8080
```

### Process Images (One-time)

```bash
uv run python main.py process --model models/model.gguf path/to/images/

# With CSV output
uv run python main.py process --model models/model.gguf --output results.csv path/to/images/

# Custom port
uv run python main.py process --model models/model.gguf --port 9090 path/to/images/
```

### Watch Mode (Continuous)

```bash
uv run python main.py watch --model models/model.gguf --dir path/to/watch/
```

This will monitor the directory for new images and automatically extract quantities, saving results to `quantities.csv` inside the watched directory.

## Output Format

### CSV Columns

| Column | Description |
|---|---|
| `processed_at` | Timestamp of processing |
| `file_path` | Path to the source image |
| `item_name` | Product name extracted from image |
| `quantity` | Numeric quantity (e.g., 2, 3.5) |
| `unit` | Measurement unit (e.g., bottles, packs, kg) |

### Example Table Output

```
┌──────────────┬─────────────┬──────────┬────────┐
│ File         │ Item Name   │ Quantity │ Unit   │
├──────────────┼─────────────┼──────────┼────────┤
│ image1.jpg   │ Toothpaste  │ 2        │ packs  │
├──────────────┼─────────────┼──────────┼────────┤
│ image2.png   │ Fevicol     │ 1        │ bottle │
└──────────────┴─────────────┴──────────┴────────┘
```

## Project Structure

```
PriceExtractionCLI/
├── main.py                        # CLI entry point (click commands)
├── price_extractor/
│   ├── __init__.py
│   ├── extractor.py               # Quantity extraction logic + VLM prompt
│   ├── file_handler.py            # File watching, CSV writing
│   ├── llama_server.py            # llama-server subprocess management
│   └── table_printer.py           # Pretty table output
├── pyproject.toml
├── Makefile
└── README.md
```

## Development

```bash
# Format code
make format

# Clean cache
make clean
```

## Dependencies

- `click` - CLI framework
- `openai` - OpenAI-compatible API client
- `pydantic` - Data validation and schemas
- `loguru` - Logging
- `watchdog` - File system monitoring
