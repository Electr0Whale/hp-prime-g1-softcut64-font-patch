#!/usr/bin/env python3
"""
HP Prime G1 20250915 softcut font patch helper.

This script does not contain or download HP firmware.  It operates only on a
local official firmware directory supplied by the user.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import struct
from pathlib import Path
from typing import Iterable


FAT_BASE = 0x2000
ARMFIR_PATH = "programs/misc/armfir.elf"
ARMFIR_DAT_PATH = "programs/misc/armfir.dat"

EXPECTED_20250915 = {
    "prime_app_md5": "663d1f7e4d4279286387f9c29e688f78",
    "armfir_elf_md5": "9e1ed504c294e70ff478e0bd5553c441",
    "armfir_elf_size": 8230724,
}

NORMAL_BRANCH_VA = 0x308DB944
NORMAL_BRANCH_FILE = 0x2DB978
INVERT_BRANCH_VA = 0x308DB940
INVERT_BRANCH_FILE = 0x2DB974
CONTINUE_VA = 0x308DB94C

NORMAL_STUB_VA = 0x30C3A5F4
NORMAL_STUB_FILE = 0x63A628
INVERT_STUB_VA = 0x30C3A608
INVERT_STUB_FILE = 0x63A63C


def md5_bytes(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_hex(value: str) -> bytes:
    return bytes.fromhex(value.replace(" ", "").replace("\n", ""))


def arm_word(value: int) -> bytes:
    return struct.pack("<I", value & 0xFFFFFFFF)


def arm_b(src_va: int, dst_va: int) -> bytes:
    offset_words = (dst_va - (src_va + 8)) >> 2
    if offset_words < -0x800000 or offset_words > 0x7FFFFF:
        raise ValueError(f"ARM branch from 0x{src_va:x} to 0x{dst_va:x} out of range")
    return arm_word(0xEA000000 | (offset_words & 0x00FFFFFF))


def cmp_r0_imm(imm: int) -> bytes:
    if imm < 0 or imm > 0xFF:
        raise ValueError("Only simple 8-bit ARM immediates are supported")
    return arm_word(0xE3500000 | imm)


def normal_stub(cutoff: int) -> bytes:
    return b"".join(
        [
            arm_word(0xE3500C01),  # cmp r0,#0x100
            arm_word(0xA3A000FF),  # movge r0,#0xff
            cmp_r0_imm(cutoff),  # cmp r0,#cutoff
            arm_word(0x33A00000),  # movlo r0,#0
            arm_b(NORMAL_STUB_VA + 16, CONTINUE_VA),
        ]
    )


def invert_stub(cutoff: int) -> bytes:
    return b"".join(
        [
            cmp_r0_imm(cutoff),
            arm_word(0x33A00000),  # movlo r0,#0
            arm_b(INVERT_STUB_VA + 8, CONTINUE_VA),
        ]
    )


class Fat16:
    def __init__(self, image: bytes, base: int = FAT_BASE):
        self.image = image
        self.base = base
        bs = image[base : base + 512]
        self.bytes_per_sector = struct.unpack_from("<H", bs, 11)[0]
        self.sectors_per_cluster = bs[13]
        self.reserved_sectors = struct.unpack_from("<H", bs, 14)[0]
        self.num_fats = bs[16]
        self.root_entries = struct.unpack_from("<H", bs, 17)[0]
        self.fat_sectors = struct.unpack_from("<H", bs, 22)[0]
        root_sectors = ((self.root_entries * 32) + (self.bytes_per_sector - 1)) // self.bytes_per_sector
        self.cluster_size = self.bytes_per_sector * self.sectors_per_cluster
        self.fat_offset = base + self.reserved_sectors * self.bytes_per_sector
        self.root_offset = base + (self.reserved_sectors + self.num_fats * self.fat_sectors) * self.bytes_per_sector
        self.data_offset = self.root_offset + root_sectors * self.bytes_per_sector

    def cluster_offset(self, cluster: int) -> int:
        return self.data_offset + (cluster - 2) * self.cluster_size

    def next_cluster(self, cluster: int) -> int:
        return struct.unpack_from("<H", self.image, self.fat_offset + cluster * 2)[0]

    def chain(self, cluster: int) -> Iterable[int]:
        seen: set[int] = set()
        while 2 <= cluster < 0xFFF8:
            if cluster in seen:
                raise ValueError(f"FAT loop at cluster {cluster}")
            seen.add(cluster)
            yield cluster
            cluster = self.next_cluster(cluster)

    @staticmethod
    def _short_name(entry: bytes) -> str:
        name = entry[:8].decode("ascii", "replace").rstrip()
        ext = entry[8:11].decode("ascii", "replace").rstrip()
        return name + (("." + ext) if ext else "")

    @staticmethod
    def _lfn_part(entry: bytes) -> str:
        raw = entry[1:11] + entry[14:26] + entry[28:32]
        return raw.decode("utf-16le", "replace").rstrip("\uffff\x00")

    def _parse_dir(self, raw: bytes) -> list[dict]:
        entries: list[dict] = []
        lfn: list[str] = []
        for i in range(0, len(raw), 32):
            entry = raw[i : i + 32]
            if len(entry) < 32 or entry[0] == 0:
                break
            if entry[0] == 0xE5:
                lfn = []
                continue
            attr = entry[11]
            if attr == 0x0F:
                lfn.append(self._lfn_part(entry))
                continue
            name = "".join(reversed(lfn)) if lfn else self._short_name(entry)
            lfn = []
            if attr & 0x08:
                continue
            cluster = struct.unpack_from("<H", entry, 26)[0]
            size = struct.unpack_from("<I", entry, 28)[0]
            entries.append({"name": name, "attr": attr, "cluster": cluster, "size": size})
        return entries

    def root_entries_list(self) -> list[dict]:
        raw = self.image[self.root_offset : self.root_offset + self.root_entries * 32]
        return self._parse_dir(raw)

    def dir_entries(self, cluster: int) -> list[dict]:
        raw = b"".join(
            self.image[self.cluster_offset(c) : self.cluster_offset(c) + self.cluster_size]
            for c in self.chain(cluster)
        )
        return self._parse_dir(raw)

    def walk(self) -> dict[str, dict]:
        out: dict[str, dict] = {}

        def rec(prefix: str, entries: list[dict]) -> None:
            for entry in entries:
                name = entry["name"]
                if name in (".", ".."):
                    continue
                path = f"{prefix}/{name}".strip("/")
                if entry["attr"] & 0x10:
                    out[path] = {**entry, "type": "dir"}
                    rec(path, self.dir_entries(entry["cluster"]))
                else:
                    out[path] = {**entry, "type": "file", "offset": self.cluster_offset(entry["cluster"])}

        rec("", self.root_entries_list())
        return out

    def read_file(self, cluster: int, size: int) -> bytes:
        if cluster == 0:
            return b""
        return b"".join(
            self.image[self.cluster_offset(c) : self.cluster_offset(c) + self.cluster_size]
            for c in self.chain(cluster)
        )[:size]

    def write_file_same_size(self, image: bytearray, cluster: int, old_size: int, content: bytes) -> None:
        if len(content) != old_size:
            raise ValueError(f"Size mismatch: {len(content)} != {old_size}")
        written = 0
        for c in self.chain(cluster):
            off = self.cluster_offset(c)
            chunk = content[written : written + self.cluster_size]
            image[off : off + len(chunk)] = chunk
            written += len(chunk)
            if written >= len(content):
                return
        raise ValueError("Cluster chain ended before content was fully written")


def plausible_sfnt(data: bytes, offset: int) -> list[dict] | None:
    if data[offset : offset + 4] not in (b"\x00\x01\x00\x00", b"OTTO"):
        return None
    if offset + 12 > len(data):
        return None
    table_count = struct.unpack_from(">H", data, offset + 4)[0]
    if not 1 <= table_count <= 64:
        return None
    if offset + 12 + table_count * 16 > len(data):
        return None
    known = {
        b"FFTM",
        b"OS/2",
        b"cmap",
        b"cvt ",
        b"fpgm",
        b"gasp",
        b"glyf",
        b"head",
        b"hhea",
        b"hmtx",
        b"kern",
        b"loca",
        b"maxp",
        b"name",
        b"post",
        b"prep",
        b"vhea",
        b"vmtx",
        b"CFF ",
    }
    records = []
    score = 0
    for idx in range(table_count):
        rec = offset + 12 + idx * 16
        tag = data[rec : rec + 4]
        if any(c < 32 or c > 126 for c in tag):
            return None
        checksum, table_offset, size = struct.unpack_from(">III", data, rec + 4)
        if table_offset + size > len(data):
            return None
        if tag in known:
            score += 1
        records.append(
            {
                "tag": tag.decode("ascii", "replace"),
                "checksum": checksum,
                "offset": table_offset,
                "size": size,
            }
        )
    tags = {r["tag"] for r in records}
    if score >= 5 and "head" in tags and "cmap" in tags:
        return records
    return None


def find_sfnts(data: bytes) -> list[dict]:
    found: list[dict] = []
    seen: set[int] = set()
    for sig in (b"\x00\x01\x00\x00", b"OTTO"):
        pos = 0
        while True:
            pos = data.find(sig, pos)
            if pos < 0:
                break
            if pos not in seen:
                records = plausible_sfnt(data, pos)
                if records:
                    size = max(r["offset"] + r["size"] for r in records)
                    found.append({"offset": pos, "size": size, "tables": records})
                    seen.add(pos)
            pos += 1
    return sorted(found, key=lambda x: x["offset"])


def load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    patch_sets = manifest.get("patch_sets")
    if not isinstance(patch_sets, list) or len(patch_sets) != 1:
        raise ValueError(f"{path} must contain exactly one patch set")
    return manifest


def extract_assets(firmware_dir: Path, work_dir: Path) -> dict:
    prime_app = firmware_dir / "PRIME_APP.DAT"
    if not prime_app.exists():
        raise FileNotFoundError(prime_app)
    out = work_dir / "extracted"
    fonts_out = out / "fonts"
    out.mkdir(parents=True, exist_ok=True)
    fonts_out.mkdir(parents=True, exist_ok=True)

    image = prime_app.read_bytes()
    fat = Fat16(image)
    files = fat.walk()
    manifest = {
        "source": {
            "firmware_dir": str(firmware_dir),
            "prime_app": str(prime_app),
            "prime_app_md5": md5_bytes(image),
            "fat_base": FAT_BASE,
        },
        "fat16": {
            "bytes_per_sector": fat.bytes_per_sector,
            "sectors_per_cluster": fat.sectors_per_cluster,
            "cluster_size": fat.cluster_size,
            "fat_offset": fat.fat_offset,
            "root_offset": fat.root_offset,
            "data_offset": fat.data_offset,
        },
        "files": {},
        "embedded_fonts": [],
    }

    for inner, target in {
        ARMFIR_PATH: out / "armfir.elf",
        ARMFIR_DAT_PATH: out / "armfir.dat",
    }.items():
        meta = files[inner]
        content = fat.read_file(meta["cluster"], meta["size"])
        target.write_bytes(content)
        manifest["files"][inner] = {
            "offset": meta["offset"],
            "size": meta["size"],
            "md5": md5_bytes(content),
            "extracted_to": str(target),
        }

    armfir_dat = (out / "armfir.dat").read_bytes()
    font_names = ["PrimeSansBold.ttf", "PrimeSansFull.ttf", "PrimeSansMono.ttf"]
    for idx, sfnt in enumerate(find_sfnts(armfir_dat)):
        name = font_names[idx] if idx < len(font_names) else f"font_{idx}.ttf"
        content = armfir_dat[sfnt["offset"] : sfnt["offset"] + sfnt["size"]]
        target = fonts_out / name
        target.write_bytes(content)
        manifest["embedded_fonts"].append(
            {
                "name": name,
                "armfir_dat_offset": sfnt["offset"],
                "prime_app_offset": manifest["files"][ARMFIR_DAT_PATH]["offset"] + sfnt["offset"],
                "size": sfnt["size"],
                "md5": md5_bytes(content),
                "tables": [r["tag"] for r in sfnt["tables"]],
                "extracted_to": str(target),
            }
        )

    manifest_path = out / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def generate_softcut_manifest(work_dir: Path, cutoff: int) -> Path:
    if cutoff < 1 or cutoff > 255:
        raise ValueError("cutoff must be in 1..255")
    source = work_dir / "extracted" / "armfir.elf"
    if not source.exists():
        raise FileNotFoundError(source)
    data = source.read_bytes()

    normal = normal_stub(cutoff)
    invert = invert_stub(cutoff)
    for off, stub in ((NORMAL_STUB_FILE, normal), (INVERT_STUB_FILE, invert)):
        if data[off : off + len(stub)] != b"\0" * len(stub):
            raise ValueError(f"stub cave at 0x{off:x} is not zero-filled")

    patched_dir = work_dir / "patched"
    patched_dir.mkdir(parents=True, exist_ok=True)
    output = patched_dir / f"armfir.softcut{cutoff}.elf"
    manifest = {
        "patch_sets": [
            {
                "source": str(source),
                "output": str(output),
                "source_md5": md5_bytes(data),
                "patches": [
                    {
                        "file_offset": f"0x{NORMAL_STUB_FILE:x}",
                        "virtual_address": f"0x{NORMAL_STUB_VA:x}",
                        "old": data[NORMAL_STUB_FILE : NORMAL_STUB_FILE + len(normal)].hex(),
                        "new": normal.hex(),
                        "semantic": (
                            f"ARM softcut{cutoff} normal-coverage stub: clamp r0 >=256 to 255, "
                            f"zero r0 <{cutoff}, then return to gray_hline shared callback/bitmap path."
                        ),
                    },
                    {
                        "file_offset": f"0x{INVERT_STUB_FILE:x}",
                        "virtual_address": f"0x{INVERT_STUB_VA:x}",
                        "old": data[INVERT_STUB_FILE : INVERT_STUB_FILE + len(invert)].hex(),
                        "new": invert.hex(),
                        "semantic": (
                            f"ARM softcut{cutoff} inverted-coverage stub: zero r0 <{cutoff}, "
                            "then return to gray_hline shared callback/bitmap path."
                        ),
                    },
                    {
                        "file_offset": f"0x{INVERT_BRANCH_FILE:x}",
                        "virtual_address": f"0x{INVERT_BRANCH_VA:x}",
                        "old": data[INVERT_BRANCH_FILE : INVERT_BRANCH_FILE + 4].hex(),
                        "new": arm_b(INVERT_BRANCH_VA, INVERT_STUB_VA).hex(),
                        "semantic": f"Redirect inverted gray_hline coverage continuation to ARM softcut{cutoff} stub.",
                    },
                    {
                        "file_offset": f"0x{NORMAL_BRANCH_FILE:x}",
                        "virtual_address": f"0x{NORMAL_BRANCH_VA:x}",
                        "old": data[NORMAL_BRANCH_FILE : NORMAL_BRANCH_FILE + 4].hex(),
                        "new": arm_b(NORMAL_BRANCH_VA, NORMAL_STUB_VA).hex(),
                        "semantic": (
                            f"Redirect normal gray_hline coverage clamp to ARM softcut{cutoff} stub. "
                            "The original movge at the following instruction becomes skipped dead code."
                        ),
                    },
                ],
            }
        ]
    }
    path = patched_dir / f"patch_manifest.arm_softcut{cutoff}.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def apply_manifest(manifest_path: Path) -> dict:
    manifest = load_manifest(manifest_path)
    patch_set = manifest["patch_sets"][0]
    source = Path(patch_set["source"])
    output = Path(patch_set["output"])
    original = source.read_bytes()
    if md5_bytes(original).lower() != patch_set["source_md5"].lower():
        raise ValueError(f"source MD5 mismatch for {source}")
    patched = bytearray(original)
    results = []
    for patch in patch_set["patches"]:
        off = int(patch["file_offset"], 0) if isinstance(patch["file_offset"], str) else patch["file_offset"]
        old = parse_hex(patch["old"])
        new = parse_hex(patch["new"])
        if len(old) != len(new):
            raise ValueError(f"patch at 0x{off:x} changes length")
        actual = bytes(original[off : off + len(old)])
        if actual != old:
            raise ValueError(f"old bytes mismatch at 0x{off:x}: {actual.hex()} != {old.hex()}")
        patched[off : off + len(new)] = new
        results.append({"file_offset": patch["file_offset"], "old": old.hex(), "new": new.hex()})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(patched)
    result = {
        "source": str(source),
        "output": str(output),
        "source_md5": md5_bytes(original),
        "output_md5": md5_bytes(patched),
        "patch_count": len(results),
        "patches": results,
    }
    result_path = manifest_path.with_suffix(".apply_results.json")
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def update_appslists_md5(image: bytearray, fat: Fat16, files: dict, new_arm_md5: str) -> dict:
    meta = files.get("APPSLIST.MD5")
    if not meta:
        return {"updated": False, "reason": "APPSLIST.MD5 not found"}
    old = fat.read_file(meta["cluster"], meta["size"])
    text = old.decode("ascii", "replace")
    replaced = re.sub(
        r"[0-9a-fA-F]{32}(\s+\*?[\\/]?programs[\\/]misc[\\/]armfir\.elf)",
        new_arm_md5 + r"\1",
        text,
        flags=re.IGNORECASE,
    )
    if replaced == text:
        replaced = re.sub(
            r"[0-9a-fA-F]{32}(\s+\*?armfir\.elf)",
            new_arm_md5 + r"\1",
            text,
            flags=re.IGNORECASE,
        )
    if replaced == text:
        return {"updated": False, "reason": "armfir.elf entry not found in APPSLIST.MD5"}
    encoded = replaced.encode("ascii")
    if len(encoded) != meta["size"]:
        return {"updated": False, "reason": "APPSLIST.MD5 size would change"}
    fat.write_file_same_size(image, meta["cluster"], meta["size"], encoded)
    return {"updated": True, "old_md5_file_md5": md5_bytes(old), "new_md5_file_md5": md5_bytes(encoded)}


def update_outer_md5(source_md5: Path, app_md5: str, out_md5: Path) -> None:
    text = source_md5.read_text(encoding="ascii", errors="replace")
    replaced = re.sub(
        r"[0-9a-fA-F]{32}(\s+\*?PRIME_APP\.DAT)",
        app_md5 + r"\1",
        text,
        count=1,
    )
    if replaced == text:
        raise ValueError("PRIME_APP.DAT entry not found in outer md5 file")
    out_md5.write_text(replaced, encoding="ascii")


def repack_prime_app(firmware_dir: Path, work_dir: Path, cutoff: int) -> dict:
    patched_elf = work_dir / "patched" / f"armfir.softcut{cutoff}.elf"
    if not patched_elf.exists():
        raise FileNotFoundError(patched_elf)
    source_app = firmware_dir / "PRIME_APP.DAT"
    source_md5 = firmware_dir / "Prime_FW.md5"
    if not source_app.exists():
        raise FileNotFoundError(source_app)
    if not source_md5.exists():
        raise FileNotFoundError(source_md5)

    out_dir = work_dir / "patched_firmware"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_app = out_dir / f"PRIME_APP.softcut{cutoff}_poc.DAT"
    out_md5 = out_dir / f"Prime_FW.softcut{cutoff}_poc.md5"
    report_path = out_dir / f"repack_report.softcut{cutoff}.json"

    image = bytearray(source_app.read_bytes())
    fat = Fat16(image)
    files = fat.walk()
    arm = files[ARMFIR_PATH]
    patched = patched_elf.read_bytes()
    original = fat.read_file(arm["cluster"], arm["size"])
    if len(patched) != arm["size"]:
        raise ValueError(f"patched armfir.elf size mismatch: {len(patched)} != {arm['size']}")
    if patched[:4] != b"\x7fELF":
        raise ValueError("patched armfir.elf is not an ELF file")
    fat.write_file_same_size(image, arm["cluster"], arm["size"], patched)
    appslists = update_appslists_md5(image, fat, files, md5_bytes(patched))
    out_app.write_bytes(image)
    app_md5 = md5_bytes(image)
    update_outer_md5(source_md5, app_md5, out_md5)
    report = {
        "source_prime_app": str(source_app),
        "output_prime_app": str(out_app),
        "source_prime_app_md5": md5_bytes(source_app.read_bytes()),
        "output_prime_app_md5": app_md5,
        "armfir": {
            "path": ARMFIR_PATH,
            "offset": arm["offset"],
            "size": arm["size"],
            "old_md5": md5_bytes(original),
            "new_md5": md5_bytes(patched),
        },
        "appslists_md5": appslists,
        "outer_md5": str(out_md5),
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def verify_outputs(firmware_dir: Path, work_dir: Path, cutoff: int) -> dict:
    failures: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    source_elf = work_dir / "extracted" / "armfir.elf"
    manifest_path = work_dir / "patched" / f"patch_manifest.arm_softcut{cutoff}.json"
    patched_elf = work_dir / "patched" / f"armfir.softcut{cutoff}.elf"
    app = work_dir / "patched_firmware" / f"PRIME_APP.softcut{cutoff}_poc.DAT"
    outer_md5 = work_dir / "patched_firmware" / f"Prime_FW.softcut{cutoff}_poc.md5"
    original_app = firmware_dir / "PRIME_APP.DAT"

    for path in (source_elf, manifest_path, patched_elf, app, outer_md5, original_app):
        check(path.exists(), f"missing {path}")
    if failures:
        return {"ok": False, "failures": failures}

    original = source_elf.read_bytes()
    patched = patched_elf.read_bytes()
    manifest = load_manifest(manifest_path)
    patch_set = manifest["patch_sets"][0]
    check(md5_bytes(original).lower() == patch_set["source_md5"].lower(), "manifest source MD5 mismatch")
    check(len(original) == len(patched), "patched ELF size changed")
    check(patched[:4] == b"\x7fELF", "patched ELF missing ELF magic")

    expected = bytearray(original)
    for patch in patch_set["patches"]:
        off = int(patch["file_offset"], 0) if isinstance(patch["file_offset"], str) else patch["file_offset"]
        old = parse_hex(patch["old"])
        new = parse_hex(patch["new"])
        check(bytes(original[off : off + len(old)]) == old, f"old bytes mismatch at 0x{off:x}")
        expected[off : off + len(old)] = new
    check(bytes(expected) == patched, "patched ELF differs outside manifest patches")

    image = app.read_bytes()
    check(len(image) == len(original_app.read_bytes()), "PRIME_APP size changed")
    fat = Fat16(image)
    files = fat.walk()
    arm = files.get(ARMFIR_PATH)
    check(arm is not None, f"FAT missing {ARMFIR_PATH}")
    if arm:
        embedded = fat.read_file(arm["cluster"], arm["size"])
        check(embedded == patched, "embedded armfir.elf does not match patched ELF")

    appslists = files.get("APPSLIST.MD5")
    check(appslists is not None, "FAT missing APPSLIST.MD5")
    if appslists:
        text = fat.read_file(appslists["cluster"], appslists["size"]).decode("ascii", "replace")
        arm_lines = [line for line in text.splitlines() if "armfir.elf" in line.lower()]
        check(any(line.lower().startswith(md5_bytes(patched)) for line in arm_lines), "APPSLIST.MD5 does not match patched ELF")

    outer_text = outer_md5.read_text(encoding="ascii", errors="replace")
    match = re.search(r"([0-9a-fA-F]{32})(\s+\*?PRIME_APP\.DAT)", outer_text)
    check(match is not None, "outer MD5 missing PRIME_APP.DAT line")
    if match:
        check(match.group(1).lower() == md5_bytes(image), "outer MD5 does not match patched PRIME_APP")

    result = {
        "ok": not failures,
        "failures": failures,
        "cutoff": cutoff,
        "patched_elf_md5": md5_bytes(patched),
        "patched_prime_app_md5": md5_bytes(image),
    }
    out = work_dir / "patched" / f"softcut{cutoff}_verification.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def make_flash_package(firmware_dir: Path, work_dir: Path, cutoff: int, out_dir: Path) -> dict:
    patched_app = work_dir / "patched_firmware" / f"PRIME_APP.softcut{cutoff}_poc.DAT"
    patched_md5 = work_dir / "patched_firmware" / f"Prime_FW.softcut{cutoff}_poc.md5"
    if not patched_app.exists():
        raise FileNotFoundError(patched_app)
    if not patched_md5.exists():
        raise FileNotFoundError(patched_md5)
    out_dir.mkdir(parents=True, exist_ok=True)

    for src in firmware_dir.iterdir():
        if not src.is_file():
            continue
        name_upper = src.name.upper()
        if name_upper in {"PRIME_APP.DAT", "PRIME_FW.MD5"}:
            continue
        shutil.copy2(src, out_dir / src.name)
    shutil.copy2(patched_app, out_dir / "PRIME_APP.DAT")
    shutil.copy2(patched_md5, out_dir / "Prime_FW.md5")

    report = {
        "out_dir": str(out_dir),
        "prime_app_md5": md5_file(out_dir / "PRIME_APP.DAT"),
        "prime_fw_md5_file": str(out_dir / "Prime_FW.md5"),
        "files": sorted(p.name for p in out_dir.iterdir() if p.is_file()),
    }
    (out_dir / f"flash_package.softcut{cutoff}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def run_all(args: argparse.Namespace) -> None:
    extract_assets(args.firmware_dir, args.work_dir)
    manifest = generate_softcut_manifest(args.work_dir, args.cutoff)
    apply_manifest(manifest)
    repack_prime_app(args.firmware_dir, args.work_dir, args.cutoff)
    result = verify_outputs(args.firmware_dir, args.work_dir, args.cutoff)
    if not result["ok"]:
        raise SystemExit(json.dumps(result, indent=2))
    if args.flash_out:
        make_flash_package(args.firmware_dir, args.work_dir, args.cutoff, args.flash_out)
    print(json.dumps(result, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Patch HP Prime G1 20250915 font rendering with softcut coverage.")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--firmware-dir", type=Path, required=True, help="Directory containing official PRIME_APP.DAT, PRIME_MASTER.DAT, PRIME_OS.ROM, Prime_FW.md5")
        p.add_argument("--work-dir", type=Path, required=True, help="Output work directory; generated binaries stay here and should not be committed")
        p.add_argument("--cutoff", type=int, default=64, help="softcut threshold, default 64")

    p = sub.add_parser("extract", help="Extract armfir.elf, armfir.dat, and embedded fonts from official PRIME_APP.DAT")
    p.add_argument("--firmware-dir", type=Path, required=True)
    p.add_argument("--work-dir", type=Path, required=True)

    p = sub.add_parser("generate-softcut", help="Generate ARM softcut patch manifest")
    p.add_argument("--work-dir", type=Path, required=True)
    p.add_argument("--cutoff", type=int, default=64)

    p = sub.add_parser("apply", help="Apply a binary patch manifest")
    p.add_argument("--manifest", type=Path, required=True)

    p = sub.add_parser("repack", help="Repack patched armfir.elf into PRIME_APP.DAT")
    add_common(p)

    p = sub.add_parser("verify", help="Verify patched ELF, FAT image, APPSLIST.MD5, and outer Prime_FW.md5")
    add_common(p)

    p = sub.add_parser("make-flash-package", help="Create a local flash package directory with official names")
    add_common(p)
    p.add_argument("--out-dir", type=Path, required=True)

    p = sub.add_parser("all", help="Run extract, manifest generation, apply, repack, verify, and optional flash package")
    add_common(p)
    p.add_argument("--flash-out", type=Path)

    args = parser.parse_args()
    if args.command == "extract":
        print(json.dumps(extract_assets(args.firmware_dir, args.work_dir), indent=2))
    elif args.command == "generate-softcut":
        print(generate_softcut_manifest(args.work_dir, args.cutoff))
    elif args.command == "apply":
        print(json.dumps(apply_manifest(args.manifest), indent=2))
    elif args.command == "repack":
        print(json.dumps(repack_prime_app(args.firmware_dir, args.work_dir, args.cutoff), indent=2))
    elif args.command == "verify":
        result = verify_outputs(args.firmware_dir, args.work_dir, args.cutoff)
        print(json.dumps(result, indent=2))
        if not result["ok"]:
            raise SystemExit(1)
    elif args.command == "make-flash-package":
        print(json.dumps(make_flash_package(args.firmware_dir, args.work_dir, args.cutoff, args.out_dir), indent=2))
    elif args.command == "all":
        run_all(args)


if __name__ == "__main__":
    main()

