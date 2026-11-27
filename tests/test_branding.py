"""Validate integration branding files and documentation references."""
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]
ICON = ROOT / "custom_components/wetsoil/brand/icon.png"
ROOT_LOGO = ROOT / "wetsoil-logo.png"
DOC_LOGO = ROOT / "docs/wetsoil-logo.png"


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data.startswith(b"\x89PNG\r\n\x1a\n"), f"Invalid PNG signature: {path}"
    cursor = 8
    dimensions = None
    ended = False
    while cursor < len(data):
        assert cursor + 12 <= len(data), f"Truncated PNG chunk: {path}"
        length = int.from_bytes(data[cursor:cursor + 4], "big")
        kind = data[cursor + 4:cursor + 8]
        end = cursor + 12 + length
        assert end <= len(data), f"Truncated PNG payload: {path}"
        chunk = data[cursor + 8:cursor + 8 + length]
        actual_crc = int.from_bytes(data[cursor + 8 + length:end], "big")
        assert zlib.crc32(kind + chunk) == actual_crc, f"Corrupted PNG chunk: {path}"
        if kind == b"IHDR":
            assert length == 13
            dimensions = struct.unpack(">II", chunk[:8])
        if kind == b"IEND":
            ended = True
            assert end == len(data), f"Unexpected trailing bytes: {path}"
            break
        cursor = end
    assert ended and dimensions is not None, f"Incomplete PNG: {path}"
    return dimensions


def test_branding_pngs_are_valid_and_consistent():
    assert png_dimensions(ICON) == (128, 128)
    # The redundant root-level logo was intentionally removed after 0.1.2.
    assert not ROOT_LOGO.exists(), "Duplicate logo in repository root"
    width, height = png_dimensions(DOC_LOGO)
    assert width == height and width >= 512


def test_english_and_german_documentation_use_high_resolution_logo():
    english = (ROOT / "README.md").read_text(encoding="utf-8")
    german = (ROOT / "docs/README.de.md").read_text(encoding="utf-8")
    assert 'src="docs/wetsoil-logo.png"' in english
    assert 'src="wetsoil-logo.png"' in german
    assert "0.1.2" in english and "0.1.2" in german


def test_release_version_and_notes_are_consistent():
    import json
    manifest = json.loads((ROOT / "custom_components/wetsoil/manifest.json").read_text())
    assert manifest["version"] == "0.1.2"
    assert (ROOT / "RELEASE_NOTES_0.1.2.md").is_file()
