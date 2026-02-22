import functools
import subprocess
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONFIGS_DIR = Path(__file__).resolve().parent / "configs"


def _build_site(config_file: Path, output_dir: Path) -> Path:
    subprocess.run(
        [
            "uv",
            "run",
            "mkdocs",
            "build",
            "--config-file",
            str(config_file),
            "--site-dir",
            str(output_dir),
        ],
        cwd=str(ROOT),
        check=True,
        capture_output=True,
    )
    return output_dir


def _serve_dir(directory: Path) -> tuple[HTTPServer, str]:
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(directory))
    server = HTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{port}"


@pytest.fixture(scope="session")
def default_site(tmp_path_factory):
    output = tmp_path_factory.mktemp("default")
    _build_site(ROOT / "mkdocs.yml", output)
    server, url = _serve_dir(output)
    yield url
    server.shutdown()


@pytest.fixture(scope="session")
def editor_site(tmp_path_factory):
    output = tmp_path_factory.mktemp("editor")
    _build_site(CONFIGS_DIR / "mkdocs-editor.yml", output)
    server, url = _serve_dir(output)
    yield url
    server.shutdown()


@pytest.fixture(scope="session")
def clean_validation_site(tmp_path_factory):
    output = tmp_path_factory.mktemp("clean-validation")
    _build_site(CONFIGS_DIR / "mkdocs-clean-validation.yml", output)
    server, url = _serve_dir(output)
    yield url
    server.shutdown()


@pytest.fixture(scope="session")
def no_validation_site(tmp_path_factory):
    output = tmp_path_factory.mktemp("no-validation")
    _build_site(CONFIGS_DIR / "mkdocs-no-validation.yml", output)
    server, url = _serve_dir(output)
    yield url
    server.shutdown()


@pytest.fixture(scope="session")
def graph_site(tmp_path_factory):
    output = tmp_path_factory.mktemp("graph")
    _build_site(CONFIGS_DIR / "mkdocs-graph.yml", output)
    server, url = _serve_dir(output)
    yield url
    server.shutdown()
