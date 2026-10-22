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


def test_ytdlp_gzip_deps():
    r = (ROOT / "requirements.txt").read_text()
    assert "yt-dlp[default]" in r and "brotli" in r and "zstandard" in r


def test_no_br_header_without_decoder():
    s = (ROOT / "bot/helper/mirror_utils/download_utils/direct_link_generator.py").read_text()
    assert "gzip, deflate, br" not in s


def test_envfiles_roundtrip(tmp_path):
    import base64, importlib.util
    spec = importlib.util.spec_from_file_location("envfiles", ROOT / "envfiles.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    raw = b"\x80\x04binary-pickle\x00"
    env = {"TOKEN_PICKLE_B64": base64.b64encode(raw).decode(), "COOKIES_TXT_B64": "# plain text"}
    out = m.write_files(env, str(tmp_path))
    assert set(out) == {"token.pickle", "cookies.txt"}
    assert (tmp_path / "token.pickle").read_bytes() == raw
    assert (tmp_path / "cookies.txt").read_text() == "# plain text"
