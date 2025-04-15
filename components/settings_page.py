import json
import os
from tkinter import filedialog
import requests
import customtkinter as ctk
from components.CustomTools import CustomScrollableFrame
from CTkMessagebox import CTkMessagebox
from PIL import Image
from components.CustomTools import ToolTip, create_custom_help_button
from components.network_utils import disable_network_connectivity_check, get_network_connectivity_check_status


class SettingsPage:
    def __init__(self, parent, update_config_callback):
        self.previous_text = {}
        self.update_config_callback = update_config_callback
        self.frame = ctk.CTkFrame(parent, fg_color="#111921", corner_radius=0)
        self.frame.columnconfigure(0, weight=0)
        self.frame.columnconfigure(1, weight=0)
        self.frame.columnconfigure(2, weight=1)
        left_border = ctk.CTkFrame(self.frame, width=2, height=700, corner_radius=0)
        left_border.grid(row=0, column=0, sticky="ns", rowspan=2)  # 模拟单侧框线
        self.settings = {}
        if self.load_settings_info():
            self.recv_path = self.settings['recv_path']
            self.key = self.settings['key']
            self.deepseek_api_key = self.settings.get('deepseek_api_key', '')
            self.auto_delete_label = self.settings['auto_delete_label']
            self.auto_clear_temp = self.settings['auto_clear_temp']
            self.auto_clear_logs = self.settings.get('auto_clear_logs', False)  # 新增日志清除设置，默认为False
            # 文件传输缓冲区大小设置
            self.buffer_size = self.settings.get('buffer_size', 1024)  # 默认1024字节
        else:
            self.recv_path = os.path.abspath("file_recv").replace(os.sep, '/')
            self.key = ''
            self.deepseek_api_key = ''
            self.auto_delete_label = False
            self.auto_clear_temp = False
            self.auto_clear_logs = False  # 新增日志清除设置
            self.buffer_size = 1024  # 默认1024字节
            self.settings = {'recv_path': self.recv_path, 'key': self.key, 'deepseek_api_key': self.deepseek_api_key,
                             'auto_delete_label': self.auto_delete_label,
                             'auto_clear_temp': self.auto_clear_temp,
                             'auto_clear_logs': self.auto_clear_logs,  # 添加到设置字典
                             'buffer_size': self.buffer_size}  # 添加缓冲区大小设置
        self.create_settings_page()

    def create_settings_page(self):
        image = ctk.CTkImage(light_image=Image.open("icons/settings.png"),
                             dark_image=Image.open("icons/settings.png"),
                             size=(32, 32)
                             )
        self.title_image = ctk.CTkLabel(self.frame, text="", image=image)
        self.title_label = ctk.CTkLabel(self.frame, text="设置",
                                        font=ctk.CTkFont("微软雅黑", size=24, weight="bold"))
        self.settings_list_frame = CustomScrollableFrame(self.frame, fg_color="transparent", height=620,
                                                         border_color="#7D7D7D")
        self.title_image.grid(row=0, column=1, sticky="wns", padx=(10, 5), pady=5)
        self.title_label.grid(row=0, column=2, sticky="wns", padx=10, pady=5)
        self.settings_list_frame.grid(row=1, column=1, columnspan=3, sticky="nsew", padx=5, pady=5)

        # 标题：密钥设置
        self.basic_title_frame = ctk.CTkFrame(self.settings_list_frame, fg_color="#111921")
        self.basic_title_label = ctk.CTkLabel(self.basic_title_frame, text="密钥设置",
                                              font=ctk.CTkFont("微软雅黑", size=20, weight="bold"))
        self.basic_title_label.grid(row=0, column=0, sticky="wns", padx=10, pady=10)
        self.basic_title_frame.pack(fill="x")

        #  VirusTotal Key设置
        self.key_frame = ctk.CTkFrame(self.settings_list_frame, fg_color="#111921")
        self.key_label = ctk.CTkLabel(self.key_frame, text="VirusTotal Key",
                                      font=ctk.CTkFont("微软雅黑", size=18))
        self.key_entry = ctk.CTkEntry(self.key_frame, placeholder_text=self.key, width=500,
                                      font=ctk.CTkFont("微软雅黑", size=16), state="normal")
        self.save_key_button = ctk.CTkButton(self.key_frame, text="保存", fg_color="#1F6AA5", hover_color="#144870",
                                             font=ctk.CTkFont("微软雅黑", size=16, weight="bold"),
                                             command=self.save_key,
                                             width=80)
        self.key_entry.bind("<Button-1>", lambda event: self.on_focus_in(event, "key", self.key))
        self.key_entry.bind("<FocusOut>", lambda event: self.on_focus_out(event, self.key_entry, "key"))
        self.key_label.grid(row=0, column=0, sticky="wns", padx=(40, 10), pady=10)
        self.key_entry.grid(row=0, column=1, sticky="wns", padx=5, pady=10)
        self.save_key_button.grid(row=0, column=2, sticky="wns", padx=5, pady=10)
        self.key_frame.columnconfigure(0, weight=0, minsize=310)
        self.key_frame.pack(fill="x")

        # DeepSeek API Key设置
        self.deepseek_key_frame = ctk.CTkFrame(self.settings_list_frame, fg_color="#111921")
        self.deepseek_key_label = ctk.CTkLabel(self.deepseek_key_frame, text="DeepSeek API Key",
                                               font=ctk.CTkFont("微软雅黑", size=18))
        self.deepseek_key_entry = ctk.CTkEntry(self.deepseek_key_frame, placeholder_text=self.deepseek_api_key,
                                               width=500,
                                               font=ctk.CTkFont("微软雅黑", size=16), state="normal")
        self.save_deepseek_key_button = ctk.CTkButton(self.deepseek_key_frame, text="保存", fg_color="#1F6AA5",
                                                      hover_color="#144870",
                                                      font=ctk.CTkFont("微软雅黑", size=16, weight="bold"),
                                                      command=self.save_deepseek_key,
                                                      width=80)
        self.deepseek_key_entry.bind("<Button-1>", lambda event: self.on_focus_in(event, "deepseek_api_key",
                                                                                  self.deepseek_api_key))
        self.deepseek_key_entry.bind("<FocusOut>", lambda event: self.on_focus_out(event, self.deepseek_key_entry,
                                                                                   "deepseek_api_key"))
        self.deepseek_key_label.grid(row=0, column=0, sticky="wns", padx=(40, 10), pady=10)
        self.deepseek_key_entry.grid(row=0, column=1, sticky="wns", padx=5, pady=10)
        self.save_deepseek_key_button.grid(row=0, column=2, sticky="wns", padx=5, pady=10)
        self.deepseek_key_frame.columnconfigure(0, weight=0, minsize=310)
        self.deepseek_key_frame.pack(fill="x")

        # 分隔线
        self.bottom_border_frame = ctk.CTkFrame(self.settings_list_frame, fg_color="#111921")
        self.bottom_border = ctk.CTkFrame(self.bottom_border_frame, height=2, width=1200, corner_radius=0)
        self.bottom_border.grid(row=0, column=0, sticky="nsew", padx=10, pady=15)
        self.bottom_border_frame.pack(fill="x")

        # 标题：传输设置
        self.transfer_title_frame = ctk.CTkFrame(self.settings_list_frame, fg_color="#111921")
        self.transfer_title_label = ctk.CTkLabel(self.transfer_title_frame, text="传输设置",
                                                 font=ctk.CTkFont("微软雅黑", size=20, weight="bold"))
        self.transfer_title_label.grid(row=0, column=0, sticky="wns", padx=10, pady=10)
        self.transfer_title_frame.pack(fill="x")

        # 接收路径设置
        self.recv_path_frame = ctk.CTkFrame(self.settings_list_frame, fg_color="#111921")
        self.recv_path_label = ctk.CTkLabel(self.recv_path_frame, text="接收路径",
                                            font=ctk.CTkFont("微软雅黑", size=18))
        self.recv_path_entry = ctk.CTkEntry(self.recv_path_frame, placeholder_text=self.recv_path, width=500,
                                            font=ctk.CTkFont("微软雅黑", size=16), state="normal")
        self.recv_path_button = ctk.CTkButton(self.recv_path_frame, text="浏览", fg_color="#1F6AA5",
                                              hover_color="#144870",
                                              font=ctk.CTkFont("微软雅黑", size=16, weight="bold"),
                                              command=self.open_folder_dialog,
                                              width=80)

        # 禁用编辑：通过绑定事件来禁止用户输入
        self.recv_path_entry.bind("<Key>", self.disable_entry)
        self.recv_path_entry.bind("<Button-1>", self.disable_entry)  # 禁止点击编辑
        self.recv_path_label.grid(row=0, column=0, sticky="wns", padx=(40, 10), pady=10)
        self.recv_path_entry.grid(row=0, column=1, sticky="wns", padx=5, pady=10)
        self.recv_path_button.grid(row=0, column=2, sticky="wns", padx=5, pady=10)
        self.recv_path_frame.columnconfigure(0, weight=0, minsize=310)
        self.recv_path_frame.pack(fill="x")

        # 缓冲区大小设置
        self.buffer_size_frame = ctk.CTkFrame(self.settings_list_frame, fg_color="#111921")
        self.buffer_size_label = ctk.CTkLabel(self.buffer_size_frame, text="传输缓冲区大小",
                                              font=ctk.CTkFont("微软雅黑", size=18))

        # 创建单选按钮框架
        self.buffer_size_radio_frame = ctk.CTkFrame(self.buffer_size_frame, fg_color="transparent")

        # 创建单选按钮变量
        self.buffer_size_var = ctk.IntVar(value=self.buffer_size)

        # 根据当前缓冲区大小设置相应的单选按钮
        if self.buffer_size not in [1024, 4096, 8192]:
            self.buffer_size = 1024  # 如果不是预设值，则默认设为1KB
            self.buffer_size_var.set(1024)
            self.settings['buffer_size'] = 1024
            self.save_settings_info()

        # 创建三个单选按钮
        self.radio_1kb = ctk.CTkRadioButton(self.buffer_size_radio_frame, text="1024B",
                                            variable=self.buffer_size_var, value=1024,
                                            font=ctk.CTkFont("微软雅黑", size=16))
        self.radio_4kb = ctk.CTkRadioButton(self.buffer_size_radio_frame, text="4096B",
                                            variable=self.buffer_size_var, value=4096,
                                            font=ctk.CTkFont("微软雅黑", size=16))
        self.radio_8kb = ctk.CTkRadioButton(self.buffer_size_radio_frame, text="8192B",
                                            variable=self.buffer_size_var, value=8192,
                                            font=ctk.CTkFont("微软雅黑", size=16))

        # 布局单选按钮
        self.radio_1kb.grid(row=0, column=0, padx=20, pady=5, sticky="w")
        self.radio_4kb.grid(row=0, column=1, padx=20, pady=5, sticky="w")
        self.radio_8kb.grid(row=0, column=2, padx=20, pady=5, sticky="w")

        # 保存按钮
        self.save_buffer_size_button = ctk.CTkButton(self.buffer_size_frame, text="保存", fg_color="#1F6AA5",
                                                     hover_color="#144870",
                                                     font=ctk.CTkFont("微软雅黑", size=16, weight="bold"),
                                                     command=self.save_buffer_size,
                                                     width=80)

        # 帮助按钮
        self.buffer_size_help = create_custom_help_button(self.buffer_size_frame)
        ToolTip(self.buffer_size_help,
                text="缓冲区大小影响文件传输速度，\n较大的缓冲区在良好网络环境下可提高传输效率，\n但在不稳定网络中可能导致传输失败")

        # 布局
        self.buffer_size_label.grid(row=0, column=0, sticky="wns", padx=(40, 10), pady=10)
        self.buffer_size_radio_frame.grid(row=0, column=1, sticky="wns", padx=5, pady=10)
        self.save_buffer_size_button.grid(row=0, column=2, sticky="wns", padx=(85, 5), pady=10)
        self.buffer_size_help.grid(row=0, column=3, sticky="wns", padx=5, pady=10)
        self.buffer_size_frame.columnconfigure(0, weight=0, minsize=310)
        self.buffer_size_frame.pack(fill="x")

        # 分隔线
        self.bottom_border_frame_2 = ctk.CTkFrame(self.settings_list_frame, fg_color="#111921")
        self.bottom_border = ctk.CTkFrame(self.bottom_border_frame_2, height=2, width=1200, corner_radius=0)
        self.bottom_border.grid(row=0, column=0, sticky="nsew", padx=10, pady=15)
        self.bottom_border_frame_2.pack(fill="x")

        # 标题：自动化
        self.auto_title_frame = ctk.CTkFrame(self.settings_list_frame, fg_color="#111921")
        self.auto_title_label = ctk.CTkLabel(self.auto_title_frame, text="自动化",
                                             font=ctk.CTkFont("微软雅黑", size=20, weight="bold"))
        self.auto_title_label.grid(row=0, column=0, sticky="wns", padx=10, pady=10)
        self.auto_title_frame.pack(fill="x")

        # 自动清除威胁设置
        self.auto_frame = ctk.CTkFrame(self.settings_list_frame, fg_color="#111921")
        self.auto_label = ctk.CTkLabel(self.auto_frame, text="威胁清除",
                                       font=ctk.CTkFont("微软雅黑", size=18))
        self.auto_switch = ctk.CTkSwitch(self.auto_frame, text="", width=40, height=30)
        if self.auto_delete_label:
            self.auto_switch.select()
        else:
            self.auto_switch.deselect()
        self.auto_switch.bind("<Button-1>", self.auto_delete)
        self.auto_help = create_custom_help_button(self.auto_frame)
        ToolTip(self.auto_help, text="打开时，当检测到风险文件系统会自动删除")
        self.auto_label.grid(row=0, column=0, sticky="wns", padx=(40, 10), pady=5)
        self.auto_switch.grid(row=0, column=1, sticky="wns", padx=5, pady=5)
        self.auto_help.grid(row=0, column=2, sticky="wns", padx=5, pady=5)
        self.auto_frame.columnconfigure(0, weight=0, minsize=220)
        self.auto_frame.pack(fill="x")

        # 自动清除缓存设置
        self.temp_clean_frame = ctk.CTkFrame(self.settings_list_frame, fg_color="#111921")
        self.temp_label = ctk.CTkLabel(self.temp_clean_frame, text="缓存清除",
                                       font=ctk.CTkFont("微软雅黑", size=18))
        self.temp_switch = ctk.CTkSwitch(self.temp_clean_frame, text="", width=40, height=30)
        self.temp_switch.bind("<Button-1>", self.auto_clear)
        if self.auto_clear_temp:
            self.temp_switch.select()
        else:
            self.temp_switch.deselect()
        self.temp_help = create_custom_help_button(self.temp_clean_frame)
        ToolTip(self.temp_help, text="打开时，程序会在运行时清理图片缓存")
        self.temp_label.grid(row=0, column=0, sticky="wns", padx=(40, 10), pady=5)
        self.temp_switch.grid(row=0, column=1, sticky="wns", padx=5, pady=5)
        self.temp_help.grid(row=0, column=2, sticky="wns", padx=5, pady=5)
        self.temp_clean_frame.columnconfigure(0, weight=0, minsize=220)
        self.temp_clean_frame.pack(fill="x")

        # 自动清除日志设置
        self.logs_clean_frame = ctk.CTkFrame(self.settings_list_frame, fg_color="#111921")
        self.logs_label = ctk.CTkLabel(self.logs_clean_frame, text="日志清除",
                                       font=ctk.CTkFont("微软雅黑", size=18))
        self.logs_switch = ctk.CTkSwitch(self.logs_clean_frame, text="", width=40, height=30)
        self.logs_switch.bind("<Button-1>", self.auto_clear_logs_toggle)
        if self.auto_clear_logs:
            self.logs_switch.select()
        else:
            self.logs_switch.deselect()
        self.logs_help = create_custom_help_button(self.logs_clean_frame)
        ToolTip(self.logs_help,
                text="打开时，当文件被从列表中移除后，自动清除对应的检测日志，\n并在启动时清理意外操作导致的孤日志")
        self.logs_label.grid(row=0, column=0, sticky="wns", padx=(40, 10), pady=5)
        self.logs_switch.grid(row=0, column=1, sticky="wns", padx=5, pady=5)
        self.logs_help.grid(row=0, column=2, sticky="wns", padx=5, pady=5)
        self.logs_clean_frame.columnconfigure(0, weight=0, minsize=220)
        self.logs_clean_frame.pack(fill="x")

        # 网络连接指示器活动测试设置
        self.network_check_frame = ctk.CTkFrame(self.settings_list_frame, fg_color="#111921")
        self.network_check_label = ctk.CTkLabel(self.network_check_frame, text="无感认证",
                                               font=ctk.CTkFont("微软雅黑", size=18))
        self.network_check_switch = ctk.CTkSwitch(self.network_check_frame, text="", width=40, height=30)
        self.network_check_switch.bind("<Button-1>", self.toggle_network_check)

        # 检查当前系统设置状态并更新开关
        current_status = get_network_connectivity_check_status()
        if current_status is not None and current_status:
            self.network_check_switch.select()
        else:
            self.network_check_switch.deselect()

        self.network_check_help = create_custom_help_button(self.network_check_frame)
        ToolTip(self.network_check_help,
                text="打开时，将禁用Windows网络连接指示器活动测试，\n可以禁止自动弹出校园网认证页，配合登录脚本使用\n(需要管理员权限)")
        self.network_check_label.grid(row=0, column=0, sticky="wns", padx=(40, 10), pady=5)
        self.network_check_switch.grid(row=0, column=1, sticky="wns", padx=5, pady=5)
        self.network_check_help.grid(row=0, column=2, sticky="wns", padx=5, pady=5)
        self.network_check_frame.columnconfigure(0, weight=0, minsize=220)
        self.network_check_frame.pack(fill="x")

    def save_key(self):
        if self.test_virustotal_api_key(self.key_entry.get()):
            self.key = self.key_entry.get()
            self.settings['key'] = self.key
            self.save_settings_info()
            self.previous_text['key'] = self.key
            self.update_config_callback(self.recv_path, self.key)

    def save_deepseek_key(self):
        self.deepseek_api_key = self.deepseek_key_entry.get()
        self.settings['deepseek_api_key'] = self.deepseek_api_key
        self.save_settings_info()
        self.previous_text['deepseek_api_key'] = self.deepseek_api_key
        self.update_config_callback(self.recv_path, self.key, self.deepseek_api_key)
        self.frame.focus()

    def save_buffer_size(self):
        self.buffer_size = self.buffer_size_var.get()
        self.settings['buffer_size'] = self.buffer_size
        self.save_settings_info()
        self.previous_text['buffer_size'] = str(self.buffer_size)
        self.update_config_callback(buffer_size=self.buffer_size)
        print(f"缓冲区大小已更新为: {self.buffer_size} 字节")
        CTkMessagebox(title="成功", message=f"缓冲区大小已设置为 {self.buffer_size} 字节", icon="check",
                      option_1="确认", font=("微软雅黑", 14))

    def test_virustotal_api_key(self, api_key):
        # VirusTotal API URL
        url = "https://www.virustotal.com/api/v3/urls"
        payload = {"url": "https://www.google.com"}
        # 设置请求头，包含API Key
        headers = {
            "x-apikey": api_key
        }

        try:
            # 发送请求并检查响应
            response = requests.post(url, headers=headers, data=payload)

            # 检查响应状态码
            if response.status_code == 200:
                CTkMessagebox(title="成功", message="保存成功", icon="check", option_1="确认", font=("微软雅黑", 14))
                return True
            elif response.status_code == 403:
                CTkMessagebox(title="失败", message="非法或未授权的API Key", icon="cancel", option_1="确认",
                              font=("微软雅黑", 14))
                return False
            else:
                CTkMessagebox(title="失败", message=f"出现了错误:{response.status_code}", icon="cancel",
                              option_1="确认",
                              font=("微软雅黑", 14))
                return False
        except Exception as e:
            print(f"Error: {e}")
            return False

    def open_folder_dialog(self):
        # 打开文件夹选择对话框
        folder_path = filedialog.askdirectory(title="选择一个文件夹")

        if folder_path:
            self.recv_path = folder_path
            self.recv_path_entry.configure(placeholder_text=folder_path)
            self.update_config_callback(self.recv_path, self.key)
            self.settings['recv_path'] = self.recv_path
            self.save_settings_info()

    def auto_delete(self, event):
        value = self.auto_switch.get()  # 获取开关的当前状态（True 或 False）
        if value:
            self.auto_delete_label = True
            self.update_config_callback(auto_delete_label=self.auto_delete_label)
            print("自动删除已打开")
        else:
            self.auto_delete_label = False
            self.update_config_callback(auto_delete_label=self.auto_delete_label)
            print("自动删除已关闭")
        self.settings['auto_delete_label'] = self.auto_delete_label
        self.save_settings_info()

    def auto_clear(self, event):
        value = self.temp_switch.get()
        if value:
            self.auto_clear_temp = True
            print("自动清理已打开")
        else:
            self.auto_clear_temp = False
            print("自动清理已关闭")
        self.settings['auto_clear_temp'] = self.auto_clear_temp
        self.save_settings_info()

    def auto_clear_logs_toggle(self, event):
        value = self.logs_switch.get()
        if value:
            self.auto_clear_logs = True
            print("日志自动清理已打开")
        else:
            self.auto_clear_logs = False
            print("日志自动清理已关闭")
        self.settings['auto_clear_logs'] = self.auto_clear_logs
        self.save_settings_info()

    def toggle_network_check(self, event):
        # 获取当前开关状态
        value = self.network_check_switch.get()
        
        if value:
            # 尝试禁用网络连接指示器活动测试
            success = disable_network_connectivity_check(True)
            if success:
                print("网络连接指示器活动测试已禁用")
                CTkMessagebox(title="成功", message="已开启无感认证", icon="check",
                              option_1="确认", font=("微软雅黑", 14))
            else:
                # 如果失败，恢复开关状态
                self.network_check_switch.deselect()
                CTkMessagebox(title="提示", message="操作需要管理员权限，请在弹出的UAC窗口中确认", icon="info",
                              option_1="确认", font=("微软雅黑", 14))
        else:
            # 尝试启用网络连接指示器活动测试
            success = disable_network_connectivity_check(False)
            if success:
                print("网络连接指示器活动测试已启用")
                CTkMessagebox(title="成功", message="已禁用无感认证", icon="check",
                              option_1="确认", font=("微软雅黑", 14))
            else:
                # 如果失败，恢复开关状态
                self.network_check_switch.select()
                CTkMessagebox(title="提示", message="操作需要管理员权限，请在弹出的UAC窗口中确认", icon="info",
                              option_1="确认", font=("微软雅黑", 14))

    def save_settings_info(self):
        """保存接收到的文件信息到本地 JSON 文件"""
        if not os.path.exists("data"):
            os.mkdir("data")
        try:
            with open('data/settings_info.json', 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存接收文件信息失败: {e}")

    def load_settings_info(self):
        """从本地 JSON 文件加载接收到的文件信息"""
        if os.path.exists('data/settings_info.json'):
            try:
                with open('data/settings_info.json', 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
            except Exception as e:
                print(f"加载接收文件信息失败: {e}")
            return True
        else:
            return False

    def update_all_config(self):
        self.update_config_callback(recv_path=self.recv_path,
                                    api_key=self.key,
                                    deepseek_api_key=self.deepseek_api_key,
                                    auto_delete_label=self.auto_delete_label,
                                    auto_clear_logs=self.auto_clear_logs,
                                    buffer_size=self.buffer_size)

    def disable_entry(self, event):
        # 使其余输入框失焦
        self.frame.focus()
        return "break"  # 阻止事件，禁止输入

    # 用于处理焦点事件的函数
    def on_focus_out(self, event, entry, entry_name):
        text = self.previous_text.get(entry_name)
        entry.delete(0, "end")
        self.frame.focus()
        entry.configure(placeholder_text=text)
        print("失焦")

    # 用于保存原始文本
    def on_focus_in(self, event, entry_name, text):
        print("聚焦")
        self.previous_text[entry_name] = text  # 保存当前文本

    def auto_update(self):
        self.update_config_callback()
