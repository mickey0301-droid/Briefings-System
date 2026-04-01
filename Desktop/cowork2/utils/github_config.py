import os
from typing import Optional, Tuple


def _read_streamlit_secret(*keys: str) -> Optional[str]:
    try:
        import streamlit as st
    except Exception:
        return None

    for key in keys:
        try:
            value = st.secrets[key]
        except Exception:
            value = None
        if value:
            return str(value).strip()
    return None


def get_github_token() -> Optional[str]:
    for key in ("GITHUB_TOKEN", "GH_TOKEN"):
        value = os.getenv(key, "").strip()
        if value:
            return value

    return _read_streamlit_secret("GITHUB_TOKEN", "GH_TOKEN", "github_token")


def configure_github_env() -> Tuple[bool, str]:
    token = get_github_token()
    if not token:
        return False, "missing"

    source = "env" if (os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")) else "secrets"

    if not os.getenv("GITHUB_TOKEN"):
        os.environ["GITHUB_TOKEN"] = token
    if not os.getenv("GH_TOKEN"):
        os.environ["GH_TOKEN"] = token

    return True, source

