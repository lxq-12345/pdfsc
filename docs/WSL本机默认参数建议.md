# WSL本机默认参数建议

**适用机器**：LENOVO 21HW  
**生成日期**：2026-03-13  
**适用环境**：Windows + WSL2 + pdfsc 项目  
**用途**：为当前这台机器提供一套可直接落地的 WSL 默认参数，作为“简化版 VMware”使用。

---

## 1. 本机基线

已确认的本机信息：

- 物理内存：约 32 GB（34071240704 bytes）
- CPU：13th Gen Intel(R) Core(TM) i7-13700H
- 物理核心数：14
- 逻辑处理器数：20
- Windows 系统代理：127.0.0.1:7899
- 磁盘剩余空间：
  - C 盘剩余约 117.44 GB
  - D 盘剩余约 355.79 GB

结论：

- WSL 发行版建议长期放在 D 盘
- 网络建议优先使用 mirrored 模式
- 代理建议优先使用 autoProxy，再按需补手动代理

---

## 2. 推荐方案

### 2.1 总体建议

这台机器建议把 WSL 当作长期固定开发环境使用，参数如下：

- 内存上限：12 GB
- CPU 上限：8 个逻辑处理器
- Swap：8 GB
- 默认虚拟磁盘上限：256 GB
- 网络模式：mirrored
- 防火墙：开启
- DNS 隧道：开启
- 自动代理：开启
- VHD 存储目录：D:\\WSL\\Ubuntu 或 D:\\WSL\\h2o

这套参数的考虑是：

- 对 32 GB 内存机器，给 WSL 12 GB 足够跑 Python、Docker、向量处理和常规开发任务
- 对 20 线程 CPU，给 8 线程足够，不会过度侵占 Windows 前台使用体验
- 8 GB swap 可作为高峰缓冲
- 256 GB 虚拟磁盘上限足够长期项目与 Docker 缓存使用

---

## 3. 推荐的 .wslconfig

建议创建文件：`C:\Users\wy885\.wslconfig`

推荐内容如下：

```ini
[wsl2]
memory=12GB
processors=8
swap=8GB
swapFile=D:\\WSL\\swap.vhdx
vmIdleTimeout=600000

# 网络
networkingMode=mirrored
firewall=true
dnsTunneling=true
autoProxy=true
localhostForwarding=true

# 新建发行版默认磁盘上限
defaultVhdSize=256GB

[experimental]
autoMemoryReclaim=gradual
sparseVhd=true
hostAddressLoopback=true
```

说明：

- `memory=12GB`：限制 WSL 最多吃掉 12 GB 内存
- `processors=8`：限制 CPU 并发占用
- `swapFile=D:\\WSL\\swap.vhdx`：把 swap 放到 D 盘，避免继续吃 C 盘
- `networkingMode=mirrored`：更利于代理、端口映射和本机网络对接
- `autoProxy=true`：自动读取 Windows 代理设置
- `defaultVhdSize=256GB`：新建发行版时默认限制 VHD 最大容量

应用方式：

```powershell
wsl --shutdown
wsl -d Ubuntu
```

---

## 4. 当前 Ubuntu 的建议处理

当前 Ubuntu 的根磁盘文件在 C 盘，建议后续迁移到 D 盘。

推荐做法：

```powershell
wsl --terminate Ubuntu
wsl --manage Ubuntu --move D:\WSL\Ubuntu
```

迁移后优点：

- 减轻 C 盘空间压力
- 便于集中管理 WSL 资产
- 备份和恢复更直观

如果你更希望完全隔离项目环境，可以新建一个独立发行版，例如 `h2o`：

```powershell
wsl --install Ubuntu --name h2o --location D:\WSL\h2o --version 2 --fixed-vhd --vhd-size 256GB
```

这更接近 VMware 的“单独虚机”使用习惯。

---

## 5. 代理建议

### 5.1 推荐主方案

你的 Windows 系统代理当前是：`127.0.0.1:7899`

推荐主方案：

- `.wslconfig` 中使用 `networkingMode=mirrored`
- 开启 `autoProxy=true`
- 保持 Windows 代理工具持续运行

这样做的目的，是让 WSL 尽量自动继承 Windows 代理设置。

### 5.2 备用方案

如果仍然出现代理不通或出现 localhost 未镜像提示，则在 Linux 内手动设置：

```bash
export http_proxy=http://127.0.0.1:7899
export https_proxy=http://127.0.0.1:7899
export all_proxy=socks5://127.0.0.1:7899
```

若 mirrored 模式下仍不可用，再改为使用宿主机局域网地址或按代理工具的“允许局域网连接”配置处理。

建议验证命令：

```bash
env | grep -i proxy
curl -I https://www.google.com
curl -I https://pypi.org
```

---

## 6. 适合这台机器的使用场景

这套配置适合以下场景：

- Python 项目开发
- Docker / systemd 服务
- 本地 CLI 工具开发
- API 调试与联网安装依赖
- 中型数据处理与文本转换流水线

如果只是轻量脚本，不需要长期服务，可以把内存降到 8 GB；如果未来要跑较重的 Docker 或模型工具，再升到 16 GB。

---

## 7. 不建议的配置

对这台机器，不建议：

- `memory` 直接给到 20 GB 以上：会明显压缩 Windows 前台可用内存
- `processors` 直接给满 20：没有必要，且容易影响宿主机响应
- 继续把大型 VHD、swap 文件都留在 C 盘
- 在 NAT 模式下长期依赖 localhost 代理却不做手动补偿

---

## 8. 推荐执行顺序

建议按以下顺序实施：

1. 创建 `C:\Users\wy885\.wslconfig`
2. 写入本文件给出的推荐配置
3. 执行 `wsl --shutdown`
4. 重新进入 Ubuntu 验证资源与代理
5. 确认无误后，将 Ubuntu 移动到 `D:\WSL\Ubuntu`
6. 如果要完全隔离，再单独创建 `h2o` 发行版

---

## 9. 一句话结论

对当前这台 32 GB / 20 线程笔记本，最稳妥的 WSL 默认方案是：

- `memory=12GB`
- `processors=8`
- `swap=8GB`
- `defaultVhdSize=256GB`
- `networkingMode=mirrored`
- `autoProxy=true`
- WSL 存储迁移到 D 盘

这套配置足够把 WSL 当成一个长期、可控、接近 VMware 使用体验的开发虚机。