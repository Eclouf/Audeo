from __future__ import annotations

import json
import os
import sys
import webbrowser
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import urlparse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from pathlib import Path


@dataclass(frozen=True)
class UpdateCheckResult:
    repo: str
    current_version: str
    latest_tag: str
    open_url: str
    asset_url: Optional[str]
    is_update_available: bool
    raw_release: Optional[dict[str, Any]] = None


def parse_version(v: str) -> tuple[int, int, int]:
    if not v:
        return (0, 0, 0)
    v = str(v).strip()
    if v.startswith("v"):
        v = v[1:]
    parts = v.split(".")
    nums: list[int] = []
    for p in parts[:3]:
        try:
            nums.append(int(p))
        except Exception:
            nums.append(0)
    while len(nums) < 3:
        nums.append(0)
    return (nums[0], nums[1], nums[2])


def normalize_version_str(v: str) -> str:
    v = str(v or "").strip()
    if v.startswith("v"):
        v = v[1:]
    return v


def pick_asset_url(release: dict[str, Any]) -> Optional[str]:
    assets = release.get("assets") or []
    if not isinstance(assets, list):
        return None

    platform_key = "linux"
    if sys.platform == "win32":
        platform_key = "windows"
    elif sys.platform == "darwin":
        platform_key = "mac"

    preferred_exts = {
        # Targets you want to publish primarily.
        "windows": [".exe", ".msi", ".zip"],
        "mac": [".dmg", ".zip"],
        "linux": [".AppImage", ".appimage", ".tar.gz", ".zip"],
    }[platform_key]

    def score_asset(name: str) -> int | None:
        n = name.lower()
        for i, ext in enumerate(preferred_exts):
            if n.endswith(ext.lower()):
                base = i * 100
                # Platform-specific preference by naming convention.
                if platform_key == "windows" and ext.lower() == ".exe":
                    # Prefer installer exe (setup/installer) over portable exe.
                    if "setup" in n or "installer" in n:
                        base -= 50
                if platform_key == "linux" and (ext.lower() in [".appimage", ".appimage"]):
                    # Prefer canonical casing AppImage if present.
                    if name.endswith(".AppImage"):
                        base -= 10
                return base
        return None

    candidates: list[tuple[int, str]] = []
    for a in assets:
        try:
            name = str(a.get("name") or "")
            url = str(a.get("browser_download_url") or "")
        except Exception:
            continue
        if not name or not url:
            continue

        score = score_asset(name)
        if score is not None:
            candidates.append((score, url))

    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def _fetch_json(url: str) -> Any:
    req = Request(url, headers={"User-Agent": "Audeo-2"})
    try:
        with urlopen(req, timeout=15) as resp:
            data = resp.read().decode("utf-8", errors="replace")
        return json.loads(data)
    except HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
            parsed = json.loads(body)
            if isinstance(parsed, dict):
                parsed.setdefault("status", e.code)
                return parsed
        except Exception:
            pass
        return {"message": str(e), "status": getattr(e, "code", None)}
    except URLError as e:
        return {"message": str(e), "status": None}


def fetch_latest_release(repo: str) -> dict[str, Any]:
    """Fetch the latest release info for a repo.

    Uses a resilient strategy:
    - releases/latest
    - releases?per_page=10 (first non-draft, prefer non-prerelease)
    - tags?per_page=10 (last resort)

    Raises ValueError on failure.
    """

    latest_url = f"https://api.github.com/repos/{repo}/releases/latest"
    releases_url = f"https://api.github.com/repos/{repo}/releases?per_page=10"
    tags_url = f"https://api.github.com/repos/{repo}/tags?per_page=10"
    releases_page_url = f"https://github.com/{repo}/releases"

    # 1) official latest
    data = _fetch_json(latest_url)
    if isinstance(data, dict) and data.get("message") == "Not Found":
        data = None
    if isinstance(data, dict) and ("tag_name" in data):
        return data

    # 2) releases list
    data = _fetch_json(releases_url)
    if isinstance(data, list) and data:
        non_draft = [r for r in data if isinstance(r, dict) and not r.get("draft")]
        stable = [r for r in non_draft if not r.get("prerelease")]
        if stable:
            return stable[0]
        if non_draft:
            return non_draft[0]

    # 3) tags fallback
    data = _fetch_json(tags_url)
    if isinstance(data, list) and data:
        tag = str((data[0] or {}).get("name") or "")
        return {
            "tag_name": tag,
            "html_url": releases_page_url,
            "assets": [],
        }

    if isinstance(data, dict) and data.get("message"):
        raise ValueError(f"GitHub API error: {data.get('message')}")

    raise ValueError("Unable to resolve latest release")


def check_for_updates(*, repo: str, current_version: str) -> UpdateCheckResult:
    release = fetch_latest_release(repo)

    tag = str(release.get("tag_name") or "")
    html_url = str(release.get("html_url") or "")
    asset_url = pick_asset_url(release)

    releases_page_url = f"https://github.com/{repo}/releases"
    open_url = asset_url or html_url or releases_page_url

    current = parse_version(current_version)
    latest = parse_version(tag)

    return UpdateCheckResult(
        repo=repo,
        current_version=current_version,
        latest_tag=tag,
        open_url=open_url,
        asset_url=asset_url,
        is_update_available=latest > current,
        raw_release=release if isinstance(release, dict) else None,
    )


def open_updates_page(url: str) -> None:
    webbrowser.open(url)


def download_file(url: str, dest_path: Path, *, on_progress=None, chunk_size: int = 1024 * 128) -> Path:
    """Download `url` to `dest_path`.

    `on_progress` is called as: on_progress(downloaded_bytes: int, total_bytes: Optional[int])
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    req = Request(url, headers={"User-Agent": "Audeo-2"})
    with urlopen(req, timeout=60) as resp:
        total = resp.headers.get("Content-Length")
        try:
            total_bytes = int(total) if total else None
        except Exception:
            total_bytes = None

        downloaded = 0
        with open(dest_path, "wb") as f:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if on_progress is not None:
                    on_progress(downloaded, total_bytes)

    return dest_path


def open_file_in_os(path: Path) -> None:
    """Open a file with the OS default handler."""
    if sys.platform == "win32":
        os.startfile(str(path))
    elif sys.platform == "darwin":
        import subprocess

        subprocess.Popen(["open", str(path)])
    else:
        import subprocess

        subprocess.Popen(["xdg-open", str(path)])


def asset_filename_from_url(url: str, *, fallback: str = "Audeo-2-update") -> str:
    try:
        parsed = urlparse(url)
        name = Path(parsed.path).name
        return name or fallback
    except Exception:
        return fallback


def download_update_asset(
    *,
    asset_url: str,
    cache_dir: Path,
    on_progress=None,
) -> Path:
    """Download an update asset into cache_dir/updates and return the local path."""
    filename = asset_filename_from_url(asset_url)
    dest_dir = cache_dir / "updates"
    dest_path = dest_dir / filename
    return download_file(asset_url, dest_path, on_progress=on_progress)


def download_and_open_update_asset(
    *,
    asset_url: str,
    cache_dir: Path,
    on_progress=None,
) -> Path:
    """Download the asset and open it with the OS handler."""
    downloaded = download_update_asset(asset_url=asset_url, cache_dir=cache_dir, on_progress=on_progress)
    open_file_in_os(downloaded)
    return downloaded
