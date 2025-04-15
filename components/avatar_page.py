import json
from tkinter import filedialog
import customtkinter as ctk
from PIL import Image
from CTkMessagebox import CTkMessagebox
import socket
import os
import numpy as np


def get_local_ip():
    """获取本地 IP 地址。"""
    try:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    except:
        return "无法获取 IP"


def create_circular_image(image_path, size):
    """
    将图片裁剪为圆形，使用像素级抗锯齿绘制平滑遮罩。
    """
    image = Image.open(image_path).resize(size, Image.Resampling.LANCZOS).convert("RGBA")
    width, height = size
    mask = np.zeros((height, width), dtype=np.uint8)
    center_x, center_y = width // 2, height // 2
    radius = min(center_x, center_y)
    for y in range(height):
        for x in range(width):
            distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
            if distance < radius:
                mask[y, x] = 255
            elif distance < radius + 1:
                mask[y, x] = int(255 * (1 - (distance - radius)))
    mask_image = Image.fromarray(mask, mode="L")
    circular_image = Image.new("RGBA", size)
    circular_image.paste(image, (0, 0), mask_image)
    return circular_image


class AvatarPage:
    def __init__(self, parent, update_sidebar_avatar_callback, update_network_broadcast_callback):
        """
        初始化 AvatarPage。
        Args:
            parent: 父窗口组件。
            update_sidebar_avatar_callback: 更新侧边栏头像的回调函数。
            update_network_broadcast_callback: 更新广播内容的回调函数。
        """
        self.parent = parent
        self.update_sidebar_avatar_callback = update_sidebar_avatar_callback
        self.update_network_broadcast_callback = update_network_broadcast_callback

        # 默认设置
        self.default_avatar_path = "icons/default_avatar.png"  # 默认头像路径

        self.avatar_path = self.default_avatar_path
        self.computer_name = f"device_{os.urandom(3).hex()[:5]}"  # 默认计算机名称
        self.local_ip = get_local_ip()  # 本地 IP
        self.broadcast_port = 50000  # 默认广播端口
        self.tcp_port = 50001  # 默认 TCP 端口

        # 创建主框架
        self.frame = ctk.CTkFrame(parent, fg_color="#1B2B3B")
        self.frame.grid_columnconfigure(0, weight=1)

        # 创建页面内容
        self.create_avatar_page()


    def create_avatar_page(self, ):
        """创建头像页面"""
        self.load_settings()
        # 加载头像图片
        if self.avatar_path == self.default_avatar_path:
            avatar_image = Image.open(self.default_avatar_path)
            # 显示头像图片
            self.avatar_image = ctk.CTkImage(light_image=avatar_image, dark_image=avatar_image, size=(150, 150))
        else:
            self.avatar_image = self.reshaped_avatar()
        self.avatar_label = ctk.CTkLabel(self.frame, image=self.avatar_image, text="")
        self.avatar_label.grid(row=0, column=0, columnspan=2, pady=(50, 10))
        self.avatar_label.bind("<Button-1>", lambda e: self.change_avatar())

        # 提示
        ctk.CTkLabel(self.frame, text="点击图片以添加头像", font=("微软雅黑", 18), text_color="gray").grid(
            row=1, column=0, columnspan=2, pady=(0, 10)
        )

        # 配置列宽
        self.frame.grid_columnconfigure(0, weight=1)  # 标签列
        self.frame.grid_columnconfigure(1, weight=1)  # 输入框列

        # 计算机名称输入框
        ctk.CTkLabel(self.frame, text="计算机名称:", font=("微软雅黑", 18)).grid(row=2, column=0, padx=10, pady=(20, 5),
                                                                                 sticky="e")
        self.computer_name_entry = ctk.CTkEntry(
            self.frame, placeholder_text="输入计算机名称", width=200, height=40, font=("微软雅黑", 16)
        )
        self.computer_name_entry.insert(0, self.computer_name)
        self.computer_name_entry.grid(row=2, column=1, pady=(20, 5), padx=10, sticky="w")

        # 广播端口设置
        ctk.CTkLabel(self.frame, text="广播端口:", font=("微软雅黑", 18)).grid(row=3, column=0, padx=10, pady=(10, 5),
                                                                               sticky="e")
        self.broadcast_port_entry = ctk.CTkEntry(
            self.frame, placeholder_text="50000", width=200, height=40, font=("微软雅黑", 16)
        )
        self.broadcast_port_entry.insert(0, str(self.broadcast_port))
        self.broadcast_port_entry.grid(row=3, column=1, pady=(10, 5), padx=10, sticky="w")

        # TCP端口设置
        ctk.CTkLabel(self.frame, text="TCP 端口:", font=("微软雅黑", 18)).grid(row=4, column=0, padx=10, pady=(10, 5),
                                                                               sticky="e")
        self.tcp_port_entry = ctk.CTkEntry(
            self.frame, placeholder_text="50001", width=200, height=40, font=("微软雅黑", 16)
        )
        self.tcp_port_entry.insert(0, str(self.tcp_port))
        self.tcp_port_entry.grid(row=4, column=1, pady=(10, 5), padx=10, sticky="w")

        # 保存设置按钮
        save_button = ctk.CTkButton(
            self.frame, text="保存设置", command=self.save_settings, width=200, height=40,
            font=ctk.CTkFont(family="微软雅黑", size=14, weight="bold")
        )
        save_button.grid(row=5, column=0, columnspan=2, pady=(20, 10))

    def load_settings(self):
        """从本地文件加载配置。"""
        config_file = "data/config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.avatar_path = config.get("avatar_path", self.default_avatar_path)
                    self.computer_name = config.get("computer_name", self.computer_name)
                    self.broadcast_port = config.get("broadcast_port", self.broadcast_port)
                    self.tcp_port = config.get("tcp_port", self.tcp_port)
                    self.update_sidebar_avatar_callback(self.avatar_path, self.computer_name)
                    self.update_network_broadcast_callback(self.computer_name, self.broadcast_port, self.tcp_port)
            except Exception as e:
                print(f"加载配置失败: {e}")

    def save_settings(self):
        """保存计算机名称、广播端口和 TCP 端口设置。"""
        try:
            # 获取用户输入
            self.computer_name = self.computer_name_entry.get()
            self.broadcast_port = int(self.broadcast_port_entry.get())
            self.tcp_port = int(self.tcp_port_entry.get())

            # 验证端口范围
            if not (1 <= self.broadcast_port <= 65535 and 1 <= self.tcp_port <= 65535):
                raise ValueError("端口号必须在 1 到 65535 之间")

            # 更新广播和网络设置
            self.update_sidebar_avatar_callback(self.avatar_path, self.computer_name)
            self.update_network_broadcast_callback(
                self.computer_name, self.broadcast_port, self.tcp_port
            )

            # 保存配置到本地文件
            config = {
                "avatar_path": self.avatar_path,
                "computer_name": self.computer_name,
                "broadcast_port": self.broadcast_port,
                "tcp_port": self.tcp_port,
            }
            if not os.path.exists("data"):
                os.mkdir("data")
            with open("data/config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)

            CTkMessagebox(
                title="保存成功",
                message=f"设置已保存！\n计算机名称: {self.computer_name}\n广播端口: {self.broadcast_port}\nTCP 端口: {self.tcp_port}",
                icon="check", font=("微软雅黑", 14),
                option_1="确认"
            )
        except ValueError as e:
            CTkMessagebox(
                title="错误",
                message=f"保存失败！\n错误信息: {str(e)}",
                icon="error", font=("微软雅黑", 14),
                option_1="确认"
            )

    def change_avatar(self):
        """更改头像图片。"""
        file_path = filedialog.askopenfilename(
            title="选择头像",
            filetypes=[("图片文件", "*.png;*.jpg;*.jpeg"), ("所有文件", "*.*")]
        )
        if file_path:
            self.avatar_path = file_path
            avatar_image = self.reshaped_avatar()
            self.avatar_label.configure(image=avatar_image)
            self.update_sidebar_avatar_callback(self.avatar_path, self.computer_name)
            self.update_network_broadcast_callback(self.computer_name, self.broadcast_port, self.tcp_port)

    def reshaped_avatar(self):
        """更新头像显示为圆形图片。"""
        circular_image = create_circular_image(self.avatar_path, (150, 150))
        avatar_image = ctk.CTkImage(light_image=circular_image, dark_image=circular_image, size=(150, 150))
        return avatar_image

