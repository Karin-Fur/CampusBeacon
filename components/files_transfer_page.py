import json
import os
import re
import socket
import subprocess
import threading
import time
from tkinter import filedialog
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from PIL import Image
from PyQt5.QtCore import QFileInfo, QIODevice, QBuffer
from PyQt5.QtWidgets import QFileIconProvider
from components.CustomTools import CustomScrollableFrame
from components.avatar_page import create_circular_image


def get_file_icon(file_path, icon_time):
    """通过Pyqt获取文件图标"""
    file_info = QFileInfo(file_path)
    if file_info:
        icon_provider = QFileIconProvider()
        icon = icon_provider.icon(file_info)  # 获取文件图标
        pixmap = icon.pixmap(64, 64)  # 获取一个64x64大小的图标
        # 将QPixmap转换为QImage
        image = pixmap.toImage()  # 转换为QImage
        buffer = QBuffer()
        buffer.open(QIODevice.ReadWrite)  # 设置为可读写模式
        # 将QImage保存为PNG格式的字节数据
        if not os.path.exists("temp"):
            os.mkdir("temp")
        # 使用正则表达式提取所有数字
        numbers_only = ''.join(re.findall(r'\d', icon_time))
        image.save(f"temp/{numbers_only}.png", "PNG")
        icon_light = Image.open(f"temp/{numbers_only}.png")
        icon_dark = Image.open(f"temp/{numbers_only}.png")
    # 如果没有图标，返回默认图标
    else:
        icon_light = Image.open("icons/filetype/file_light.png")
        icon_dark = Image.open("icons/filetype/file_dark.png")

    return icon_light, icon_dark


class FilesTransferPage:
    def __init__(self, parent, device_ip, device_name, local_ip, local_device_name, update_files_list_callback,
                 update_received_files_info_callback):
        # 加载文件夹图标
        self.image = ctk.CTkImage(  # 加载unlink图标
            light_image=Image.open("icons/unlink_light.png"),
            dark_image=Image.open("icons/unlink_dark.png"),
            size=(50, 50),
        )
        self.update_files_list_callback = update_files_list_callback
        self.update_received_files_info_callback = update_received_files_info_callback
        self.device_ip = device_ip
        self.device_name = device_name
        self.local_ip = local_ip
        self.local_device_name = local_device_name
        self.tcp_port = 5001
        self.connection_ctrl = self.tcp_port + 1
        self.is_sending_or_receiving = False  # 控制是否正在发送或接收文件
        self.connection_state = False  # 连接状态
        self.terminate_check = False  # 主动终止连接检查
        self.server_disconnect_check = True
        self.disconnect_check = True
        self.recv_path = "file_recv/"
        if not os.path.exists("file_recv"):
            os.mkdir("file_recv")
        # 用于存储接收文件的信息
        self.received_files_info = []
        # 用于存储发送文件的信息
        self.sent_files_info = []
        # 文件传输缓冲区大小
        self.buffer_size = 1024  # 默认缓冲区大小为1024字节
        self.frame = ctk.CTkFrame(parent, fg_color="#1B2B3B")
        self.create_transfer_page()

    def create_transfer_page(self):
        while True:
            if self.disconnect_check and self.server_disconnect_check:
                break

        # 清空旧组件
        # 延迟执行销毁操作
        self.destroy_all_widgets(self.frame)
        # 创建标签并设置图片作为背景，确保标签填满
        self.is_sending_or_receiving = False  # 控制是否正在发送或接收文件
        self.connection_state = False  # 连接状态
        self.terminate_check = False  # 主动终止连接检查
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=0)
        self.frame.grid_columnconfigure(2, weight=0)
        self.file_page_label = ctk.CTkLabel(self.frame, text='\n\n\n未连接', image=self.image, height=640,
                                            bg_color="#1B2B3B",
                                            font=("微软雅黑", 16))
        self.file_page_label.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)  # 使标签铺满父容器

        self.frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)  # 设置grid布局

    def update_files_page(self, local_avatar_path):
        """更新文件传输页面内容"""
        self.connection_state = True  # 连接状态
        # 清空旧组件
        # 清空旧组件
        self.destroy_all_widgets(self.frame)
        # 创建新的图标
        circular_avatar = create_circular_image(local_avatar_path, (50, 50))
        device_icon = ctk.CTkImage(light_image=Image.open("icons/device_light.png"),
                                   dark_image=Image.open("icons/device_dark.png"), size=(50, 50))
        avatar_icon = ctk.CTkImage(light_image=circular_avatar,
                                   dark_image=circular_avatar, size=(50, 50))
        link_icon = ctk.CTkImage(light_image=Image.open("icons/link_light.png"),
                                 dark_image=Image.open("icons/link_dark.png"), size=(32, 32))

        # 第一行：设备名称、连接图标、本机名称和头像
        self.connected_device_label = ctk.CTkLabel(self.frame, text="\n\n\n" + self.device_name, image=device_icon,
                                                   bg_color="#1B2B3B", font=("微软雅黑", 16))
        self.connected_device_label.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.link = ctk.CTkLabel(self.frame, text="", image=link_icon, bg_color="#1B2B3B")
        self.link.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        self.local_device_label = ctk.CTkLabel(self.frame, text="\n\n\n" + self.local_device_name, image=avatar_icon,
                                               bg_color="#1B2B3B", font=("微软雅黑", 16))
        self.local_device_label.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)

        # 创建滚动框架
        self.file_list_frame = CustomScrollableFrame(self.frame, fg_color="transparent", height=500,
                                                     border_color="#7D7D7D", border_width=3)
        self.file_list_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=20, pady=(10, 5))
        # 分隔左右两列，区分发送/接收
        self.file_list_frame.grid_columnconfigure(0, weight=1)
        self.file_list_frame.grid_columnconfigure(1, weight=1)

        # 创建选择文件按钮
        self.select_file_button = ctk.CTkButton(self.frame, text="选择文件", command=self.select_file, height=40,
                                                font=ctk.CTkFont(family="微软雅黑", size=14, weight="bold"))
        self.select_file_button.grid(row=2, column=0, pady=(5, 5), sticky="e")
        # 创建打开接收路径按钮
        self.open_in_explorer_button = ctk.CTkButton(self.frame, text="打开接收目录",
                                                     command=self.path_in_explorer,
                                                     height=40,
                                                     font=ctk.CTkFont(family="微软雅黑", size=14, weight="bold"))
        self.open_in_explorer_button.grid(row=2, column=1, pady=(5, 5))
        # 创建断开连接按钮
        self.disconnect_button = ctk.CTkButton(self.frame, text="断开连接",
                                               command=lambda: self.disconnect(positive=True), height=40,
                                               font=ctk.CTkFont(family="微软雅黑", size=14, weight="bold"),
                                               fg_color="#E65A5A", hover_color="#B54747")
        self.disconnect_button.grid(row=2, column=2, pady=(5, 5), sticky="w")

        # 确保布局的行列配置
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_columnconfigure(2, weight=1)
        # 启动连接检查
        threading.Thread(target=self.connect_check, daemon=True).start()

    def update_local_info(self, device_name, device_ip, local_ip, local_device_name, tcp_port):
        """更新"""
        self.device_name = device_name
        self.device_ip = device_ip
        self.local_ip = local_ip
        self.local_device_name = local_device_name
        self.tcp_port = tcp_port

    def select_file(self):
        """选择文件并启动文件发送"""
        if self.is_sending_or_receiving:
            return  # 如果正在发送或接收文件，忽略请求

        file_path = filedialog.askopenfilename(title="选择要发送的文件")
        if file_path:
            # 启动文件发送线程
            self.is_sending_or_receiving = True
            threading.Thread(target=self.send_file, args=(file_path,)).start()

    def send_file(self, file_path):
        """发送文件并更新进度条"""
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((self.device_ip, self.tcp_port))

        try:
            # 获取文件元信息
            filename = os.path.basename(file_path)
            filesize = os.path.getsize(file_path)
            file_extension = os.path.splitext(filename)[1][1:].lower()  # 获取文件扩展名
            send_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            # 创建文件卡片并获取进度条
            file_card, progress_bar, speed_label, time_label = (
                self.create_file_card(file_path, filename, filesize, send_time, is_sent=True))

            # 发送文件元信息
            file_meta = {"filename": filename, "filesize": filesize}
            file_meta_json = json.dumps(file_meta) + "\n"
            client_socket.send(file_meta_json.encode('utf-8'))

            # 发送文件内容
            bytes_sent = 0
            bytes_before = 0  # 计算实时速率
            start_time = time.time()  # 获取开始时间
            with open(file_path, "rb") as f:
                while chunk := f.read(self.buffer_size):
                    client_socket.sendall(chunk)
                    bytes_sent += len(chunk)

                    # 每次发送时，检查是否已过1秒，若过了1秒，更新进度条
                    elapsed_time = time.time() - start_time
                    if elapsed_time >= 1:  # 如果已经过了1秒
                        start_time = time.time()  # 重置计时器
                        progress_bar.set(bytes_sent / filesize)  # 更新进度条
                        # 计算传输速率
                        temp = bytes_sent - bytes_before
                        speed = temp / elapsed_time  # bytes per second
                        speed_str = self.format_speed(speed)
                        bytes_before = bytes_sent
                        speed_label.configure(text=f"{speed_str}")  # 更新速率标签
            print(f"文件 {filename} 发送完成！")
            # 记录文件信息
            file_info_dict = {
                "filename": filename,
                "filesize": self.format_size(filesize),
                "send_time": send_time,
                "file_extension": file_extension,
                "file_path": file_path,  # 保存文件路径
                "status": "安全性未知"
            }

            # 将发送的文件信息添加到列表中
            self.sent_files_info.append(file_info_dict)
            print(f"文件信息已保存：{file_info_dict}")
            # 更新卡片状态为已发送
            progress_bar.grid_forget()  # 隐藏进度条
            time_label.configure(text=send_time, font=("微软雅黑", 12))
            speed_label.configure(text=f"发送完成", text_color="green")  # 隐藏速率标签

        except Exception as e:
            print(f"发送文件时出错：{e}")
        finally:
            client_socket.close()
            self.is_sending_or_receiving = False

    def receive_file(self, client_socket):
        """接收文件并更新进度条"""
        # 接收前获取最新的接收文件信息
        self.load_received_files_info()
        try:
            # 接收文件元信息
            file_info = ""
            while True:
                char = client_socket.recv(1).decode('utf-8')  # 逐字节接收
                if char == "\n":  # 换行符作为结束标志
                    break
                file_info += char

            print(f"接收到的文件元信息：{file_info}")
            file_meta = json.loads(file_info)  # 解析 JSON
            filename = file_meta["filename"]
            filesize = int(file_meta["filesize"])
            # 获取文件的扩展名
            basename, file_extension = os.path.splitext(filename)
            # 判断文件是否重名
            i = 1
            while True:
                for info in self.received_files_info:
                    if info["filename"] == filename:
                        filename = f"{basename}({i}){file_extension}"
                        i += 1
                        break  # 退出循环，从头判断
                else:  # 正常退出循环，表明不存在重名，循环结束
                    break
            # 获取文件路径
            file_path = os.path.join(self.recv_path, filename)
            print(f"准备接收文件：{filename}, 大小：{filesize} 字节")

            # 创建文件卡片并获取进度条
            file_card, progress_bar, speed_label, time_label, file_icon_label = self.create_file_card(file_path,
                                                                                                      filename,
                                                                                                      filesize,
                                                                                                      '0',
                                                                                                      is_sent=False)

            # 接收文件内容
            file_path = os.path.join(self.recv_path, filename)
            bytes_received = 0
            bytes_before = 0  # 计算实时速率
            start_time = time.time()  # 获取开始时间
            with open(file_path, "wb") as f:
                while bytes_received < filesize:
                    chunk = client_socket.recv(self.buffer_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    bytes_received += len(chunk)

                    # 每次接收时，检查是否已过1秒，若过了1秒，更新进度条
                    elapsed_time = time.time() - start_time
                    if elapsed_time >= 1:  # 如果已经过了1秒
                        start_time = time.time()  # 重置计时器
                        progress_bar.set(bytes_received / filesize)  # 更新进度条
                        # 计算传输速率
                        temp = bytes_received - bytes_before
                        speed = temp / elapsed_time  # bytes per second
                        speed_str = self.format_speed(speed)
                        bytes_before = bytes_received
                        speed_label.configure(text=f"{speed_str}")  # 更新速率标签

            print(f"文件 {filename} 接收完成！")

            # 获取文件的绝对路径，并将路径分隔符统一为 /
            absolute_file_path = os.path.abspath(file_path).replace(os.sep, '/')

            # 记录文件信息
            receive_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())  # 格式化时间
            file_info_dict = {
                "filename": filename,
                "filesize": self.format_size(filesize),
                "receive_time": receive_time,
                "file_extension": file_extension,
                "file_path": absolute_file_path,  # 使用绝对路径，并统一为 /
                "status": "安全性未知"
            }

            # 将接收到的文件信息添加到列表中
            self.received_files_info.append(file_info_dict)
            print(f"文件信息已保存：{file_info_dict}")
            print(f"测试接收列表:{self.received_files_info}")

            # 更新卡片状态为已接收
            progress_bar.grid_forget()  # 隐藏进度条
            time_label.configure(text=receive_time, font=("微软雅黑", 12))
            speed_label.configure(text=f"接收完成", text_color="green")  # 隐藏速率标签

            # 更新图标
            icon_light, icon_dark = get_file_icon(file_path, receive_time)
            file_icon = ctk.CTkImage(light_image=icon_light, dark_image=icon_dark, size=(64, 64))
            file_icon_label.configure(file_card, text="", bg_color="#1E1F22",
                                      image=file_icon)

            # 更新文件管理界面的接收文件列表
            self.update_received_files_info_callback(self.received_files_info)
            # 更新文件管理界面卡片
            self.update_files_list_callback()

        except Exception as e:
            print(f"接收文件时出错：{e}")
        finally:
            self.is_sending_or_receiving = False
            client_socket.close()

    def format_size(self, size_in_bytes):
        """格式化文件大小为 KB/MB/GB"""
        if size_in_bytes < 1024:
            return f"{size_in_bytes} B"
        elif size_in_bytes < 1024 ** 2:
            return f"{size_in_bytes / 1024:.2f} KB"
        elif size_in_bytes < 1024 ** 3:
            return f"{size_in_bytes / 1024 ** 2:.2f} MB"
        else:
            return f"{size_in_bytes / 1024 ** 3:.2f} GB"

    def format_speed(self, speed_in_bytes_per_second):
        """格式化传输速度为 B/s, KB/s, MB/s"""
        if speed_in_bytes_per_second < 1024:
            return f"{speed_in_bytes_per_second:.2f} B/s"
        elif speed_in_bytes_per_second < 1024 ** 2:
            return f"{speed_in_bytes_per_second / 1024:.2f} KB/s"
        elif speed_in_bytes_per_second < 1024 ** 3:
            return f"{speed_in_bytes_per_second / 1024 ** 2:.2f} MB/s"
        else:
            return f"{speed_in_bytes_per_second / 1024 ** 3:.2f} GB/s"

    def start_server(self):
        """启动服务端监听客户端请求"""

        # 尝试绑定端口
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 重用端口
        server_socket.bind((self.local_ip, self.tcp_port))
        server_socket.listen(1)
        server_socket.settimeout(0.5)
        print(f"等待客户端连接... {self.local_ip}:{self.tcp_port}")
        self.server_disconnect_check = False
        try:
            while self.connection_state:
                if not self.connection_state:
                    break
                try:
                    client_socket, _ = server_socket.accept()
                    print("客户端已连接")
                    self.receive_file(client_socket)
                except socket.timeout:
                    continue
        except OSError as e:
            print(f"端口绑定失败: {e}")
            if e.errno == 10048:
                print(f"端口 {self.tcp_port} 已被占用，请关闭占用该端口的应用程序")
        except Exception as e:
            print(f"服务端启动错误: {e}")
        finally:
            server_socket.close()
            self.server_disconnect_check = True
            print("文件接收端已停止")

    def start_server_thread(self):
        threading.Thread(target=self.start_server, daemon=True).start()

    def create_file_card(self, file_path, file_name, file_size, icon_time, is_sent):
        """创建文件信息卡片，显示文件图标、名称、大小和进度条"""

        file_size_str = self.format_size(file_size)

        # 创建卡片框架
        file_card = ctk.CTkFrame(self.file_list_frame, fg_color="#1E1F22", corner_radius=10)
        if is_sent:
            file_card.grid(column=1, sticky="nse", padx=5, pady=5)
        else:
            file_card.grid(column=0, sticky="nsw", padx=5, pady=5)
        # 预设文件图标
        file_icon = ctk.CTkImage(light_image=Image.open("icons/filetype/file_light.png"),
                                 dark_image=Image.open("icons/filetype/file_dark.png"), size=(64, 64))

        # 如果是发送文件，直接从文件路径获取图标
        if is_sent:
            icon_light, icon_dark = get_file_icon(file_path, icon_time)
            file_icon = ctk.CTkImage(light_image=icon_light, dark_image=icon_dark, size=(64, 64))

        # 文件图标和文件名称
        file_icon_label = ctk.CTkLabel(file_card, text="", bg_color="#1E1F22",
                                       image=file_icon)
        file_name_label = ctk.CTkLabel(file_card, text=file_name, bg_color="#1E1F22",
                                       font=ctk.CTkFont(family="微软雅黑", size=18, weight="bold"))
        file_icon_label.grid(row=0, column=0, padx=10, pady=10, sticky="we", rowspan=2)
        file_name_label.grid(row=0, column=1, padx=5, pady=(10, 0), sticky="ws", columnspan=4)

        # 文件大小标签 (第一行，右对齐)
        size_label = ctk.CTkLabel(file_card, text=f"{file_size_str}", bg_color="#1E1F22", font=("微软雅黑", 12),
                                  text_color="gray")
        size_label.grid(row=1, column=1, padx=5, pady=(0, 5), sticky="wn", columnspan=4)

        # 进度条
        time_label = ctk.CTkLabel(file_card, text="", width=250, text_color="gray")
        time_label.grid(row=2, column=1, padx=10, pady=(0, 10), sticky="ws")
        progress_bar = ctk.CTkProgressBar(file_card, width=300)
        progress_bar.grid(row=2, column=0, padx=10, pady=(0, 10), columnspan=4)
        progress_bar.set(0)  # 初始进度

        # 传输速率标签
        speed_label = ctk.CTkLabel(file_card, text="0B/s", bg_color="#1E1F22", font=("微软雅黑", 12), width=70)
        speed_label.grid(row=2, column=4, padx=10, pady=(0, 10))

        # 绑定卡片事件，跳转本地路径，设置悬停样式
        file_card.bind("<Button-1>", lambda e: self.file_in_explorer(file_path))
        file_card.bind("<Enter>", lambda e: file_card.configure(fg_color="#263844"))
        file_card.bind("<Leave>", lambda e: file_card.configure(fg_color="#1E1F22"))
        # 给卡片中所有子组件绑定事件和悬停样式
        for child in file_card.winfo_children():
            child.bind("<Button-1>", lambda e: self.file_in_explorer(file_path))
            child.bind("<Enter>", lambda e: file_card.configure(fg_color="#263844"))
            child.bind("<Leave>", lambda e: file_card.configure(fg_color="#1E1F22"))
        # 对齐方式设置
        file_card.grid_columnconfigure(0, weight=1)  # 第一列占据大部分宽度
        file_card.grid_columnconfigure(1, weight=3)  # 第二列（文件大小）右对齐

        # 发送方发送完毕无需更新图标，接收方更新
        if is_sent:
            return file_card, progress_bar, speed_label, time_label
        else:
            return file_card, progress_bar, speed_label, time_label, file_icon_label

    def path_in_explorer(self):
        try:
            os.startfile(os.path.abspath(self.recv_path))
        except Exception as e:
            print(f"打开目录时发生错误:{e}")

    def file_in_explorer(self, file_path):
        if os.path.exists(file_path):
            # 使用 subprocess 打开资源管理器，并选中文件
            subprocess.run(['explorer', '/select,', file_path.replace("/", "\\")])
        else:
            CTkMessagebox(title="错误", message=f"文件已经移动或删除", icon="cancel",
                          option_1="确认", font=("微软雅黑", 14))

    def disconnect(self, positive, close_event=False):
        if close_event:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.device_ip, self.connection_ctrl))
            client_socket.sendall("DISCONNECT".encode('UTF-8'))
            return
        if positive:
            msg = CTkMessagebox(title="断开连接", icon="question",
                                message=f"确认断开与设备{self.device_name}({self.device_ip})的连接吗？",
                                font=("微软雅黑", 14),
                                option_1="确认", option_2="取消")
            response = msg.get()
            if response == "取消":
                return
            elif response == "确认":
                #   主动终止
                self.terminate_check = True
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((self.device_ip, self.connection_ctrl))
                client_socket.sendall("DISCONNECT".encode('UTF-8'))
        # 断开连接
        self.connection_state = False
        device_name = self.device_name
        device_ip = self.device_ip
        self.device_name = None
        self.device_ip = None
        self.create_transfer_page()
        CTkMessagebox(title="断开连接", message=f"与设备{device_name}({device_ip})的连接已断开", icon="info",
                      option_1="确认", font=("微软雅黑", 14))

    def connect_check(self):
        """检查连接状态"""
        # 尝试绑定端口
        print("正在检查连接状态")
        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 重用端口
        listen_socket.bind((self.local_ip, self.connection_ctrl))
        listen_socket.listen(1)
        listen_socket.settimeout(0.5)
        command = ""
        self.disconnect_check = False
        try:
            while self.connection_state:
                if not self.connection_state:
                    break
                try:
                    conn, addr = listen_socket.accept()
                    command = conn.recv(1024).decode('utf-8')  # 逐字节接收
                    if command:
                        break
                except socket.timeout:
                    continue
            print(command)
        except Exception as e:
            print(f"检查连接状态时出错:{e}")
        finally:
            listen_socket.close()
            self.disconnect_check = True
            if command == "DISCONNECT" and not self.terminate_check:
                self.disconnect(positive=False)
            print("连接已断开")

    def save_received_files_info(self):
        """保存接收到的文件信息到本地 JSON 文件"""
        if not os.path.exists("data"):
            os.mkdir("data")
        try:
            with open('data/received_files_info.json', 'w', encoding='utf-8') as f:
                json.dump(self.received_files_info, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存接收文件信息失败: {e}")

    def load_received_files_info(self):
        """从本地 JSON 文件加载接收到的文件信息"""
        if os.path.exists('data/received_files_info.json'):
            try:
                with open('data/received_files_info.json', 'r', encoding='utf-8') as f:
                    self.received_files_info = json.load(f)
            except Exception as e:
                print(f"加载接收文件信息失败: {e}")

    def destroy_all_widgets(self, frame):
        # 遍历框架中的所有子控件
        for widget in frame.winfo_children():
            # 如果子控件本身是一个框架，则递归销毁
            if isinstance(widget, ctk.CTkFrame):
                self.destroy_all_widgets(widget)  # 递归销毁子框架
            widget.destroy()  # 销毁子控件
