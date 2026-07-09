# Softcut64 Design

## 试过的方案

探索过程中试过几类方案：

```text
coverage255      把所有非零 coverage 拉到 255
threshold128     coverage >= 128 ? 255 : 0
threshold160/192 更硬的阈值
softcut64/96     coverage < cutoff 时清零，其他灰度保留
softband64_224   清浅灰，同时把很高 coverage 拉黑
```

硬阈值方案在低分辨率中文和密集 UI 文本中会出现黑块、粘连和局部不可辨认。用户确认“像素太硬”后，硬阈值路线被否决。

`softcut64` 保留中高 coverage 的灰度，只剪掉很浅的灰边，是当前最稳妥的第一实机候选。

## ARM patch shape

补丁使用 ELF 里已有的零填充代码洞，不新增段、不改变文件大小。

代码洞：

```text
normal stub   file 0x63a628 VA 0x30c3a5f4
inverted stub file 0x63a63c VA 0x30c3a608
```

redirect：

```text
file 0x2db974 VA 0x308db940 -> inverted stub
file 0x2db978 VA 0x308db944 -> normal stub
```

normal stub:

```asm
30c3a5f4  cmp    r0, #0x100
30c3a5f8  movge  r0, #0xff
30c3a5fc  cmp    r0, #0x40
30c3a600  movlo  r0, #0
30c3a604  b      0x308db94c
```

inverted stub:

```asm
30c3a608  cmp    r0, #0x40
30c3a60c  movlo  r0, #0
30c3a610  b      0x308db94c
```

## 字节级 manifest

最终 manifest 在：

```text
patches/patch_manifest.arm_softcut64.json
```

核心字节：

```text
0x63a628: 0000000000000000000000000000000000000000
       -> 010c50e3ff00a0a3400050e30000a033d084f2ea

0x63a63c: 000000000000000000000000
       -> 400050e30000a033cd84f2ea

0x2db974: 010000ea -> 307b0dea
0x2db978: 010c50e3 -> 2a7b0dea
```

## 验收条件

静态验收必须满足：

- patched ELF MD5 为 `32ac6681f1a8287db20fbe33d0035fe7`；
- ELF 大小仍为 `8230724`；
- 只有 manifest 记录的字节变化；
- `PRIME_APP.DAT` 大小不变；
- FAT16 仍可解析；
- 内部 `APPSLIST.MD5` 匹配 patched `armfir.elf`；
- 外层 `Prime_FW.md5` 匹配 repacked `PRIME_APP.DAT`。


