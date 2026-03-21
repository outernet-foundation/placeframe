# ruff: noqa: S404, S603 — tests for the subprocess wrapper
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from common.bash import bash, bash_check, bash_check_stream, bash_no_raise, bash_output


class TestBashOutput:
    def test_captures_stdout(self):
        assert bash_output("echo hello") == "hello\n"

    def test_returns_empty_string_on_no_output(self):
        assert bash_output("true") == ""

    def test_raises_on_failure(self):
        with pytest.raises(subprocess.CalledProcessError):
            bash_output("false")

    def test_attaches_stderr_to_exception(self):
        with pytest.raises(subprocess.CalledProcessError) as exc_info:
            bash_output("sh -c 'echo oops >&2; exit 1'")
        assert "oops" in (exc_info.value.stderr or "")

    def test_attaches_stdout_to_exception(self):
        with pytest.raises(subprocess.CalledProcessError) as exc_info:
            bash_output("sh -c 'echo partial; exit 1'")
        assert "partial" in (exc_info.value.stdout or "")

    def test_respects_cwd(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = bash_output("pwd", cwd=Path(tmpdir))
            assert result.strip() == tmpdir

    def test_passes_stdin_text(self):
        assert bash_output("cat", stdin_text="hello world") == "hello world"

    def test_handles_quoted_arguments(self):
        assert bash_output("echo 'hello world'") == "hello world\n"


class TestBash:
    def test_no_raise_on_success(self):
        bash("true")

    def test_raises_on_failure(self):
        with pytest.raises(subprocess.CalledProcessError):
            bash("false")

    def test_returns_none(self):
        assert bash("true") is None

    def test_respects_cwd(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    f"from pathlib import Path; from common.bash import bash; bash('pwd', cwd=Path('{tmpdir}'))",
                ],
                capture_output=True,
                text=True,
            )
            assert tmpdir in result.stdout

    def test_passes_stdin_text(self):
        result = subprocess.run(
            [sys.executable, "-c", "from common.bash import bash; bash('cat', stdin_text='streamed input')"],
            capture_output=True,
            text=True,
        )
        assert "streamed input" in result.stdout


class TestBashCheck:
    def test_returns_true_on_success(self):
        assert bash_check("true") is True

    def test_returns_false_on_failure(self):
        assert bash_check("false") is False

    def test_no_raise_on_failure(self):
        bash_check("false")

    def test_respects_cwd(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            assert bash_check(f"test -d {tmpdir}") is True

    def test_suppresses_all_output(self, capsys):
        bash_check("echo should_not_appear")
        captured = capsys.readouterr()
        assert "should_not_appear" not in captured.out
        assert "should_not_appear" not in captured.err


class TestBashCheckStream:
    def test_returns_true_on_success(self):
        assert bash_check_stream("true") is True

    def test_returns_false_on_failure(self):
        assert bash_check_stream("false") is False

    def test_no_raise_on_failure(self):
        bash_check_stream("false")

    def test_respects_cwd(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            assert bash_check_stream(f"test -d {tmpdir}") is True


class TestBashNoRaise:
    def test_no_raise_on_success(self):
        bash_no_raise("true")

    def test_no_raise_on_failure(self):
        bash_no_raise("false")

    def test_returns_none(self):
        assert bash_no_raise("true") is None

    def test_respects_cwd(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bash_no_raise(f"test -d {tmpdir}")


class TestBashHandoff:
    def test_stdout_contains_output(self):
        result = subprocess.run(
            [sys.executable, "-c", "from common.bash import bash_handoff; bash_handoff('echo handoff_test')"],
            capture_output=True,
            text=True,
        )
        assert "handoff_test" in result.stdout

    def test_exit_code_matches(self):
        result = subprocess.run(
            [sys.executable, "-c", "from common.bash import bash_handoff; bash_handoff('sh -c \"exit 42\"')"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 42

    def test_respects_cwd(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    f"from pathlib import Path; from common.bash import bash_handoff; bash_handoff('pwd', cwd=Path('{tmpdir}'))",
                ],
                capture_output=True,
                text=True,
            )
            assert tmpdir in result.stdout
