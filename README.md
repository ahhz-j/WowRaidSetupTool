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
- 自然人与角色管理界面初版
- 自然人与角色数据库读写初版
- 活动 / 班次 / 模板管理初版

## 本地运行

```bash
pip install -r requirements.txt
python src/main.py
```

## 当前已实现

- 自然人新增、编辑、删除
- 自然人默认可参加活动日设置（Fri/Sat/Sun/Mon）
- 角色新增、编辑、删除
- 角色职业设置
- 角色职责设置（Tank / Healer / DPS）
- 角色启用/停用状态
- 阵容模板新增、编辑、删除
- 模板人数校验（总人数必须等于 25）
- 活动新增、编辑、删除
- 班次新增、编辑、删除
- 班次绑定模板
- 周五/六/日/一批量生成班次（14 天窗口）

## 打包 EXE

在 Windows PowerShell 中执行：

```powershell
./build.ps1
```
