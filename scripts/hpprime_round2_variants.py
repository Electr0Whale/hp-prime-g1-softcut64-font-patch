#!/usr/bin/env python3
"""
Round2/Round3 HP Prime G1 font coverage variants.

This companion script builds on hpprime_softcut64.py.  It generates, applies,
repacks, and verifies formula and LUT coverage-output variants without changing
the FreeType bitmap format.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from hpprime_softcut64 import (
    ARMFIR_PATH,
    FAT_BASE,
    INVERT_BRANCH_FILE,
    INVERT_BRANCH_VA,
    NORMAL_BRANCH_FILE,
    NORMAL_BRANCH_VA,
    CONTINUE_VA,
    Fat16,
    apply_manifest,
    arm_b,
    arm_word,
    cmp_r0_imm,
    extract_assets,
    load_manifest,
    md5_bytes,
    parse_hex,
    update_appslists_md5,
    update_outer_md5,
)


NORMAL_STUB_VA = 0x30C3A5F4
NORMAL_STUB_FILE = 0x63A628

SOFTCUT_INVERT_STUB_VA = 0x30C3A608
SOFTCUT_INVERT_STUB_FILE = 0x63A63C

SOFTBAND_INVERT_STUB_VA = 0x30C3A620
SOFTBAND_INVERT_STUB_FILE = 0x63A654

BOOST_INVERT_STUB_VA = 0x30C3A654
BOOST_INVERT_STUB_FILE = 0x63A688

LUT_INVERT_STUB_VA = 0x30C3A608
LUT_INVERT_STUB_FILE = 0x63A63C
LUT_VA = 0x30C3A700
LUT_FILE = 0x63A734


@dataclass(frozen=True)
class Variant:
    name: str
    kind: str
    low: int
    high: int | None = None
    shift: int | None = None
    lut_kind: str | None = None
    strength: int | None = None


def movhs_r0_imm(imm: int) -> bytes:
    if imm < 0 or imm > 0xFF:
        raise ValueError("Only 8-bit ARM immediates are supported")
    return arm_word(0x23A00000 | imm)


def addhs_r0_r0_lsr(shift: int) -> bytes:
    if shift < 1 or shift > 31:
        raise ValueError("shift must be 1..31")
    return arm_word(0x20800000 | (shift << 7) | 0x20)


def boost_percent_to_shift(percent: int) -> int:
    mapping = {150: 1, 125: 2, 112: 3, 106: 4}
    if percent not in mapping:
        raise ValueError(f"unsupported boost percent {percent}; supported: {sorted(mapping)}")
    return mapping[percent]


def boost_shift_to_percent(shift: int) -> int:
    return 100 + (100 >> shift)


def parse_variant(name: str) -> Variant:
    match = re.fullmatch(r"softcut(\d+)", name)
    if match:
        return Variant(name=name, kind="softcut", low=int(match.group(1)))

    match = re.fullmatch(r"softband(\d+)_(\d+)", name)
    if match:
        low = int(match.group(1))
        high = int(match.group(2))
        return Variant(name=name, kind="softband", low=low, high=high)

    match = re.fullmatch(r"boost(\d+)_(\d+)", name)
    if match:
        low = int(match.group(1))
        percent = int(match.group(2))
        return Variant(name=name, kind="boost", low=low, shift=boost_percent_to_shift(percent))

    match = re.fullmatch(r"lut(\d+)_(ease|contrast)(\d+)", name)
    if match:
        return Variant(
            name=name,
            kind="lut",
            low=int(match.group(1)),
            lut_kind=match.group(2),
            strength=int(match.group(3)),
        )

    raise ValueError(f"Unrecognized variant name: {name}")


def softcut_normal_stub(low: int) -> bytes:
    return b"".join(
        [
            arm_word(0xE3500C01),
            arm_word(0xA3A000FF),
            cmp_r0_imm(low),
            arm_word(0x33A00000),
            arm_b(NORMAL_STUB_VA + 16, CONTINUE_VA),
        ]
    )


def softcut_invert_stub(low: int) -> bytes:
    return b"".join(
        [
            cmp_r0_imm(low),
            arm_word(0x33A00000),
            arm_b(SOFTCUT_INVERT_STUB_VA + 8, CONTINUE_VA),
        ]
    )


def softband_normal_stub(low: int, high: int) -> bytes:
    return b"".join(
        [
            arm_word(0xE3500C01),
            arm_word(0xA3A000FF),
            cmp_r0_imm(low),
            arm_word(0x33A00000),
            cmp_r0_imm(high),
            movhs_r0_imm(0xFF),
            arm_b(NORMAL_STUB_VA + 24, CONTINUE_VA),
        ]
    )


def softband_invert_stub(low: int, high: int) -> bytes:
    return b"".join(
        [
            cmp_r0_imm(low),
            arm_word(0x33A00000),
            cmp_r0_imm(high),
            movhs_r0_imm(0xFF),
            arm_b(SOFTBAND_INVERT_STUB_VA + 16, CONTINUE_VA),
        ]
    )


def boost_normal_stub(low: int, shift: int) -> bytes:
    return b"".join(
        [
            arm_word(0xE3500C01),
            arm_word(0xA3A000FF),
            cmp_r0_imm(low),
            arm_word(0x33A00000),
            addhs_r0_r0_lsr(shift),
            arm_word(0xE3500C01),
            arm_word(0xA3A000FF),
            arm_b(NORMAL_STUB_VA + 28, CONTINUE_VA),
        ]
    )


def boost_invert_stub(low: int, shift: int) -> bytes:
    return b"".join(
        [
            cmp_r0_imm(low),
            arm_word(0x33A00000),
            addhs_r0_r0_lsr(shift),
            arm_word(0xE3500C01),
            arm_word(0xA3A000FF),
            arm_b(BOOST_INVERT_STUB_VA + 20, CONTINUE_VA),
        ]
    )


def add_r2_pc_imm(imm: int) -> bytes:
    if imm < 0 or imm > 0xFF:
        raise ValueError("this LUT helper only supports unrotated 8-bit immediates")
    return arm_word(0xE28F2000 | imm)


def ldrb_r0_r2_r0() -> bytes:
    return arm_word(0xE7D20000)


def lut_normal_stub() -> bytes:
    table_delta = LUT_VA - (NORMAL_STUB_VA + 16)
    return b"".join(
        [
            arm_word(0xE3500C01),
            arm_word(0xA3A000FF),
            add_r2_pc_imm(table_delta),
            ldrb_r0_r2_r0(),
            arm_b(NORMAL_STUB_VA + 16, CONTINUE_VA),
        ]
    )


def lut_invert_stub() -> bytes:
    table_delta = LUT_VA - (LUT_INVERT_STUB_VA + 16)
    return b"".join(
        [
            arm_word(0xE3500C01),
            arm_word(0xA3A000FF),
            add_r2_pc_imm(table_delta),
            ldrb_r0_r2_r0(),
            arm_b(LUT_INVERT_STUB_VA + 16, CONTINUE_VA),
        ]
    )


def ease_table(low: int, gamma_x100: int) -> bytes:
    if low < 0 or low > 254:
        raise ValueError("low must be 0..254")
    gamma = gamma_x100 / 100.0
    values = []
    for coverage in range(256):
        if coverage < low:
            out = 0
        else:
            t = (coverage - low) / (255 - low)
            out = round(255 * (1.0 - math.pow(1.0 - t, gamma)))
        values.append(max(0, min(255, out)))
    values[255] = 255
    return bytes(values)


def contrast_table(low: int, slope_x100: int, pivot: int = 128) -> bytes:
    if low < 0 or low > 254:
        raise ValueError("low must be 0..254")
    slope = slope_x100 / 100.0
    values = []
    for coverage in range(256):
        if coverage < low:
            out = 0
        else:
            out = round(pivot + slope * (coverage - pivot))
        values.append(max(0, min(255, out)))
    values[255] = 255
    return bytes(values)


def lut_table(variant: Variant) -> bytes:
    if variant.lut_kind is None or variant.strength is None:
        raise ValueError("LUT variant requires lut_kind and strength")
    if variant.lut_kind == "ease":
        return ease_table(variant.low, variant.strength)
    if variant.lut_kind == "contrast":
        return contrast_table(variant.low, variant.strength)
    raise ValueError(variant.lut_kind)


def variant_stubs(variant: Variant) -> tuple[int, int, bytes, bytes]:
    if variant.kind == "softcut":
        return (
            SOFTCUT_INVERT_STUB_FILE,
            SOFTCUT_INVERT_STUB_VA,
            softcut_normal_stub(variant.low),
            softcut_invert_stub(variant.low),
        )
    if variant.kind == "softband":
        if variant.high is None:
            raise ValueError("softband requires high cutoff")
        return (
            SOFTBAND_INVERT_STUB_FILE,
            SOFTBAND_INVERT_STUB_VA,
            softband_normal_stub(variant.low, variant.high),
            softband_invert_stub(variant.low, variant.high),
        )
    if variant.kind == "boost":
        if variant.shift is None:
            raise ValueError("boost requires shift")
        return (
            BOOST_INVERT_STUB_FILE,
            BOOST_INVERT_STUB_VA,
            boost_normal_stub(variant.low, variant.shift),
            boost_invert_stub(variant.low, variant.shift),
        )
    if variant.kind == "lut":
        return (
            LUT_INVERT_STUB_FILE,
            LUT_INVERT_STUB_VA,
            lut_normal_stub(),
            lut_invert_stub(),
        )
    raise ValueError(variant.kind)


def semantic(variant: Variant) -> str:
    if variant.kind == "softcut":
        return f"coverage = min(coverage, 255); if coverage < {variant.low}, set to 0."
    if variant.kind == "softband":
        return (
            f"coverage = min(coverage, 255); if coverage < {variant.low}, set to 0; "
            f"if coverage >= {variant.high}, set to 255."
        )
    if variant.kind == "boost":
        return (
            f"coverage = min(coverage, 255); if coverage < {variant.low}, set to 0; "
            f"otherwise coverage += coverage >> {variant.shift} "
            f"(about {boost_shift_to_percent(variant.shift or 1)}%), then saturate to 255."
        )
    if variant.kind == "lut":
        if variant.lut_kind == "ease":
            return (
                f"coverage = min(coverage, 255); table maps coverage < {variant.low} to 0; "
                f"surviving coverage uses ease curve strength {variant.strength / 100:.2f}."
            )
        if variant.lut_kind == "contrast":
            return (
                f"coverage = min(coverage, 255); table maps coverage < {variant.low} to 0; "
                f"surviving coverage uses contrast slope {variant.strength / 100:.2f} around pivot 128."
            )
    raise ValueError(variant.kind)


def generate_manifest(work_dir: Path, variant_name: str) -> Path:
    variant = parse_variant(variant_name)
    source = work_dir / "extracted" / "armfir.elf"
    if not source.exists():
        raise FileNotFoundError(source)

    data = source.read_bytes()
    invert_file, invert_va, normal, invert = variant_stubs(variant)
    for off, stub in ((NORMAL_STUB_FILE, normal), (invert_file, invert)):
        if data[off : off + len(stub)] != b"\0" * len(stub):
            raise ValueError(f"stub cave at 0x{off:x} is not zero-filled")
    extra_patches = []
    if variant.kind == "lut":
        table = lut_table(variant)
        if data[LUT_FILE : LUT_FILE + len(table)] != b"\0" * len(table):
            raise ValueError(f"LUT table area at 0x{LUT_FILE:x} is not zero-filled")
        extra_patches.append(
            {
                "file_offset": f"0x{LUT_FILE:x}",
                "virtual_address": f"0x{LUT_VA:x}",
                "old": data[LUT_FILE : LUT_FILE + len(table)].hex(),
                "new": table.hex(),
                "semantic": f"{variant.name} 256-byte 8-bit coverage lookup table.",
            }
        )

    patched_dir = work_dir / "patched"
    patched_dir.mkdir(parents=True, exist_ok=True)
    output = patched_dir / f"armfir.{variant.name}.elf"
    manifest = {
        "patch_sets": [
            {
                "source": str(source),
                "output": str(output),
                "source_md5": md5_bytes(data),
                "variant": variant.name,
                "semantic": semantic(variant),
                "patches": [
                    {
                        "file_offset": f"0x{NORMAL_STUB_FILE:x}",
                        "virtual_address": f"0x{NORMAL_STUB_VA:x}",
                        "old": data[NORMAL_STUB_FILE : NORMAL_STUB_FILE + len(normal)].hex(),
                        "new": normal.hex(),
                        "semantic": f"{variant.name} normal-coverage stub.",
                    },
                    {
                        "file_offset": f"0x{invert_file:x}",
                        "virtual_address": f"0x{invert_va:x}",
                        "old": data[invert_file : invert_file + len(invert)].hex(),
                        "new": invert.hex(),
                        "semantic": f"{variant.name} inverted-coverage stub.",
                    },
                    *extra_patches,
                    {
                        "file_offset": f"0x{INVERT_BRANCH_FILE:x}",
                        "virtual_address": f"0x{INVERT_BRANCH_VA:x}",
                        "old": data[INVERT_BRANCH_FILE : INVERT_BRANCH_FILE + 4].hex(),
                        "new": arm_b(INVERT_BRANCH_VA, invert_va).hex(),
                        "semantic": f"Redirect inverted gray_hline coverage continuation to {variant.name} stub.",
                    },
                    {
                        "file_offset": f"0x{NORMAL_BRANCH_FILE:x}",
                        "virtual_address": f"0x{NORMAL_BRANCH_VA:x}",
                        "old": data[NORMAL_BRANCH_FILE : NORMAL_BRANCH_FILE + 4].hex(),
                        "new": arm_b(NORMAL_BRANCH_VA, NORMAL_STUB_VA).hex(),
                        "semantic": f"Redirect normal gray_hline coverage clamp to {variant.name} stub.",
                    },
                ],
            }
        ]
    }
    path = patched_dir / f"patch_manifest.arm_{variant.name}.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def repack_variant(firmware_dir: Path, work_dir: Path, variant_name: str) -> dict:
    patched_elf = work_dir / "patched" / f"armfir.{variant_name}.elf"
    source_app = firmware_dir / "PRIME_APP.DAT"
    source_md5 = firmware_dir / "Prime_FW.md5"
    if not patched_elf.exists():
        raise FileNotFoundError(patched_elf)
    if not source_app.exists():
        raise FileNotFoundError(source_app)
    if not source_md5.exists():
        raise FileNotFoundError(source_md5)

    out_dir = work_dir / "patched_firmware"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_app = out_dir / f"PRIME_APP.{variant_name}_poc.DAT"
    out_md5 = out_dir / f"Prime_FW.{variant_name}_poc.md5"
    report_path = out_dir / f"repack_report.{variant_name}.json"

    image = bytearray(source_app.read_bytes())
    fat = Fat16(image, FAT_BASE)
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
        "variant": variant_name,
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


def verify_variant(firmware_dir: Path, work_dir: Path, variant_name: str) -> dict:
    failures: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    manifest_path = work_dir / "patched" / f"patch_manifest.arm_{variant_name}.json"
    app_path = work_dir / "patched_firmware" / f"PRIME_APP.{variant_name}_poc.DAT"
    outer_md5_path = work_dir / "patched_firmware" / f"Prime_FW.{variant_name}_poc.md5"
    stock_app_path = firmware_dir / "PRIME_APP.DAT"
    for path in (manifest_path, app_path, outer_md5_path, stock_app_path):
        check(path.exists(), f"missing {path}")
    if failures:
        return {"ok": False, "variant": variant_name, "failures": failures}

    manifest = load_manifest(manifest_path)
    patch_set = manifest["patch_sets"][0]
    source = Path(patch_set["source"])
    patched_elf_path = Path(patch_set["output"])
    check(source.exists(), f"missing {source}")
    check(patched_elf_path.exists(), f"missing {patched_elf_path}")
    if failures:
        return {"ok": False, "variant": variant_name, "failures": failures}

    original = source.read_bytes()
    patched = patched_elf_path.read_bytes()
    expected = bytearray(original)
    check(md5_bytes(original).lower() == patch_set["source_md5"].lower(), "manifest source MD5 mismatch")
    check(len(original) == len(patched), "patched ELF size changed")
    check(patched[:4] == b"\x7fELF", "patched ELF missing ELF magic")
    for patch in patch_set["patches"]:
        off = int(patch["file_offset"], 0) if isinstance(patch["file_offset"], str) else patch["file_offset"]
        old = parse_hex(patch["old"])
        new = parse_hex(patch["new"])
        check(bytes(original[off : off + len(old)]) == old, f"old bytes mismatch at 0x{off:x}")
        expected[off : off + len(old)] = new
    check(bytes(expected) == patched, "patched ELF differs outside manifest patches")

    image = app_path.read_bytes()
    stock_app = stock_app_path.read_bytes()
    check(len(image) == len(stock_app), "PRIME_APP size changed")
    fat = Fat16(image, FAT_BASE)
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

    outer_text = outer_md5_path.read_text(encoding="ascii", errors="replace")
    match = re.search(r"([0-9a-fA-F]{32})(\s+\*?PRIME_APP\.DAT)", outer_text)
    check(match is not None, "outer MD5 missing PRIME_APP.DAT line")
    if match:
        check(match.group(1).lower() == md5_bytes(image), "outer MD5 does not match patched PRIME_APP")

    result = {
        "ok": not failures,
        "variant": variant_name,
        "failures": failures,
        "patched_elf_md5": md5_bytes(patched),
        "patched_prime_app_md5": md5_bytes(image),
    }
    out = work_dir / "patched_firmware" / f"verify_repack.{variant_name}.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def make_flash_package(firmware_dir: Path, work_dir: Path, variant_name: str, out_dir: Path) -> dict:
    patched_app = work_dir / "patched_firmware" / f"PRIME_APP.{variant_name}_poc.DAT"
    patched_md5 = work_dir / "patched_firmware" / f"Prime_FW.{variant_name}_poc.md5"
    if not patched_app.exists():
        raise FileNotFoundError(patched_app)
    if not patched_md5.exists():
        raise FileNotFoundError(patched_md5)
    out_dir.mkdir(parents=True, exist_ok=True)
    for src in firmware_dir.iterdir():
        if not src.is_file():
            continue
        if src.name.upper() in {"PRIME_APP.DAT", "PRIME_FW.MD5"}:
            continue
        shutil.copy2(src, out_dir / src.name)
    shutil.copy2(patched_app, out_dir / "PRIME_APP.DAT")
    shutil.copy2(patched_md5, out_dir / "Prime_FW.md5")
    report = {
        "variant": variant_name,
        "out_dir": str(out_dir),
        "prime_app_md5": md5_bytes((out_dir / "PRIME_APP.DAT").read_bytes()),
        "files": sorted(p.name for p in out_dir.iterdir() if p.is_file()),
    }
    (out_dir / f"flash_package.{variant_name}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def run_all(args: argparse.Namespace) -> None:
    if args.extract:
        extract_assets(args.firmware_dir, args.work_dir)
    results = []
    for variant in args.variants:
        manifest = generate_manifest(args.work_dir, variant)
        apply_manifest(manifest)
        repack_variant(args.firmware_dir, args.work_dir, variant)
        result = verify_variant(args.firmware_dir, args.work_dir, variant)
        if not result["ok"]:
            raise SystemExit(json.dumps(result, indent=2))
        if args.flash_root:
            make_flash_package(
                args.firmware_dir,
                args.work_dir,
                variant,
                args.flash_root / f"flash_package_{variant}",
            )
        results.append(result)
    print(json.dumps(results, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate HP Prime G1 coverage variants.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("generate", help="Generate a coverage patch manifest")
    p.add_argument("--work-dir", type=Path, required=True)
    p.add_argument("--variant", required=True)

    p = sub.add_parser("repack", help="Repack an already-patched variant ELF into PRIME_APP.DAT")
    p.add_argument("--firmware-dir", type=Path, required=True)
    p.add_argument("--work-dir", type=Path, required=True)
    p.add_argument("--variant", required=True)

    p = sub.add_parser("verify", help="Verify a repacked variant")
    p.add_argument("--firmware-dir", type=Path, required=True)
    p.add_argument("--work-dir", type=Path, required=True)
    p.add_argument("--variant", required=True)

    p = sub.add_parser("make-flash-package", help="Create a variant flash package directory")
    p.add_argument("--firmware-dir", type=Path, required=True)
    p.add_argument("--work-dir", type=Path, required=True)
    p.add_argument("--variant", required=True)
    p.add_argument("--out-dir", type=Path, required=True)

    p = sub.add_parser("all", help="Generate, apply, repack, verify, and optionally make flash packages")
    p.add_argument("--firmware-dir", type=Path, required=True)
    p.add_argument("--work-dir", type=Path, required=True)
    p.add_argument("--variants", nargs="+", required=True)
    p.add_argument("--flash-root", type=Path)
    p.add_argument("--extract", action="store_true", help="Extract assets before generating variants")

    args = parser.parse_args()
    if args.command == "generate":
        print(generate_manifest(args.work_dir, args.variant))
    elif args.command == "repack":
        print(json.dumps(repack_variant(args.firmware_dir, args.work_dir, args.variant), indent=2))
    elif args.command == "verify":
        result = verify_variant(args.firmware_dir, args.work_dir, args.variant)
        print(json.dumps(result, indent=2))
        if not result["ok"]:
            raise SystemExit(1)
    elif args.command == "make-flash-package":
        print(json.dumps(make_flash_package(args.firmware_dir, args.work_dir, args.variant, args.out_dir), indent=2))
    elif args.command == "all":
        run_all(args)


if __name__ == "__main__":
    main()
