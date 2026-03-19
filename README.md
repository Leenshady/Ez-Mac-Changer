# ez-mac-changer

一款简单易用的 Windows 平台 MAC 地址修改器，拥有直观的图形界面。自动请求管理员权限，支持随机生成 MAC 地址，并可在修改前查看当前网卡信息。

## ✨ 功能特性

- 🖥️ **自动提权**：启动时若权限不足，自动通过 UAC 请求管理员权限，无需手动右键“以管理员身份运行”。
- 📋 **网卡列表**：下拉菜单显示所有物理网卡，格式为“名称 (描述)”，方便识别。
- 🖱️ **跟随提示**：鼠标悬停在网卡下拉框上时，完整名称会浮动显示。
- 🎲 **随机 MAC**：点击按钮可生成符合规范的随机 MAC 地址（单播、全局唯一）。
- ✏️ **手动修改**：支持手动输入任意合法的 MAC 地址（格式如 `00:11:22:33:44:55`）。
- 🔧 **一键应用**：调用 PowerShell 命令修改指定网卡的 MAC 地址，无需额外工具。
- ℹ️ **关于窗口**：包含项目地址（可复制），方便用户访问源码。

## 📦 安装与运行

### 1. 直接运行 Python 脚本（需 Python 3.8+）
```bash
# 克隆或下载本项目
git clone https://github.com/Leenshady/Ez-Mac-Changer.git
cd Ez-Mac-Changer

# 安装依赖
pip install netifaces

# 运行程序
python main.py
```

### 2. 使用打包好的 exe（推荐）
从 [Releases](../../releases) 页面下载最新版本的 `Ez-Mac-Changer.exe`，直接双击运行即可。

## 🔨 自行打包

项目提供了自动打包脚本，基于 Python 虚拟环境和 PyInstaller，生成的无控制台窗口的 exe 文件。

### 准备工作
- 安装 [Python 3.8+](https://www.python.org/downloads/) 并添加到 PATH。
- 确保网络通畅（脚本会自动使用国内 PyPI 镜像加速）。

### 打包步骤
1. 将 `main.py` 和 `build_exe.bat` 放在同一目录。
2. 双击运行 `build_exe.bat`。
3. 脚本将：
   - 创建虚拟环境 `venv_build`
   - 安装 `pipreqs` 并自动生成 `requirements.txt`
   - 安装依赖（强制包含 `netifaces`）
   - 安装 PyInstaller 并打包为 `--onefile --noconsole` 的 exe
   - 询问是否删除临时虚拟环境
4. 生成的 exe 位于 `dist` 文件夹内。

### 打包脚本核心命令
```bash
pyinstaller --onefile --noconsole --hidden-import netifaces main.py
```

## ⚠️ 注意事项

- **管理员权限**：修改 MAC 地址需要系统级权限，程序会自动请求 UAC 提权。若用户拒绝，程序将退出。
- **网卡支持**：仅支持 Windows 系统，且网卡驱动需允许 MAC 地址修改（大部分有线/无线网卡支持）。
- **修改后生效**：修改 MAC 后可能需要重新插拔网线或重启网络适配器才能生效。
- **安全提示**：随机生成的 MAC 地址符合 IEEE 802 标准（单播、全局唯一），但请勿用于任何非法用途。

## 📄 许可证

本项目采用 [GNU General Public License v3.0 许可证](LICENSE)。你可以自由使用、修改和分发，但需保留版权声明。

## 📮 反馈与贡献

欢迎提交 [Issues](../../issues) 报告问题或提出建议，也欢迎通过 Pull Request 贡献代码。

---

**Happy MAC Changing!** 🚀
