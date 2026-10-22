"""Write files from base64 env vars. For hosts (Koyeb etc.) with no file upload.

Env var  <NAME>_B64  ->  file.  Example: TOKEN_PICKLE_B64 -> token.pickle
Also: <NAME>_B64 can hold plain text if it is not valid base64 (fallback).
"""
from base64 import b64decode
from binascii import Error as B64Error
from os import environ, path as ospath

FILES = {
    "CONFIG_ENV_B64": "config.env",
    "TOKEN_PICKLE_B64": "token.pickle",
    "CREDENTIALS_JSON_B64": "credentials.json",
    "COOKIES_TXT_B64": "cookies.txt",
    "RCLONE_CONF_B64": "rclone.conf",
    "NETRC_B64": ".netrc",
    "ACCOUNTS_ZIP_B64": "accounts.zip",
    "LIST_DRIVES_TXT_B64": "list_drives.txt",
    "CATEGORIES_TXT_B64": "categories.txt",
    "BUTTONS_TXT_B64": "buttons.txt",
    "SHORTENERS_TXT_B64": "shorteners.txt",
    "TERABOX_TXT_B64": "terabox.txt",
}


def write_files(env=environ, base="."):
    done = []
    for var, name in FILES.items():
        val = env.get(var, "").strip()
        if not val:
            continue
        try:
            data = b64decode(val, validate=True)
        except (B64Error, ValueError):
            data = val.encode()
        with open(ospath.join(base, name), "wb") as f:
            f.write(data)
        done.append(name)
    return done


if __name__ == "__main__":
    for n in write_files():
        print(f"envfiles: wrote {n}")
