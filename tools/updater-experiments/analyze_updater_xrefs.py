import argparse
import json
import re
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86_const import X86_OP_MEM, X86_OP_IMM, X86_REG_RIP


def u16(data, off):
    return struct.unpack_from("<H", data, off)[0]


def u32(data, off):
    return struct.unpack_from("<I", data, off)[0]


def u64(data, off):
    return struct.unpack_from("<Q", data, off)[0]


class PE:
    def __init__(self, path):
        self.path = Path(path)
        self.data = self.path.read_bytes()
        if self.data[:2] != b"MZ":
            raise ValueError("not an MZ executable")
        pe = u32(self.data, 0x3C)
        if self.data[pe : pe + 4] != b"PE\0\0":
            raise ValueError("not a PE executable")
        self.pe_off = pe
        self.machine = u16(self.data, pe + 4)
        self.section_count = u16(self.data, pe + 6)
        self.opt_size = u16(self.data, pe + 20)
        opt = pe + 24
        magic = u16(self.data, opt)
        if magic != 0x20B:
            raise ValueError(f"expected PE32+, got optional header magic 0x{magic:x}")
        self.image_base = u64(self.data, opt + 24)
        self.entry_rva = u32(self.data, opt + 16)
        sec_off = opt + self.opt_size
        self.sections = []
        for i in range(self.section_count):
            off = sec_off + i * 40
            name = self.data[off : off + 8].split(b"\0", 1)[0].decode("ascii", "replace")
            virt_size = u32(self.data, off + 8)
            virt_addr = u32(self.data, off + 12)
            raw_size = u32(self.data, off + 16)
            raw_ptr = u32(self.data, off + 20)
            chars = u32(self.data, off + 36)
            self.sections.append(
                {
                    "name": name,
                    "virt_size": virt_size,
                    "virt_addr": virt_addr,
                    "raw_size": raw_size,
                    "raw_ptr": raw_ptr,
                    "chars": chars,
                }
            )

    def rva_to_off(self, rva):
        for sec in self.sections:
            start = sec["virt_addr"]
            end = start + max(sec["virt_size"], sec["raw_size"])
            if start <= rva < end:
                off = sec["raw_ptr"] + (rva - start)
                if off < len(self.data):
                    return off
        return None

    def off_to_rva(self, off):
        for sec in self.sections:
            start = sec["raw_ptr"]
            end = start + sec["raw_size"]
            if start <= off < end:
                return sec["virt_addr"] + (off - start)
        return None

    def off_to_va(self, off):
        rva = self.off_to_rva(off)
        if rva is None:
            return None
        return self.image_base + rva

    def section_data(self, name):
        sec = next(s for s in self.sections if s["name"] == name)
        return sec, self.data[sec["raw_ptr"] : sec["raw_ptr"] + sec["raw_size"]]


def find_strings(data, needle):
    out = []
    ascii_pat = needle.encode("ascii")
    wide_pat = needle.encode("utf-16le")
    for pat, kind in [(ascii_pat, "ascii"), (wide_pat, "utf16le")]:
        start = 0
        while True:
            idx = data.find(pat, start)
            if idx < 0:
                break
            out.append({"offset": idx, "kind": kind})
            start = idx + 1
    return out


def disasm_text(pe):
    text_sec, text = pe.section_data(".text")
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True
    base = pe.image_base + text_sec["virt_addr"]
    return list(md.disasm(text, base))


def find_xrefs(instructions, target_va):
    refs = []
    for insn in instructions:
        for op in insn.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                eff = insn.address + insn.size + op.mem.disp
                if eff == target_va:
                    refs.append(insn)
            elif op.type == X86_OP_IMM and op.imm == target_va:
                refs.append(insn)
    return refs


def function_window(instructions, insn, before=80, after=140):
    idx = instructions.index(insn)
    lo = max(0, idx - before)
    hi = min(len(instructions), idx + after)
    return instructions[lo:hi]


def format_insn(insn):
    bytes_s = insn.bytes.hex()
    return f"{insn.address:016x}  {bytes_s:<24}  {insn.mnemonic} {insn.op_str}".rstrip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--needle", default="No updates are available")
    ap.add_argument("--json-out")
    args = ap.parse_args()

    pe = PE(args.exe)
    instructions = disasm_text(pe)
    hits = []
    for hit in find_strings(pe.data, args.needle):
        va = pe.off_to_va(hit["offset"])
        xrefs = find_xrefs(instructions, va) if va is not None else []
        item = {
            "needle": args.needle,
            "kind": hit["kind"],
            "file_offset": hit["offset"],
            "rva": None if va is None else va - pe.image_base,
            "va": va,
            "xrefs": [],
        }
        print(f"STRING {hit['kind']} off=0x{hit['offset']:x} va={None if va is None else hex(va)}")
        for ref in xrefs:
            ref_off = pe.rva_to_off(ref.address - pe.image_base)
            print(f"XREF file=0x{ref_off:x} {format_insn(ref)}")
            window = function_window(instructions, ref)
            print("WINDOW")
            for w in window:
                mark = "=>" if w.address == ref.address else "  "
                print(f"{mark} {format_insn(w)}")
            item["xrefs"].append(
                {
                    "file_offset": ref_off,
                    "va": ref.address,
                    "instruction": format_insn(ref),
                    "window": [format_insn(w) for w in window],
                }
            )
        hits.append(item)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(hits, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

