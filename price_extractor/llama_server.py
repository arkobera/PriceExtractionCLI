"""
Manage a llama-server subprocess for local LLM inference.
"""

import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from loguru import logger

DEFAULT_PORT = 8080


def start_llama_server(
    model_path: str,
    port: int = DEFAULT_PORT,
    verbose: bool = False,
    use_hf: bool = False,
) -> subprocess.Popen:
    """Start llama-server as a subprocess.

    Args:
        model_path: Path to GGUF model OR HF model ID
        port: Port to run the server on
        verbose: Show logs or suppress
        use_hf: Whether model_path is HuggingFace ID

    Returns:
        Subprocess handle
    """

    # 🔥 IMPORTANT: correct binary path
    binary = "./build/bin/llama-server"

    if not Path(binary).exists():
        raise FileNotFoundError(
            "llama-server binary not found. Did you build llama.cpp?"
        )

    # 🔁 Choose mode
    if use_hf:
        cmd = [binary, "-hf", model_path, "--port", str(port)]
    else:
        cmd = [binary, "-m", model_path, "--port", str(port)]

    logger.info(f"Starting llama-server with command: {' '.join(cmd)}")

    if verbose:
        process = subprocess.Popen(cmd)
    else:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    return process


def wait_for_server(port: int = DEFAULT_PORT, timeout: int = 120) -> None:
    """Wait until server is ready."""
    url = f"http://127.0.0.1:{port}/health"

    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    logger.info("llama-server is ready")
                    return
        except (urllib.error.URLError, urllib.error.HTTPError):
            pass

        time.sleep(0.5)

    raise TimeoutError(f"Server not ready within {timeout}s")


def stop_server(process: subprocess.Popen) -> None:
    """Stop llama-server."""
    logger.info("Stopping llama-server...")
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        logger.warning("Force killing server...")
        process.kill()
        process.wait()
    logger.info("llama-server stopped")