# WSL简要使用手册（简化版 VMware）

**适用项目**：pdfsc  
**创建日期**：2026-03-13  
**版本**：v1.0

---

## 1. 目标

将 WSL2 作为一个长期可复用、可控的 Linux 开发环境使用，重点实现：

- 可控资源：CPU、内存、Swap、虚拟磁盘上限
- 可控网络：NAT / mirrored 模式、DNS、防火墙策略
- 代理可用：对接 Windows 代理（含翻墙代理）
- 可运维：可停止、可迁移、可备份、可恢复

---

## 2. 与 VMware 的关系

相同点：

- 都是独立 Linux 运行环境
- 都能做资源限制、网络配置、备份恢复
- 都适合长期项目开发

差异点：

- WSL2 是轻量虚拟化，不是完整 BIOS/硬件层虚机
- WSL 更偏开发工作流，和 Windows 文件/终端集成更紧密
- 控制方式以 `wsl` 命令 + 配置文件为主，不是图形化虚机面板

结论：

- 可把 WSL2 看作“简化版 VMware 虚机”，足够覆盖大多数开发场景

---

## 3. 配置文件与存储位置

### 3.1 Windows 全局配置（控制所有 WSL2 发行版）

- 路径：`C:\Users\<你的用户名>\.wslconfig`
- 作用：内存、CPU、swap、网络模式、代理策略、VHD 默认上限等

### 3.2 Linux 发行版内配置（每个发行版单独）

- 路径：`/etc/wsl.conf`
- 作用：systemd、默认用户、自动挂载、发行版内网络行为

### 3.3 发行版磁盘文件

- 路径（示例）：`C:\Users\<你的用户名>\AppData\Local\wsl\{GUID}\ext4.vhdx`
- 说明：这是发行版根文件系统虚拟磁盘

---

## 4. 常用管理命令（PowerShell）

```powershell
wsl --status                    # 查看 WSL 状态
wsl -l -v                       # 查看发行版与版本
wsl -d Ubuntu                   # 进入 Ubuntu
wsl -d Ubuntu --cd /mnt/d/usr/百信公司项目/pdfsc

wsl --set-default Ubuntu        # 设置默认发行版
wsl --terminate Ubuntu          # 停止某个发行版
wsl --shutdown                  # 停止全部 WSL VM
```

---

## 5. 资源与网络控制（.wslconfig 模板）

在 `C:\Users\<你的用户名>\.wslconfig` 写入：

```ini
[wsl2]
memory=8GB
processors=6
swap=8GB
swapFile=C:\\WSL\\swap.vhdx
vmIdleTimeout=600000

# 网络
networkingMode=mirrored
firewall=true
dnsTunneling=true
autoProxy=true
localhostForwarding=true

# 新建发行版默认虚拟磁盘上限
defaultVhdSize=256GB

[experimental]
autoMemoryReclaim=gradual
sparseVhd=true
# mirrored 模式下常用
hostAddressLoopback=true
```

应用配置：

```powershell
wsl --shutdown
# 等几秒后重新启动发行版
wsl -d Ubuntu
```

说明：

- `memory`、`processors`、`swap`：最核心的“虚机配额”
- `defaultVhdSize`：新建发行版时默认 VHD 大小上限
- `networkingMode=mirrored`：通常比 NAT 更容易使用本机代理和端口
- `autoProxy=true`：自动读取 Windows 代理设置

---

## 6. 发行版内配置（/etc/wsl.conf 示例）

```ini
[boot]
systemd=true

[user]
default=wy885

[network]
generateHosts=true
generateResolvConf=true
```

修改后执行：

```powershell
wsl --shutdown
wsl -d Ubuntu
```

---

## 7. 代理对接（翻墙代理）

### 7.1 推荐方案：mirrored + autoProxy

前提：

- Windows 代理工具已开启
- Windows 系统代理配置可用
- `.wslconfig` 中启用 `networkingMode=mirrored` 和 `autoProxy=true`

验证：

```bash
env | grep -i proxy
curl -I https://www.google.com
```

### 7.2 兼容方案：NAT 手动代理（当 mirrored 不可用时）

```bash
HOST_IP=$(grep nameserver /etc/resolv.conf | awk '{print $2}')
export http_proxy=http://$HOST_IP:7890
export https_proxy=http://$HOST_IP:7890
export all_proxy=socks5://$HOST_IP:7890
```

持久化到 `~/.bashrc` 或 `~/.zshrc`。

---

## 8. 磁盘上限、迁移、备份恢复

### 8.1 调整发行版磁盘大小上限（已存在发行版）

```powershell
wsl --manage Ubuntu --resize 256GB
```

### 8.2 移动发行版到指定目录（更可控）

```powershell
wsl --manage Ubuntu --move D:\WSL\Ubuntu
```

### 8.3 备份（导出）

```powershell
wsl --export Ubuntu D:\WSL_Backup\Ubuntu_20260313.tar
```

### 8.4 恢复（导入）

```powershell
wsl --import h2o D:\WSL\h2o D:\WSL_Backup\Ubuntu_20260313.tar --version 2
wsl --set-default h2o
```

### 8.5 新建固定大小磁盘发行版（接近 VMware 固定盘）

```powershell
wsl --install Ubuntu --name h2o --location D:\WSL\h2o --version 2 --fixed-vhd --vhd-size 256GB
```

---

## 9. 推荐日常流程

1. 启动并进入项目目录

```powershell
wsl -d Ubuntu --cd /mnt/d/usr/百信公司项目/pdfsc
```

2. 在 WSL 内执行开发任务（Python、脚本、Docker 等）

3. 任务结束按需停止

```powershell
wsl --terminate Ubuntu
# 或
wsl --shutdown
```

---

## 10. 故障与排查

### 10.1 配置改了不生效

- 先执行：`wsl --shutdown`
- 关闭所有 WSL 终端
- 等数秒后重启发行版

### 10.2 出现“localhost 代理未镜像到 WSL”提示

- 优先改为 `networkingMode=mirrored`
- 或改用 NAT 手动代理方案（第 7.2 节）

### 10.3 检查当前运行状态

```powershell
wsl --status
wsl -l -v
wsl --list --running
```

---

## 11. 一句话总结

WSL2 可以作为简化版 VMware 使用：

- 用 `.wslconfig` 控全局资源和网络
- 用 `/etc/wsl.conf` 控发行版行为
- 用 `wsl` 命令完成启动、停止、迁移、备份与恢复
