import argparse
import hashlib
import json
from pathlib import Path


PATCHES = [
    {
        "file_offset": 0x5A13,
        "virtual_address": "0x140006613",
        "old": bytes.fromhex("097a0000"),
        "new": bytes.fromhex("397a0000"),
        "before": "default scan accepts APPSDISK.DAT",
        "after": "default scan accepts PRIME_APP.DAT",
    },
    {
        "file_offset": 0x5A27,
        "virtual_address": "0x140006627",
        "old": bytes.fromhex("057a0000"),
        "new": bytes.fromhex("357a0000"),
        "before": "default scan accepts BESTAARM.ROM",
        "after": "default scan accepts PRIME_OS.ROM",
    },
    {
        "file_offset": 0x5A3B,
        "virtual_address": "0x14000663b",
        "old": bytes.fromhex("017a0000"),
        "new": bytes.fromhex("317a0000"),
        "before": "default scan accepts MASTER.DAT",
        "after": "default scan accepts PRIME_MASTER.DAT",
    },
]


def digest(name, data):
    h = hashlib.new(name)
    h.update(data)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--manifest", required=True)
    args = ap.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)
    manifest_path = Path(args.manifest)

    source = in_path.read_bytes()
    data = bytearray(source)
    applied = []

    for patch in PATCHES:
        off = patch["file_offset"]
        old = patch["old"]
        new = patch["new"]
        actual = bytes(data[off : off + len(old)])
        if actual == old:
            data[off : off + len(old)] = new
            status = "patched"
        elif actual == new:
            status = "already_patched"
        else:
            raise SystemExit(
                f"unexpected bytes at 0x{off:x}: expected {old.hex()} or {new.hex()}, got {actual.hex()}"
            )
        applied.append(
            {
                "file_offset": f"0x{off:x}",
                "virtual_address": patch["virtual_address"],
                "old": old.hex(),
                "new": new.hex(),
                "before": patch["before"],
                "after": patch["after"],
                "status": status,
            }
        )

    out_path.write_bytes(data)

    expected = bytearray(source)
    for patch in PATCHES:
        off = patch["file_offset"]
        if bytes(expected[off : off + len(patch["old"])]) == patch["old"]:
            expected[off : off + len(patch["old"])] = patch["new"]
    if bytes(expected) != bytes(data):
        raise SystemExit("output differs beyond expected filename-filter patches")

    manifest = {
        "source": str(in_path),
        "target": str(out_path),
        "source_md5": digest("md5", source),
        "source_sha256": digest("sha256", source),
        "output_md5": digest("md5", data),
        "output_sha256": digest("sha256", data),
        "semantic": (
            "Updater.exe default folder scan filter patch: accept the official "
            "PRIME_APP.DAT / PRIME_OS.ROM / PRIME_MASTER.DAT file names in the "
            "same early filter slots that originally accepted APPSDISK.DAT / "
            "BESTAARM.ROM / MASTER.DAT."
        ),
        "patches": applied,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"patched: {out_path}")
    print(f"output_md5={manifest['output_md5']}")
    print(f"output_sha256={manifest['output_sha256']}")
    print(f"manifest={manifest_path}")


if __name__ == "__main__":
    main()

