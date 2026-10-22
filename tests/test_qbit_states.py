"""Static tests: qBit 5.x state names handled, files parse, version ok. Run: python -m pytest tests"""
import ast, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
FILES = [
    "bot/helper/mirror_utils/download_utils/qbit_download.py",
    "bot/helper/mirror_utils/status_utils/qbit_status.py",
    "bot/helper/listeners/qbit_listener.py",
]


def test_all_py_parse():
    for p in ROOT.rglob("*.py"):
        if "tests" in p.parts:
            continue
        ast.parse(p.read_text(encoding="utf-8"), filename=str(p))


def test_qbit5_stopped_states_handled():
    for f in FILES:
        s = (ROOT / f).read_text()
        assert "stoppedDL" in s, f"{f}: missing qBit5 stoppedDL"
    assert "stoppedUP" in (ROOT / FILES[1]).read_text()
    assert "stoppedUP" in (ROOT / FILES[2]).read_text()


def test_legacy_paused_kept():
    assert "pausedDL" in (ROOT / FILES[0]).read_text()


def test_aria_fake_qbit_version_new():
    s = (ROOT / "aria.sh").read_text()
    assert "-qB5240-" in s and "qBittorrent/5.2.4" in s


def test_dockerfile_qbit5():
    s = (ROOT / "Dockerfile").read_text()
    assert re.search(r"QBIT_TAG=release-5\.", s)


def test_version_format():
    ns = {}
    exec((ROOT / "bot/version.py").read_text(), ns)
    assert re.fullmatch(r"v\d+\.\d+\.\d+-\w+", ns["get_version"]())
