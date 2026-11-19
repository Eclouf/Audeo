"""Fonctions de formatage partagées (tailles, vitesses, ETA)."""

from __future__ import annotations

import math
from typing import Optional


def fmt_bytes(n: Optional[float]) -> str:
    if n is None:
        return "-"
    if n <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = min(int(math.log(n, 1024)), len(units) - 1)
    v = n / (1024**i)
    return f"{v:.1f} {units[i]}"


def fmt_eta(seconds: Optional[float]) -> str:
    if seconds is None:
        return "-"
    m, s = divmod(max(0, int(seconds)), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:d}:{s:02d}"


def fmt_speed(n: Optional[float]) -> str:
    if n is None:
        return "-"
    if n <= 0:
        return "0 B/s"
    units = ["B/s", "KB/s", "MB/s", "GB/s"]
    i = 0
    v = float(n)
    while v >= 1024.0 and i < len(units) - 1:
        v /= 1024.0
        i += 1
    return f"{v:.2f} {units[i]}"
