# Install dependencies
install:
	uv sync

# Run main script
run:
	uv run python main.py

# Start llama.cpp server
server:
	./build/bin/llama-server -m models/model.gguf

# Run watcher pipeline
watch:
	uv run python main.py --watch

# Format code
format:
	uv run black .

# Clean cache
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete