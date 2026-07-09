import argparse
import hashlib
import json
from pathlib import Path


PATCH = {
    "file_offset": 0x5CE2,
    "virtual_address": "0x1400068e2",
    "old": bytes.fromhex("746c"),
    "new": bytes.fromhex("eb6c"),
    "semantic": (
        "Updater.exe version/no-update gate bypass: change short conditional "
        "jump `je start_update` after `cmp eax, 3` to an unconditional short "
        "jump. This bypasses the local package availability/version filter "
        "after the selected update directory has been parsed."
    ),
}


def md5(data):
    return hashlib.md5(data).hexdigest()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--manifest", required=True)
    args = ap.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)
    manifest_path = Path(args.manifest)

    data = bytearray(in_path.read_bytes())
    off = PATCH["file_offset"]
    old = PATCH["old"]
    new = PATCH["new"]

    actual = bytes(data[off : off + len(old)])
    if actual == new:
        status = "already_patched"
    elif actual == old:
        data[off : off + len(old)] = new
        out_path.write_bytes(data)
        status = "patched"
    else:
        raise SystemExit(
            f"unexpected bytes at 0x{off:x}: expected {old.hex()} or {new.hex()}, got {actual.hex()}"
        )

    if status == "already_patched" and in_path != out_path:
        out_path.write_bytes(data)

    out_data = out_path.read_bytes()
    expected = bytearray(in_path.read_bytes())
    if bytes(expected[off : off + len(old)]) == old:
        expected[off : off + len(old)] = new
    if out_data != bytes(expected):
        raise SystemExit("output differs beyond the expected patch bytes")

    manifest = {
        "target": str(out_path),
        "source": str(in_path),
        "status": status,
        "source_md5": md5(in_path.read_bytes()),
        "source_sha256": sha256(in_path.read_bytes()),
        "output_md5": md5(out_data),
        "output_sha256": sha256(out_data),
        "patches": [
            {
                "file_offset": f"0x{off:x}",
                "virtual_address": PATCH["virtual_address"],
                "old": old.hex(),
                "new": new.hex(),
                "semantic": PATCH["semantic"],
                "before": "cmp eax, 3; je 0x140006950",
                "after": "cmp eax, 3; jmp 0x140006950",
            }
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"{status}: {out_path}")
    print(f"output_md5={manifest['output_md5']}")
    print(f"output_sha256={manifest['output_sha256']}")
    print(f"manifest={manifest_path}")


if __name__ == "__main__":
    main()

