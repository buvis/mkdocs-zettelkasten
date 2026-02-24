import functools
import subprocess
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONFIGS_DIR = Path(__file__).resolve().parent / "configs"

# Zettel IDs from docs/ fixtures — shared across E2E tests
ZETTEL_INSTALL = "20211122194827"
ZETTEL_DEMO = "20211122195311"
ZETTEL_PUBLISH = "20211122195910"


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


@pytest.fixture(scope="session")
def preview_site(tmp_path_factory):
    output = tmp_path_factory.mktemp("preview")
    _build_site(CONFIGS_DIR / "mkdocs-preview.yml", output)
    server, url = _serve_dir(output)
    yield url
    server.shutdown()


@pytest.fixture(scope="session")
def math_site(tmp_path_factory):
    output = tmp_path_factory.mktemp("math")
    _build_site(CONFIGS_DIR / "mkdocs-math.yml", output)
    server, url = _serve_dir(output)
    yield url
    server.shutdown()


@pytest.fixture(scope="session")
def topnav_site(tmp_path_factory):
    output = tmp_path_factory.mktemp("topnav")
    _build_site(CONFIGS_DIR / "mkdocs-topnav.yml", output)
    server, url = _serve_dir(output)
    yield url
    server.shutdown()
