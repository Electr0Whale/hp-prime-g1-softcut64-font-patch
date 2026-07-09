# Hardware Test Checklist

复制本页作为实机测试记录。

## 设备信息

```text
Device:
Hardware version:
Stock firmware before test:
Patch variant: softcut64
Patched PRIME_APP.DAT MD5: 59c9a785212599acd5b676bf72e6b5c2
Date:
Tester:
```

## 刷入前

```text
[ ] 确认是 HP Prime G1
[ ] 电量充足
[ ] USB 线稳定，直连电脑
[ ] Connectivity Kit 能识别设备
[ ] 已备份计算器数据
[ ] 已准备 stock rollback package
[ ] patched flash package verify 通过
[ ] CK cache verify 通过
```

## 更新过程

```text
[ ] 更新页面读取本地缓存
[ ] 更新开始
[ ] 设备进入 Recovery Mode
[ ] 写入完成
[ ] 设备自动重启
[ ] Connectivity Kit 重新识别设备
```

## 启动检查

```text
[ ] Home 正常
[ ] CAS 正常
[ ] App list 正常
[ ] Settings 正常
[ ] 菜单和软键可读
[ ] 输入框可读
[ ] 数学符号可读
[ ] 中文字符串可读
[ ] 关机重启正常
```

## 字体视觉检查

```text
[ ] 没有大面积黑块
[ ] 中文 12px 文本没有严重粘连
[ ] 细笔画没有明显断裂
[ ] 菜单文本没有错位
[ ] Home/CAS 结果可读性优于 stock 或至少不劣化
[ ] 长时间浏览菜单无崩溃
```

## 异常记录

```text
Observed issue:
Page/screen:
Repro steps:
Photo/video path:
Rollback required: yes/no
```

## 结论

```text
[ ] 接受 softcut64，继续观察
[ ] 可用但仍偏软，考虑 softband64_224
[ ] 不可接受，回滚 stock
[ ] 固件异常，立即回滚/恢复
```


