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
    assert "0.1.3" in english and "0.1.3" in german


def test_release_version_and_notes_are_consistent():
    import json
    manifest = json.loads((ROOT / "custom_components/wetsoil/manifest.json").read_text())
    assert manifest["version"] == "0.1.3"
    assert (ROOT / "RELEASE_NOTES_0.1.3.md").is_file()



def png_transparency(path: Path) -> tuple[bool, bool]:
    """Check actual pixels, not just the presence of an unused alpha channel.

    Decode ordinary non-interlaced PNG scanlines with Python's standard
    library. This makes the branding test independent of Pillow availability.
    """
    data = path.read_bytes()
    chunks = []
    position = 8
    while position < len(data):
        size = int.from_bytes(data[position:position + 4], "big")
        kind = data[position + 4:position + 8]
        payload = data[position + 8:position + 8 + size]
        chunks.append((kind, payload))
        position += size + 12
        if kind == b"IEND":
            break

    ihdr = next(body for kind, body in chunks if kind == b"IHDR")
    width, height, depth, colour, compression, filtering, interlace = struct.unpack(
        ">IIBBBBB", ihdr
    )
    assert depth == 8 and interlace == 0, (
        f"Unsupported PNG pixel layout for transparency validation: {path}"
    )
    assert compression == filtering == 0
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[colour]
    stride = width * channels
    trns = next((body for kind, body in chunks if kind == b"tRNS"), b"")
    pixels = zlib.decompress(b"".join(
        body for kind, body in chunks if kind == b"IDAT"
    ))
    previous = bytearray(stride)
    offset = 0
    transparent = False
    opaque = False
    for _ in range(height):
        mode = pixels[offset]
        offset += 1
        row = bytearray(pixels[offset:offset + stride])
        assert len(row) == stride
        offset += stride
        assert mode in range(5), f"Invalid PNG filter for {path}"
        for i in range(stride):
            left = row[i - channels] if i >= channels else 0
            above = previous[i]
            upper_left = previous[i - channels] if i >= channels else 0
            if mode == 1:
                prediction = left
            elif mode == 2:
                prediction = above
            elif mode == 3:
                prediction = (left + above) // 2
            elif mode == 4:
                p = left + above - upper_left
                distances = (abs(p - left), abs(p - above), abs(p - upper_left))
                prediction = (left, above, upper_left)[distances.index(min(distances))]
            else:
                prediction = 0
            row[i] = (row[i] + prediction) & 255
        previous = row
        if colour in (4, 6):
            alphas = row[channels - 1::channels]
            transparent |= any(value < 255 for value in alphas)
            opaque |= any(value == 255 for value in alphas)
        elif colour == 3:
            alphas = (trns[index] if index < len(trns) else 255 for index in row)
            for value in alphas:
                transparent |= value < 255
                opaque |= value == 255
        elif colour == 2 and len(trns) == 6:
            key = struct.unpack(">HHH", trns)
            for i in range(0, stride, 3):
                is_clear = tuple(row[i:i + 3]) == key
                transparent |= is_clear
                opaque |= not is_clear
        elif colour == 0 and len(trns) == 2:
            key = int.from_bytes(trns, "big")
            transparent |= any(value == key for value in row)
            opaque |= any(value != key for value in row)
        else:
            opaque = True
        if transparent and opaque:
            break
    return transparent, opaque


def test_branding_contains_transparent_background_and_visible_artwork():
    for path in (ICON, DOC_LOGO):
        transparent, opaque = png_transparency(path)
        assert transparent, f"No transparent pixels in logo: {path}"
        assert opaque, f"No opaque artwork in logo: {path}"
