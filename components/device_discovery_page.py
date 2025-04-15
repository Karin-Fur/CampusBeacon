import json
import socket
import sys
import threading
import customtkinter as ctk
from PIL import Image
from CTkMessagebox import CTkMessagebox
from PyQt5.QtWidgets import QApplication
from components.CustomTools import CustomScrollableFrame, ToolTip, create_custom_help_button

class DeviceDiscoveryPage:
    def __init__(self, parent, start_search_callback, stop_search_callback, switch_to_file_page_callback, local_ip,
                 local_device_name):
        """
        初始化设备发现页面。

        Args:
            parent: 父组件。
            start_search_callback: 开始搜索的回调函数。
            stop_search_callback: 停止搜索的回调函数。
            switch_to_file_page_callback: 切换到文件传输页面的回调函数。
            local_ip: 本地设备的 IP 地址。
            local_device_name: 本地设备的名称。
        """
        # 创建 QApplication 实例
        self.app = QApplication(sys.argv)  # 确保只有一个 QApplication 实例
        self.parent = parent
        self.start_search_callback = start_search_callback
        self.stop_search_callback = stop_search_callback
        self.switch_to_file_page_callback = switch_to_file_page_callback
        self.local_ip = local_ip  # 存储本地 IP 地址
        self.device_name = local_device_name  # 存储本地设备名称
        self.searching = False  # 搜索状态
        self.device_list = []  # 缓存的设备列表

        # 创建主框架
        self.frame = ctk.CTkFrame(self.parent, fg_color="#1B2B3B")
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)

        # 标题和图标改为左对齐，添加手动连接按钮在右侧
        title_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=20, padx=20)
        title_frame.grid_columnconfigure(2, weight=1)  # 中间空白区域自动扩展

        # 左侧标题和图标
        image = ctk.CTkImage(light_image=Image.open("icons/device_discover.png"),
                             dark_image=Image.open("icons/device_discover.png"),
                             size=(32, 32))
        self.title_image = ctk.CTkLabel(title_frame, text="", image=image)
        self.title_label = ctk.CTkLabel(
            title_frame, text="设备发现", font=ctk.CTkFont("微软雅黑", size=24, weight="bold")
        )
        self.title_image.grid(row=0, column=0, sticky="w", padx=(0, 5), rowspan=2)
        self.title_label.grid(row=0, column=1, sticky="w", rowspan=2)

        self.description_label = ctk.CTkLabel(self.frame,
                                              text="-经测试，由于校园网对UDP广播、组播的限制，如无法发现设备，请使用IP手动连接",
                                              )
        # 显示本机IP
        self.ip_label = ctk.CTkLabel(
            title_frame, 
            text=f"本机IP: {self.local_ip}", 
            font=ctk.CTkFont("微软雅黑", size=12, underline=True),
            text_color="#4A9BFF",
            cursor="hand2"  # 手型光标
        )
        self.ip_label.grid(row=1, column=2, sticky="e", padx=25, columnspan=2)
        self.ip_label.bind("<Button-1>", self.copy_ip_to_clipboard)
        # 右侧手动连接按钮
        self.manual_connect_button = ctk.CTkButton(
            title_frame,
            text="手动连接",
            command=self.show_manual_connect_dialog,
            height=30,
            width=100,
            font=ctk.CTkFont(family="微软雅黑", size=14),
            fg_color="#1F6AA5", 
            hover_color="#144870"
        )
        self.manual_connect_button.grid(row=0, column=2, pady=(10, 0), sticky="e")
        help_button = create_custom_help_button(title_frame)
        ToolTip(help_button, "搜索不到设备时，尝试使用该方法连接")
        help_button.grid(row=0, column=3, pady=(10, 0), sticky="e")
        # 创建滚动区域
        self.device_list_frame = CustomScrollableFrame(self.frame, fg_color="transparent",
                                                       border_color="#7D7D7D", border_width=3, height=480,)
        self.device_list_frame.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=20, pady=(0, 20))
        self.device_list_frame.grid_columnconfigure(0, weight=1)  # 保证卡片宽度

        # 加载条
        self.progress_bar = ctk.CTkProgressBar(self.frame, orientation="horizontal", mode="indeterminate", height=5)
        self.progress_bar.grid(row=3, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")
        self.progress_bar.set(0)  # 初始化为未激活状态
        self.progress_bar.grid_remove()  # 默认隐藏加载条

        # 开始/停止搜索按钮
        self.search_button = ctk.CTkButton(
            self.frame,
            text="开始搜索",
            command=self.toggle_search,
            height=40,
            font=ctk.CTkFont(family="微软雅黑", size=16, weight="bold"),
            fg_color="#1F6AA5", hover_color="#144870"
        )
        self.search_button.grid(row=4, column=0, padx=5, pady=(0, 20), sticky="e")

        # 清空列表按钮
        self.clear_button = ctk.CTkButton(
            self.frame,
            text="清空列表",
            command=lambda: self.clear_device_list(manual=True),
            height=40,
            font=ctk.CTkFont(family="微软雅黑", size=16, weight="bold"),
            fg_color="#E65A5A", hover_color="#B54747"
        )
        self.clear_button.grid(row=4, column=1, padx=5, pady=(0, 20), sticky="w")

    def toggle_search(self):
        """切换搜索状态"""
        if not self.searching:
            # 启动搜索
            if not self.start_search_callback():    # 已有设备连接则不切换
                return
            self.clear_device_list(manual=False)  # 清空设备列表
            self.progress_bar.grid()  # 显示加载条
            self.progress_bar.start()  # 开始加载动画
            self.search_button.configure(text="停止搜索", fg_color="#E65A5A", hover_color="#B54747",
                                         font=ctk.CTkFont(family="微软雅黑", size=16, weight="bold"))
        else:
            # 停止搜索
            self.progress_bar.stop()  # 停止加载动画
            self.progress_bar.grid_remove()  # 隐藏加载条
            self.stop_search_callback()
            self.search_button.configure(text="开始搜索", fg_color="#1F6AA5", hover_color="#144870",
                                         font=ctk.CTkFont(family="微软雅黑", size=16, weight="bold"))
        self.searching = not self.searching
        self.disable_button_temporarily(2)  # 禁用按钮两秒

    def disable_button_temporarily(self, delay):
        """暂时禁用按钮并延迟恢复"""
        self.search_button.configure(state="disabled")

        # 在新线程中延迟恢复按钮
        def enable_button_after_delay():
            threading.Event().wait(delay)
            self.search_button.configure(state="normal")

        threading.Thread(target=enable_button_after_delay, daemon=True).start()

    def add_device(self, device_name, ip, tcp_port, avatar_image=None):
        """添加设备到列表"""
        # 避免添加本机
        if device_name == self.device_name and ip == self.local_ip:
            return
        # 检查设备名称和 IP 是否已经存在
        for widget in self.device_list_frame.winfo_children():
            name_label = widget.winfo_children()[1]
            ip_label = widget.winfo_children()[2]

            if name_label.cget("text") == device_name and ip_label.cget("text") == f"{ip}:{tcp_port}":
                return  # 如果设备名称和 IP 均已存在，则不重复添加

        # 创建设备卡片
        card = ctk.CTkFrame(self.device_list_frame, fg_color="#2A2A2A", corner_radius=10)
        card.grid_columnconfigure(1, weight=1)

        # 设置头像和名称
        avatar = ctk.CTkImage(light_image=Image.open("icons/device_dark.png"),
                              dark_image=Image.open("icons/device_dark.png"), size=(50, 50))
        avatar_label = ctk.CTkLabel(card, image=avatar, text="")
        avatar_label.grid(row=0, column=0, rowspan=2, padx=10, pady=5)

        name_label = ctk.CTkLabel(card, text=device_name, font=ctk.CTkFont(size=14, weight="bold"))
        name_label.grid(row=0, column=1, sticky="w", padx=(0, 10))

        ip_label = ctk.CTkLabel(card, text=f"{ip}:{tcp_port}", font=ctk.CTkFont(size=12), text_color="gray")
        ip_label.grid(row=1, column=1, sticky="w", padx=(0, 10))

        # 连接按钮
        connect_icon = ctk.CTkImage(light_image=Image.open("icons/connect_light.png"),
                                    dark_image=Image.open("icons/connect_dark.png"), size=(36, 36))
        connect_button = ctk.CTkButton(card, text="", image=connect_icon, width=30, height=30,
                                       command=lambda: self.connect_to_device(self.device_name, ip, tcp_port),
                                       fg_color="transparent", hover=False)
        connect_button.grid(row=0, column=2, rowspan=2, padx=10, pady=5, sticky="e")

        card.pack(fill="x", padx=10, pady=5)

    def clear_device_list(self, manual):
        """清空设备列表"""
        confirm = True
        if manual:
            msg = CTkMessagebox(title="确认", font=("微软雅黑", 14),
                                message="确认要清空设备列表吗?",
                                icon="question",
                                option_1="确定",
                                option_2="取消")

            response = msg.get()
            if response == "确定":
                confirm = True
            else:
                confirm = False
        if confirm:
            self.device_list = []  # 清空缓存的设备列表
            for widget in self.device_list_frame.winfo_children():
                widget.destroy()

    def connect_to_device(self, device_name, ip, tcp_port):
        """与指定设备建立TCP连接"""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(10)
            client_socket.connect((ip, tcp_port))
            print(f"成功连接到 {ip}:{tcp_port}")

            # 发送确认消息
            message = {"device_name": device_name, "action": "connect",
                       "ip": self.local_ip, "tcp_port": tcp_port}
            client_socket.send(json.dumps(message).encode("utf-8"))

            # 接收服务器响应
            response = json.loads(client_socket.recv(1024).decode("utf-8"))
            print(f"收到响应: {response}")
            connect_device_name = response.get("device_name")
            connect_ip = response.get("ip")
            status = response.get("status")
            if status == "connected":
                # 如果正在搜索，停止搜索
                if self.searching:
                    self.toggle_search()
                self.clear_device_list(manual=False)  # 清空设备列表
                # 跳转到文件传输界面
                self.switch_to_file_page_callback(connect_device_name, connect_ip, tcp_port)

                CTkMessagebox(title="连接成功", message=f"成功连接到设备 {connect_ip}:{tcp_port}", icon="check",
                              option_1="确定", font=("微软雅黑", 14))
            elif status == "reject":
                CTkMessagebox(title="连接失败", message=f"对方拒绝了我们的连接", icon="cancel",
                              option_1="确定", font=("微软雅黑", 14))

        except TimeoutError:
            print(f"连接到设备 {ip}:{tcp_port} 超时")
            CTkMessagebox(
                title="连接失败",
                message=f"无法连接到设备 {ip}:{tcp_port}\n错误: 超时。",
                option_1="确定", font=("微软雅黑", 14),
                icon="cancel"
            )
        except Exception as e:
            print(f"连接到设备 {ip}:{tcp_port} 失败: {e}")
            CTkMessagebox(
                title="连接失败",
                message=f"无法连接到设备 {ip}:{tcp_port}\n错误: {e}\n请确保目标设备在搜索状态",
                option_1="确定", font=("微软雅黑", 14),
                icon="cancel",
            )

    def update_local_info(self, local_ip, local_device_name):
        """更新本机名称和 IP"""
        self.local_ip = local_ip
        self.device_name = local_device_name
        # 更新IP标签
        self.ip_label.configure(text=f"本机IP: {self.local_ip}")
        print(f"设备发现页已更新：本机名称={self.device_name}, 本机IP={self.local_ip}")

    def show_manual_connect_dialog(self):
        """显示手动连接对话框"""
        # 创建对话框窗口
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("手动连接")
        dialog.geometry("350x200")
        dialog.resizable(False, False)
        dialog.grab_set()  # 模态窗口

        # 设置窗口在父窗口中居中
        dialog.update_idletasks()
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() - dialog.winfo_width()) // 2
        y = self.parent.winfo_rooty() + (self.parent.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        # 创建表单
        form_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # IP地址输入
        ctk.CTkLabel(form_frame, text="IP地址:", font=("微软雅黑", 14)).grid(row=0, column=0, sticky="w", pady=(0, 10))
        ip_entry = ctk.CTkEntry(form_frame, width=250, font=("微软雅黑", 14))
        ip_entry.grid(row=0, column=1, sticky="ew", pady=(0, 10), padx=(10, 0))

        # 端口输入
        ctk.CTkLabel(form_frame, text="端口:", font=("微软雅黑", 14)).grid(row=1, column=0, sticky="w", pady=(0, 20))
        port_entry = ctk.CTkEntry(form_frame, width=250, font=("微软雅黑", 14))
        port_entry.insert(0, "50001")  # 默认端口
        port_entry.grid(row=1, column=1, sticky="ew", pady=(0, 20), padx=(10, 0))

        # 提示信息
        ctk.CTkLabel(
            form_frame, 
            text="注意: 请确保目标设备处于搜索状态",
            font=("微软雅黑", 12),
            text_color="gray"
        ).grid(row=2, column=0, columnspan=2, sticky="w")

        # 按钮区域
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.grid(row=3, column=0, columnspan=2, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        # 取消按钮
        ctk.CTkButton(
            button_frame,
            text="取消",
            command=dialog.destroy,
            height=30,
            width=100,
            font=ctk.CTkFont(family="微软雅黑", size=14),
            fg_color="#E65A5A",
            hover_color="#B54747"
        ).grid(row=0, column=0, padx=10, pady=10)

        # 连接按钮
        def connect_action():
            ip = ip_entry.get().strip()
            try:
                port = int(port_entry.get().strip())
            except ValueError:
                CTkMessagebox(title="错误", message="端口必须是数字", icon="cancel", font=("微软雅黑", 14))
                return

            if not ip:
                CTkMessagebox(title="错误", message="请输入IP地址", icon="cancel", font=("微软雅黑", 14))
                return

            dialog.destroy()  # 关闭对话框
            self.connect_to_device(self.device_name, ip, port)  # 连接到设备

        ctk.CTkButton(
            button_frame,
            text="连接",
            command=connect_action,
            height=30,
            width=100,
            font=ctk.CTkFont(family="微软雅黑", size=14),
            fg_color="#1F6AA5",
            hover_color="#144870"
        ).grid(row=0, column=1, padx=10, pady=10)

    def copy_ip_to_clipboard(self, event=None):
        """将IP地址复制到剪贴板"""
        self.parent.clipboard_clear()
        self.parent.clipboard_append(self.local_ip)

        # 创建一个小的悬浮提示
        tooltip = ctk.CTkToplevel(self.parent)
        tooltip.wm_overrideredirect(True)  # 移除标题栏
        tooltip.attributes("-topmost", True)  # 置顶

        # 计算位置（在IP标签下方）
        x = self.ip_label.winfo_rootx()
        y = self.ip_label.winfo_rooty() + self.ip_label.winfo_height()

        # 设置位置
        tooltip.geometry(f"150x30+{x}+{y}")

        # 添加文本
        label = ctk.CTkLabel(
            tooltip,
            text="IP已复制",
            font=ctk.CTkFont("微软雅黑", size=12),
            fg_color="#333333",
            corner_radius=5
        )
        label.pack(fill="both", expand=True)

        # 1.5秒后自动关闭
        tooltip.after(1500, tooltip.destroy)
