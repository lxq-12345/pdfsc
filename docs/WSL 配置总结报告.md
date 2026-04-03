# WSL 配置总结报告

**项目**：pdfsc  
**生成日期**：2026-03-13  
**报告范围**：总结本轮 WSL 环境治理与配置落地的全部工作  
**目标**：将当前 WSL2 环境整理为一个长期、可控、可代理联网、接近简化版 VMware 使用体验的开发环境。

---

## 一、背景与目标

在进入 pdfsc 下一阶段项目任务前，先完成 WSL 环境治理，重点解决以下问题：

1. 将 Ubuntu 发行版迁移到 D 盘，避免继续占用 C 盘。
2. 修复并验证 WSL 的网络与翻墙代理能力。
3. 为 WSL 设置明确的 CPU、内存、Swap 和磁盘上限。
4. 使该环境具备长期复用和可维护性。

---

## 二、前置信息核查

本轮配置前，已确认以下本机环境信息：

1. WSL 版本：2.6.3.0
2. 当前默认发行版：Ubuntu（WSL2）
3. 机器内存：约 32GB
4. CPU：13th Gen Intel(R) Core(TM) i7-13700H，20 个逻辑处理器
5. Windows 系统代理：127.0.0.1:7899
6. 磁盘剩余空间：
   - C 盘约 117GB 可用
   - D 盘约 356GB 可用

基于这些信息，最终决定：

1. Ubuntu 主体迁移到 D 盘。
2. 资源限制采取 12GB 内存、8 线程、8GB Swap。
3. 虚拟磁盘上限收紧到 156GB。
4. 网络采用 mirrored 模式，并开启 autoProxy。

---

## 三、本轮完成的全部工作

### 3.1 WSL 状态与发行版存储检查

已完成：

1. 检查 `wsl --status`、`wsl -l -v`，确认 Ubuntu 为默认发行版。
2. 读取注册表 `HKCU\Software\Microsoft\Windows\CurrentVersion\Lxss`，确认 Ubuntu 的实际 BasePath。
3. 确认 Ubuntu 原始根磁盘文件位于 C 盘。

### 3.2 Ubuntu 发行版迁移到 D 盘

已执行：

```powershell
wsl --shutdown
wsl --manage Ubuntu --move D:\WSL\Ubuntu
```

迁移结果：

1. Ubuntu BasePath 已切换为 `D:\WSL\Ubuntu`
2. 发行版主存储已不再落在 C 盘
3. 当前 Ubuntu 已满足“主体存放在 D 盘”的要求

### 3.3 WSL 网络与代理配置落地

已更新全局配置文件：`C:\Users\wy885\.wslconfig`

本轮写入的网络相关配置：

```ini
[wsl2]
networkingMode=mirrored
firewall=true
dnsTunneling=true
autoProxy=true

[experimental]
hostAddressLoopback=true
```

处理说明：

1. 使用 mirrored 网络模式，增强与宿主机网络和代理的协同。
2. 启用 autoProxy，使 WSL 自动继承 Windows 代理信息。
3. 启用 dnsTunneling 和 firewall，保证 DNS 与防火墙行为可控。
4. 发现 mirrored 模式下 `localhostForwarding` 无效，因此已删除该项，避免警告。

### 3.4 WSL 代理联网验证

已验证：

1. WSL 内自动注入以下代理环境变量：
   - `http_proxy=http://127.0.0.1:7899`
   - `https_proxy=http://127.0.0.1:7899`
   - `HTTP_PROXY=http://127.0.0.1:7899`
   - `HTTPS_PROXY=http://127.0.0.1:7899`
2. 从 WSL 内访问外网成功：
   - Google 返回 HTTP 200
   - PyPI 返回 HTTP 200

结论：

当前 WSL 已能正确接入本机翻墙代理并访问外网。

### 3.5 资源限制正式落地

根据本机实际硬件，已在 `C:\Users\wy885\.wslconfig` 中正式写入：

```ini
[wsl2]
memory=12GB
processors=8
swap=8GB
swapFile=D:\\WSL\\swap.vhdx
defaultVhdSize=156GB
networkingMode=mirrored
firewall=true
dnsTunneling=true
autoProxy=true

[experimental]
hostAddressLoopback=true
```

### 3.6 当前 Ubuntu 磁盘上限同步收紧

已执行：

```powershell
wsl --manage Ubuntu --resize 156GB
```

结果：

1. Ubuntu 当前发行版上限已同步调整到 156GB。
2. 在 WSL 内查看根盘，已显示约 153G 总容量，符合收紧后的磁盘边界。

### 3.7 VS Code 工作区终端集成

已为当前工作区新增：

1. `.vscode/settings.json`

作用：

1. 在 VS Code 中默认打开 Ubuntu WSL 终端。
2. 自动进入项目目录：`/mnt/d/usr/百信公司项目/pdfsc`

### 3.8 生成的配套文档

本轮同时生成了以下文档：

1. `docs/WSL简要使用手册.md`
2. `docs/WSL本机默认参数建议.md`
3. `docs/WSL 配置总结报告.md`（本文件）

---

## 四、关键配置文件与落点

### 4.1 Windows 全局 WSL 配置

- 路径：`C:\Users\wy885\.wslconfig`
- 作用：控制所有 WSL2 发行版的全局资源和网络行为

### 4.2 Ubuntu 发行版内配置

- 路径：`/etc/wsl.conf`
- 当前关键内容：

```ini
[boot]
systemd=true

[user]
default=wy885
```

### 4.3 Ubuntu 当前存储位置

- BasePath：`D:\WSL\Ubuntu`
- 根磁盘文件位于该目录下

### 4.4 Swap 文件

- 路径：`D:\WSL\swap.vhdx`

---

## 五、备份与可回滚项

本轮修改前后，已生成以下 `.wslconfig` 备份：

1. `C:\Users\wy885\.wslconfig.bak.20260313_194118`
2. `C:\Users\wy885\.wslconfig.bak.20260313_200153`
3. `C:\Users\wy885\.wslconfig.bak.20260313_200534`

如需回滚，可将任一备份覆盖回 `C:\Users\wy885\.wslconfig`，然后执行：

```powershell
wsl --shutdown
```

---

## 六、验证结果

本轮已完成的有效验证包括：

1. Ubuntu 已迁移到 D 盘：验证通过
2. WSL 内代理环境变量自动注入：验证通过
3. WSL 联网访问 Google / PyPI：验证通过
4. CPU 上限已生效：`nproc` 返回 8
5. 内存上限已生效：`free -h` 显示总内存约 11Gi
6. Swap 已生效：`free -h` 与 `swapon --show` 显示 8Gi
7. 当前 Ubuntu 磁盘上限已收紧：根盘显示约 153G

---

## 七、当前最终状态

当前这台机器上的 WSL 已具备以下特征：

1. 发行版主体存放于 D 盘
2. 可控的 CPU、内存、Swap、磁盘上限
3. 可直接接入 Windows 代理实现翻墙联网
4. 可在 VS Code 中作为固定开发终端直接使用
5. 已达到“简化版 VMware 虚机”的主要目标

当前最终参数如下：

1. 内存上限：12GB
2. CPU 上限：8 个逻辑处理器
3. Swap：8GB
4. Swap 文件：`D:\WSL\swap.vhdx`
5. 默认虚拟磁盘上限：156GB
6. 当前 Ubuntu 发行版上限：156GB
7. 网络模式：mirrored
8. 自动代理：开启

---

## 八、结论

本轮 WSL 配置工作已完整达成目标：

1. 解决了发行版存储位置问题。
2. 解决了 WSL 访问翻墙代理的问题。
3. 解决了资源无限制增长的问题。
4. 建立了可维护、可回滚、可文档化的 WSL 使用基线。

因此，当前环境已满足在进入 pdfsc 下一阶段项目任务之前的 WSL 前置条件。
