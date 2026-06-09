# WowRaidSetupTool

Windows 10 桌面版 WOW 团队活动排班工具。

## 当前状态

项目已完成首轮初始化，包含：

- 软件设计说明文档
- PySide6 桌面程序骨架
- SQLite 数据库初始化
- 基础领域模型
- Buff/Debuff 目录初版
- 导入导出协议骨架

## 本地运行

```bash
pip install -r requirements.txt
python src/main.py
```

## 打包 EXE

在 Windows PowerShell 中执行：

```powershell
./build.ps1
```
