import subprocess
from pathlib import Path

import pytest
from placeframe_stack.context_sha import compute_service_shas

BAKE_CONTENT = """\
services:
  app:
    build:
      context: .
      dockerfile: docker/app/Dockerfile
      tags:
        - "registry/app:${APP_SHA}"
  worker:
    build:
      context: .
      dockerfile: docker/worker/Dockerfile
      tags:
        - "registry/worker:${WORKER_SHA}"
  base:
    build:
      context: .
      dockerfile: docker/base/Dockerfile
"""


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=str(path), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(path), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(path), capture_output=True, check=True)


def _commit_all(path: Path) -> None:
    subprocess.run(["git", "add", "-A"], cwd=str(path), capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "init", "--allow-empty"], cwd=str(path), capture_output=True, check=True)


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    _init_repo(tmp_path)
    (tmp_path / ".dockerignore").write_text("*\n!docker/\n!packages/\n")
    (tmp_path / "docker" / "app").mkdir(parents=True)
    (tmp_path / "docker" / "app" / "main.py").write_text("print('hello')")
    (tmp_path / "docker" / "worker").mkdir(parents=True)
    (tmp_path / "docker" / "worker" / "run.py").write_text("print('work')")
    (tmp_path / "packages").mkdir()
    (tmp_path / "packages" / "lib.py").write_text("x = 1")
    (tmp_path / "README.md").write_text("ignored")
    bake_file = tmp_path / "compose.bake.yml"
    bake_file.write_text(BAKE_CONTENT)
    _commit_all(tmp_path)
    return tmp_path


class TestComputeServiceShas:
    def test_should_return_deterministic_hashes(self, repo: Path):
        shas1 = compute_service_shas(repo, repo / "compose.bake.yml")
        shas2 = compute_service_shas(repo, repo / "compose.bake.yml")

        assert shas1 == shas2

    def test_should_have_tree_prefix(self, repo: Path):
        shas = compute_service_shas(repo, repo / "compose.bake.yml")

        for sha in shas.values():
            assert sha.startswith("tree-")

    def test_should_return_only_tagged_services(self, repo: Path):
        shas = compute_service_shas(repo, repo / "compose.bake.yml")

        assert set(shas.keys()) == {"APP_SHA", "WORKER_SHA"}

    def test_should_change_only_affected_service_when_service_file_changes(self, repo: Path):
        shas_before = compute_service_shas(repo, repo / "compose.bake.yml")

        (repo / "docker" / "app" / "main.py").write_text("print('changed')")
        _commit_all(repo)

        shas_after = compute_service_shas(repo, repo / "compose.bake.yml")
        assert shas_before["APP_SHA"] != shas_after["APP_SHA"]
        assert shas_before["WORKER_SHA"] == shas_after["WORKER_SHA"]

    def test_should_change_all_services_when_shared_file_changes(self, repo: Path):
        shas_before = compute_service_shas(repo, repo / "compose.bake.yml")

        (repo / "packages" / "lib.py").write_text("x = 2")
        _commit_all(repo)

        shas_after = compute_service_shas(repo, repo / "compose.bake.yml")
        assert shas_before["APP_SHA"] != shas_after["APP_SHA"]
        assert shas_before["WORKER_SHA"] != shas_after["WORKER_SHA"]

    def test_should_not_change_when_ignored_file_changes(self, repo: Path):
        shas_before = compute_service_shas(repo, repo / "compose.bake.yml")

        (repo / "README.md").write_text("changed readme")
        _commit_all(repo)

        shas_after = compute_service_shas(repo, repo / "compose.bake.yml")
        assert shas_before == shas_after

    def test_should_not_change_from_uncommitted_edits(self, repo: Path):
        shas_before = compute_service_shas(repo, repo / "compose.bake.yml")

        (repo / "docker" / "app" / "main.py").write_text("print('uncommitted')")

        shas_after = compute_service_shas(repo, repo / "compose.bake.yml")
        assert shas_before == shas_after
