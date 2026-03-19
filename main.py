import tkinter as tk
from tkinter import messagebox, ttk
import netifaces
import subprocess
import random
import re
import sys
import ctypes
import os

# ---------- 自动提权函数 ----------
def ensure_admin():
    """如果当前不是管理员，则尝试以管理员权限重新启动本程序，然后退出当前进程。"""
    try:
        if ctypes.windll.shell32.IsUserAnAdmin():
            return  # 已经是管理员，继续执行
    except:
        # 非 Windows 环境忽略（代码实际不会运行到这里）
        return

    # 不是管理员，构造命令行并请求提权
    try:
        # 将当前命令行参数转换为正确的字符串格式（处理空格和引号）
        params = subprocess.list2cmdline(sys.argv)
        ret = ctypes.windll.shell32.ShellExecuteW(
            None,           # 父窗口句柄
            "runas",        # 操作：以管理员身份运行
            sys.executable, # 要执行的程序（Python 解释器 或 打包后的 exe）
            params,         # 命令行参数
            None,           # 工作目录
            1               # 显示窗口（SW_SHOWNORMAL）
        )
        if ret <= 32:  # ShellExecute 返回值 <=32 表示错误
            ctypes.windll.user32.MessageBoxW(
                0, "请求管理员权限失败，请手动以管理员身份运行。", "提权失败", 0x10
            )
    except Exception as e:
        ctypes.windll.user32.MessageBoxW(
            0, f"提权过程中发生错误：{str(e)}", "错误", 0x10
        )
    sys.exit(0)  # 无论成功或失败，原进程都退出

# ---------- Tooltip 类（跟随鼠标）----------
class ToolTip:
    def __init__(self, widget, text=''):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.mouse_x = 0
        self.mouse_y = 0

        self.widget.bind('<Enter>', self.on_enter)
        self.widget.bind('<Leave>', self.on_leave)
        self.widget.bind('<Motion>', self.on_motion)

    def on_enter(self, event):
        self.schedule()
        self.update_mouse_pos(event)

    def on_leave(self, event):
        self.unschedule()
        self.hidetip()

    def on_motion(self, event):
        self.update_mouse_pos(event)
        if self.tipwindow:
            x = self.mouse_x + 15
            y = self.mouse_y + 10
            self.tipwindow.wm_geometry(f"+{x}+{y}")

    def update_mouse_pos(self, event):
        self.mouse_x = event.x_root
        self.mouse_y = event.y_root

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(500, self.showtip)

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def showtip(self):
        if self.tipwindow or not self.text:
            return
        x = self.mouse_x + 15
        y = self.mouse_y + 10
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

    def update_text(self, text):
        self.text = text

# ---------- 主程序 ----------
class MacChangerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ez-mac-changer (一款 MAC 地址修改器)")
        self.root.geometry("400x160")
        self.root.resizable(False, False)
        self.root.withdraw()  # 先隐藏窗口，避免初始显示在左上角

        self.interface_mac = {}          # 显示名称 -> MAC 地址
        self.display_to_name = {}         # 显示名称 -> 友好名称（用于修改）
        self.interfaces = []              # 所有显示名称列表

        self.get_physical_interfaces()

        # 创建主容器并居中布局
        main_frame = ttk.Frame(root)
        main_frame.pack(expand=True)

        self.create_widgets(main_frame)

        if self.interfaces:
            self.interface_var.set(self.interfaces[0])
            self.update_mac_display()
        else:
            messagebox.showerror("错误", "未找到任何物理网卡！")
            self.root.destroy()
            return

        # 计算最终位置并显示窗口
        self.root.update_idletasks()  # 强制计算控件尺寸
        self.center_window()           # 设置窗口居中
        self.root.deiconify()          # 显示窗口

    def center_window(self):
        """将窗口移动到屏幕中央"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def get_physical_interfaces(self):
        display_to_name, name_to_guid = self._get_windows_adapter_map()

        for guid in netifaces.interfaces():
            if guid == 'lo' or guid.startswith(('veth', 'docker', 'br-', 'vmnet')):
                continue
            addrs = netifaces.ifaddresses(guid)
            if netifaces.AF_LINK in addrs:
                mac = addrs[netifaces.AF_LINK][0].get('addr')
                if mac and self.is_valid_mac(mac):
                    friendly_name = None
                    for name, g in name_to_guid.items():
                        if g == guid:
                            friendly_name = name
                            break
                    if friendly_name:
                        for display_str, fname in display_to_name.items():
                            if fname == friendly_name:
                                self.interface_mac[display_str] = mac
                                self.display_to_name[display_str] = friendly_name
                                self.interfaces.append(display_str)
                                break
                    else:
                        display_str = guid
                        self.interface_mac[display_str] = mac
                        self.display_to_name[display_str] = guid
                        self.interfaces.append(display_str)

    def _get_windows_adapter_map(self):
        display_to_name = {}
        name_to_guid = {}
        try:
            ps_cmd = (
                "Get-NetAdapter | "
                "Where-Object { $_.PhysicalMediaType -ne 0 } | "
                "Select-Object Name, InterfaceGuid, InterfaceDescription | "
                "ConvertTo-Csv -NoTypeInformation"
            )
            result = subprocess.run(
                ["powershell", "-Command", ps_cmd],
                capture_output=True, shell=True
            )
            if result.returncode == 0:
                stdout = result.stdout
                output = None
                for encoding in ['utf-8', 'gbk', sys.getdefaultencoding()]:
                    try:
                        output = stdout.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                if output is None:
                    output = stdout.decode('utf-8', errors='replace')

                lines = output.strip().split('\n')
                if len(lines) >= 2:
                    for line in lines[1:]:
                        if not line.strip():
                            continue
                        parts = line.strip().strip('"').split('","')
                        if len(parts) >= 3:
                            name = parts[0]
                            guid = parts[1]
                            desc = parts[2].rstrip('"')
                            display_str = f"{name} ({desc})" if desc and desc != name else name
                            display_to_name[display_str] = name
                            name_to_guid[name] = guid
        except Exception as e:
            print(f"获取 Windows 网卡映射失败: {e}", file=sys.stderr)
        return display_to_name, name_to_guid

    def is_valid_mac(self, mac):
        pattern = r'^([0-9A-Fa-f]{2}[:.-]){5}[0-9A-Fa-f]{2}$'
        return re.match(pattern, mac) is not None

    def create_widgets(self, parent):
        # 使用 grid 在 parent 中居中放置，设置行列权重使内容居中
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(2, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_rowconfigure(3, weight=1)

        # 第一行：网卡选择
        tk.Label(parent, text="选择网卡:").grid(row=0, column=1, pady=5, sticky='e')
        self.interface_var = tk.StringVar(parent)
        self.interface_var.trace('w', lambda *args: self.update_mac_display())

        self.interface_combo = ttk.Combobox(
            parent, textvariable=self.interface_var,
            values=self.interfaces, width=40, state='readonly'
        )
        self.interface_combo.grid(row=0, column=2, pady=5, padx=5, sticky='w')

        # 添加 Tooltip
        self.tooltip = ToolTip(self.interface_combo, "")
        self.interface_var.trace('w', self.update_tooltip)

        # 第二行：MAC 地址
        tk.Label(parent, text="MAC 地址:").grid(row=1, column=1, pady=5, sticky='e')
        self.mac_entry = tk.Entry(parent, width=25)
        self.mac_entry.grid(row=1, column=2, pady=5, padx=5, sticky='w')

        # 第三行：按钮
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=1, columnspan=2, pady=10)

        self.apply_btn = tk.Button(button_frame, text="应用修改", command=self.apply_change)
        self.apply_btn.pack(side='left', padx=5)

        self.random_btn = tk.Button(button_frame, text="随机 MAC", command=self.generate_random_mac)
        self.random_btn.pack(side='left', padx=5)

        # 关于按钮
        self.about_btn = tk.Button(button_frame, text="关于", command=self.show_about)
        self.about_btn.pack(side='left', padx=5)

        self.close_btn = tk.Button(button_frame, text="关闭", command=self.root.destroy)
        self.close_btn.pack(side='left', padx=5)

    def show_about(self):
        """显示关于窗口，包含可复制的网址"""
        about_win = tk.Toplevel(self.root)
        about_win.title("关于")
        about_win.resizable(False, False)
        about_win.transient(self.root)  # 设置为父窗口的临时窗口
        about_win.grab_set()            # 模态

        # 强制窗口获取焦点
        about_win.focus_force()
        
        # 网址内容（可根据实际项目地址修改）
        url = "https://github.com/Leenshady/Ez-Mac-Changer"  # 替换为你的实际项目地址

        # 根据网址长度动态调整窗口宽度
        char_width_px = 8  # 每个字符大致像素宽度
        entry_width = max(30, len(url) + 5)              # 输入框宽度（字符数）
        window_width = entry_width * char_width_px   # 窗口总宽度（像素）
        about_win.geometry(f"{int(window_width)}x140")

        # 居中显示相对于父窗口
        about_win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - about_win.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - about_win.winfo_height()) // 2
        about_win.geometry(f"+{x}+{y}")

        # 提示文本
        tk.Label(about_win, text="项目地址：", font=("微软雅黑", 9)).pack(pady=(10, 0))

        # 可复制 Entry（只读）
        url_entry = tk.Entry(about_win, width=entry_width, font=("Consolas", 9))
        url_entry.insert(0, url)
        url_entry.config(state='readonly', readonlybackground='#f0f0f0')
        url_entry.pack(pady=5, padx=20)

        # 说明
        tk.Label(about_win, text="(可选中文本后按 Ctrl+C 复制)", fg="gray", font=("微软雅黑", 8)).pack()

        # 关闭按钮
        tk.Button(about_win, text="关闭", command=about_win.destroy).pack(pady=10)

    def update_tooltip(self, *args):
        display_str = self.interface_var.get()
        self.tooltip.update_text(display_str)

    def update_mac_display(self):
        display_str = self.interface_var.get()
        if display_str in self.interface_mac:
            self.mac_entry.delete(0, tk.END)
            self.mac_entry.insert(0, self.interface_mac[display_str])

    def generate_random_mac(self):
        mac_bytes = [random.randint(0x00, 0xff) for _ in range(6)]
        mac_bytes[0] = (mac_bytes[0] & 0xfe) | 0x00
        mac_bytes[0] = (mac_bytes[0] & 0xfd) | 0x00
        mac_str = ':'.join(f"{b:02x}" for b in mac_bytes)
        self.mac_entry.delete(0, tk.END)
        self.mac_entry.insert(0, mac_str)

    def apply_change(self):
        display_str = self.interface_var.get()
        new_mac = self.mac_entry.get().strip()

        if not display_str:
            messagebox.showerror("错误", "请先选择一个网卡")
            return
        if not self.is_valid_mac(new_mac):
            messagebox.showerror("错误", "MAC 地址格式无效！\n正确格式如：00:11:22:33:44:55")
            return
        if not messagebox.askyesno("确认", f"确定要将网卡 {display_str} 的 MAC 地址修改为 {new_mac} 吗？\n修改后可能需要重新启用网卡才能生效。"):
            return

        try:
            self._change_mac(display_str, new_mac)
            messagebox.showinfo("成功", f"MAC 地址修改成功！\n请重新插拔网线或重启网络适配器使更改生效。")
            self.interface_mac[display_str] = new_mac
            self.update_mac_display()
        except Exception as e:
            messagebox.showerror("失败", f"修改 MAC 地址时出错：\n{str(e)}")

    def _change_mac(self, display_str, new_mac):
        friendly_name = self.display_to_name.get(display_str)
        if not friendly_name:
            raise RuntimeError("无法找到对应的网卡名称")
        ps_command = f"Set-NetAdapter -Name '{friendly_name}' -MacAddress '{new_mac}' -Confirm:$false"
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True, text=True, shell=True
        )
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout
            raise RuntimeError(f"PowerShell 执行失败：{error_msg}")

if __name__ == "__main__":
    ensure_admin()  # 尝试自动获取管理员权限
    # 权限足够，正常启动
    root = tk.Tk()
    app = MacChangerApp(root)
    root.mainloop()