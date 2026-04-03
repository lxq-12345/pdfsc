#### 管理和监控命令

```bash
# 查看系统状态
ipmcget -d systeminfo

# 设置电源开启
ipmcset -d powerstate -v 1

# 设置电源关闭
ipmcset -d powerstate -v 0

# 强制重启
ipmcset -d powerstate -v 3
```

#### 监控温度和风扇

```bash
# 查看温度
ipmcget -d temperature

# 查看风扇転速
ipmcget -d fan
```
