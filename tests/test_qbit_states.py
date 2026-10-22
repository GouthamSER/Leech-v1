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


def test_requirements_cover_imports():
    """Every third-party import must map to a requirement (catches 'No module named pytz')."""
    import sys
    std = set(sys.stdlib_module_names)
    pkg_for = {"PIL": "pillow", "bs4": "beautifulsoup4", "dotenv": "python-dotenv", "google": "google-auth-oauthlib",
               "googleapiclient": "google-api-python-client", "google_auth_oauthlib": "google-auth-oauthlib",
               "imdb": "cinemagoer", "magic": "python-magic", "pyrogram": "pyrofork", "qbittorrentapi": "qbittorrent-api",
               "speedtest": "speedtest-cli", "yt_dlp": "yt-dlp", "aria2p": "aria2p", "pkg_resources": "setuptools"}
    # mega comes from megasdk in base image
    skip = {"bot", "web", "mega", "health", "envfiles", "update", "driveid", "gen_sa_accounts"}
    req = {re.split(r"[\[<>=~ @]", l.strip().lower().replace("_", "-"))[0]
           for l in (ROOT / "requirements.txt").read_text().splitlines()
           if l.strip() and not l.startswith("git+")} | {"lk21"}
    for p in ROOT.rglob("*.py"):
        if "tests" in p.parts:
            continue
        for n in ast.walk(ast.parse(p.read_text())):
            if isinstance(n, ast.Import):
                mods = [a.name.split(".")[0] for a in n.names]
            elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
                mods = [n.module.split(".")[0]]
            else:
                continue
            for m in mods:
                if m in std or m in skip:
                    continue
                need = pkg_for.get(m, m).lower().replace("_", "-")
                assert need in req, f"{p}: import {m} -> add '{need}' to requirements.txt"


def test_event_loop_set_before_pyrogram():
    s = (ROOT / "bot/__init__.py").read_text()
    assert "set_event_loop(" in s and "\ninstall()" not in s
    assert s.index("set_event_loop(_uv_new_loop())") < s.index("bot = wztgClient(")


def test_event_loop_runtime():
    import asyncio
    try:
        import uvloop
    except ImportError:
        return
    loop = uvloop.new_event_loop()
    asyncio.set_event_loop(loop)
    assert asyncio.get_event_loop() is loop
    loop.close()


def test_health_server_answers():
    import importlib.util, socket, urllib.request
    spec = importlib.util.spec_from_file_location("health", ROOT / "health.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    srv = m.start_health_server(port, "127.0.0.1")
    try:
        assert urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=3).read() == b"ok"
        c = socket.create_connection(("127.0.0.1", port), timeout=3); c.close()  # TCP check
    finally:
        srv.shutdown()


def test_health_wired_in_init():
    s = (ROOT / "bot/__init__.py").read_text()
    assert "start_health_server(" in s


def test_webpaste_no_undefined_err_and_handles_bad_json():
    s = (ROOT / "bot/modules/mirror_leech.py").read_text()
    blk = s[s.index('data[2] == "webpaste"'):s.index('data[2] == "botpm"')]
    assert "except Exception as err" in blk and "timeout=" in blk
    assert "sync_to_async(_paste)" in blk


def _load_added_ok():
    src = (ROOT / "bot/helper/mirror_utils/download_utils/qbit_download.py").read_text()
    fn = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "_added_ok")
    ns = {}
    exec(ast.get_source_segment(src, fn), ns)
    return ns["_added_ok"]


def test_added_ok_old_and_new_api():
    f = _load_added_ok()
    assert f("Ok.") and f("ok.") and not f("Fails.")
    assert f({"success_count": 1, "failure_count": 0, "pending_count": 0, "added_torrent_ids": ["x"]})
    assert f({"success_count": 0, "failure_count": 0, "pending_count": 1})
    assert not f({"success_count": 0, "failure_count": 1, "pending_count": 0})
    assert f({"unknown": 1})


def test_no_raw_lower_on_add_result():
    s = (ROOT / "bot/helper/mirror_utils/download_utils/qbit_download.py").read_text()
    assert "op.lower()" not in s
