import sys
import customtkinter as ctk
from PyQt5.QtWidgets import QApplication
from CTkMessagebox import CTkMessagebox
from components.files_transfer_page import FilesTransferPage
from components.sidebar import Sidebar
from components.avatar_page import AvatarPage
from components.device_discovery_page import DeviceDiscoveryPage
from components.device_network import DeviceNetwork
from components.files_manage_page import FilesManagePage
from components.settings_page import SettingsPage
from components.ai_chat_page import AIChatPage
from components.auto_login_page import AutoLoginPage
from components.about_page import AboutPage
from components.CustomTools import set_help_icon
import socket
from PIL import Image

def get_local_ip():
    """获取本地 IP 地址。"""
    try:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    except:
        return "无法获取 IP"


def on_close():
    """关闭窗口时执行的操作"""
    if app.files_transfer_page.connection_state:
        app.files_transfer_page.disconnect(positive=False, close_event=True)
    app.quit()  # 退出主事件循环


class CampusBeacon(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 初始化图标
        self.init_icons()
        
        # 创建 QApplication 实例
        self.app = QApplication(sys.argv)  # 确保只有一个 QApplication 实例
        # 初始化默认信息
        self.device_name = "MyDevice"
        self.avatar_path = "icons/default_avatar.png"
        self.local_ip = get_local_ip()
        self.connected_device = None  # 用于存储当前连接的设备信息
        self.broadcast_port = 50000  # 默认广播端口
        self.tcp_port = 50001  # 默认TCP端口
        # 窗口设置
        self.title("CampusBeacon")
        self.geometry("1280x720")
        ctk.set_appearance_mode("dark")
        self.configure(fg_color="#111921")
        self.grid_columnconfigure(0, weight=0)  # 左侧栏的宽度固定
        self.grid_columnconfigure(1, weight=1)  # 右侧内容动态扩展
        self.grid_rowconfigure(0, weight=1)

        # 初始化侧边栏
        self.sidebar = Sidebar(self, self.switch_page)
        self.sidebar.frame.grid(row=0, column=0, sticky="ns")

        # 初始化主内容区
        self.main_frame = ctk.CTkFrame(self, fg_color="#1B2B3B", corner_radius=10)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # 页面存储（每个页面是一个 Frame）
        self.pages = {}
        self.create_pages()

        # 默认显示第一页
        self.show_page("avatar")
    
    def init_icons(self):
        """初始化图标并设置到CustomTools中"""
        try:
            # 构建帮助图标
            help_icon = ctk.CTkImage(
                light_image=Image.open("icons/help_light.png"),
                dark_image=Image.open("icons/help_dark.png"),
                size=(18, 18)
            )
            
            # 设置到CustomTools中
            set_help_icon(help_icon)
            print("成功初始化帮助图标")
        except Exception as e:
            print(f"初始化图标时出错: {str(e)}")

    def create_pages(self):
        """创建不同的页面"""
        # 首先创建设置页面，以便其他页面可以使用设置
        self.pages["settings"] = self.create_settings_page()
        
        # 然后创建文件管理页面
        self.pages["files"] = self.create_files_page()
        
        # 创建其他页面
        self.pages["discover"] = self.create_discover_page()
        self.pages["transfer"] = self.create_transfer_page()
        self.pages["ai_chat"] = self.create_ai_chat_page()
        self.pages["auto_login"] = self.create_auto_login_page()
        self.pages["about"] = self.create_about_page()
        
        # 创建头像页面
        avatar_page = AvatarPage(self.main_frame, self.update_avatar_path,
                                 update_network_broadcast_callback=self.update_broadcast_info)
        self.pages["avatar"] = avatar_page.frame
        
        # 更新所有配置
        self.settings_page.update_all_config()
        
        # 如果启用了自动清理日志，检查并清理日志
        if self.settings_page.auto_clear_logs:
            self.files_manage_page.auto_clear_logs = True
            self.files_manage_page.check_and_clear_logs_on_startup()

    def create_discover_page(self):
        """创建设备发现页面"""
        # 先创建 device_discovery_page
        self.device_discovery_page = DeviceDiscoveryPage(
            self.main_frame,
            start_search_callback=self.start_broadcast_and_listen,
            stop_search_callback=self.stop_broadcast_and_listen,
            switch_to_file_page_callback=self.switch_to_file_page,
            local_ip=self.local_ip,  # 本地设备 IP
            local_device_name=self.device_name  # 本地设备名称
        )

        # 创建 device_network，但不立即设置回调
        self.device_network = DeviceNetwork(
            device_name=self.device_name,
            ip=self.local_ip,
            broadcast_port=self.broadcast_port,
            tcp_port=self.tcp_port,
            switch_to_file_page_callback=self.switch_to_file_page,
            toggle_search_call_back=self.passive_toggle_search  # 延迟设置回调
        )

        # 在 device_discovery_page 初始化后，设置 device_network 的回调
        self.device_network.on_device_discovered = self.device_discovery_page.add_device
        return self.device_discovery_page.frame

    def create_transfer_page(self):
        self.files_transfer_page = FilesTransferPage(
            self.main_frame,
            device_ip="",
            device_name="",
            local_ip=self.local_ip,
            local_device_name=self.device_name,
            update_files_list_callback=self.files_manage_page.update_files_list,
            update_received_files_info_callback=self.files_manage_page.update_received_files_info
        )
        # 缓存清理
        if self.settings_page.auto_clear_temp:
            self.files_manage_page.clear_temp()
        return self.files_transfer_page.frame

    def create_files_page(self):
        self.files_manage_page = FilesManagePage(self.main_frame)
        return self.files_manage_page.frame

    def create_settings_page(self):
        """创建设置页面"""
        self.settings_page = SettingsPage(self.main_frame, update_config_callback=self.update_config)
        return self.settings_page.frame

    def create_ai_chat_page(self):
        """创建 AI 对话页面"""
        self.ai_chat_page = AIChatPage(self.main_frame, self)
        return self.ai_chat_page.frame

    def create_auto_login_page(self):
        """创建校园网自动登录页面"""
        self.auto_login_page = AutoLoginPage(self.main_frame)
        return self.auto_login_page.frame

    def create_about_page(self):
        """创建关于页面"""
        self.about_page = AboutPage(self.main_frame)
        return self.about_page.frame

    def update_broadcast_info(self, device_name, broadcast_port, tcp_port):
        """更新设备广播和 TCP 端口信息"""
        self.device_name = device_name
        self.device_network.device_name = device_name
        self.device_network.broadcast_port = int(broadcast_port)  # 确保端口为整数
        self.device_network.tcp_port = int(tcp_port)
        # 更新设备发现页的信息
        self.device_discovery_page.update_local_info(self.local_ip, device_name)

        print(f"广播信息已更新：设备名称={device_name}, 广播端口={broadcast_port}, TCP端口={tcp_port}")

    def start_broadcast_and_listen(self):
        """启动广播和监听"""
        if self.files_transfer_page.connection_state:
            CTkMessagebox(title="错误", message="请先断开当前连接", icon="cancel", option_1="确认", font=("微软雅黑", 14))
            return False
        else:
            self.device_network.broadcast_device_info()
            self.device_network.listen_for_devices()
            self.device_network.start_tcp_listener()  # 启动TCP监听
            return True

    def stop_broadcast_and_listen(self):
        """停止广播和监听"""
        if self.device_network:
            self.device_network.stop()


    def switch_to_file_page(self, device_name, device_ip, tcp_port):
        """切换到文件传输页面并显示连接的设备信息"""
        # 停止广播和监听
        self.stop_broadcast_and_listen()

        # 保存连接设备信息
        self.connected_device = (device_name, device_ip)

        # 获取本设备的信息
        local_name = self.device_name  # 本设备名称
        local_avatar = self.avatar_path  # 本设备头像路径
        print(local_name, local_avatar, device_name, device_ip)
        # 切换到文件页面并更新内容
        self.files_transfer_page.update_local_info(device_ip=device_ip, device_name=device_name,
                                                   local_ip=self.local_ip, local_device_name=local_name,
                                                   tcp_port=tcp_port)
        self.files_transfer_page.update_files_page(local_avatar)
        # 启动接收监听
        self.files_transfer_page.start_server_thread()
        # 通过侧边栏方法跳转界面，实现界面与侧边栏选中按钮同步更新
        Sidebar.select_button(self.sidebar, self.sidebar.buttons[1], "transfer")
        # 输出连接成功的日志
        print(f"已连接到设备：{device_name} ({device_ip})")

    def passive_toggle_search(self):
        if hasattr(self, 'device_discovery_page') and self.device_discovery_page.frame:
            # 确保 device_discovery_page 已初始化
            self.device_discovery_page.toggle_search()
            self.device_discovery_page.clear_device_list(manual=False)  # 清空设备列表

    def update_avatar_path(self, new_avatar_path, computer_name):
        """更新头像路径，把路径信息存在主类中"""
        self.avatar_path = new_avatar_path  # 更新头像路径
        self.device_name = computer_name  # 更新计算机名称

        # 更新侧边栏头像
        self.sidebar.update_avatar(self.avatar_path, self.device_name)

    def update_config(self, recv_path=None, api_key=None, deepseek_api_key=None, auto_delete_label=None, auto_clear_logs=None, buffer_size=None):
        """更新配置信息"""
        if recv_path is not None:
            self.files_transfer_page.receive_path = recv_path
            print(f"接收路径已更新: {recv_path}")
            
        if api_key is not None:
            # 更新 VirusTotal API 密钥
            if hasattr(self, 'files_manage_page'):
                self.files_manage_page.api_key = api_key
            print("VirusTotal API 密钥已更新")
            
        if deepseek_api_key is not None:
            # 更新 DeepSeek API 密钥
            if hasattr(self, 'ai_chat_page') and hasattr(self.ai_chat_page, 'api'):
                self.ai_chat_page.api.api_key = deepseek_api_key
                print("DeepSeek API 密钥已更新")
            
        if auto_delete_label is not None:
            # 更新自动删除标签设置
            if hasattr(self, 'files_manage_page'):
                self.files_manage_page.auto_delete_flag = auto_delete_label
            print(f"自动删除标签设置已更新: {auto_delete_label}")
            
        if auto_clear_logs is not None:
            # 更新自动清理日志设置
            if hasattr(self, 'files_manage_page'):
                self.files_manage_page.auto_clear_logs = auto_clear_logs
            print(f"自动清理日志设置已更新: {auto_clear_logs}")
            
        if buffer_size is not None:
            # 更新文件传输缓冲区大小
            if hasattr(self, 'files_transfer_page'):
                self.files_transfer_page.buffer_size = buffer_size
            print(f"文件传输缓冲区大小已更新: {buffer_size} 字节")
            
    def show_page(self, page_name):
        """显示指定页面"""
        # 移除当前显示的页面
        for page in self.pages.values():
            if isinstance(page, ctk.CTkFrame) or hasattr(page, 'grid_forget'):
                page.grid_forget()

        # 显示新页面
        if page_name in self.pages:
            if isinstance(self.pages[page_name], ctk.CTkFrame) or hasattr(self.pages[page_name], 'grid'):
                self.pages[page_name].grid(row=0, column=0, sticky="nsew")
            else:
                print(f"错误：页面 {page_name} 不是有效的Frame对象")

    def switch_page(self, page_name):
        """切换页面"""
        self.show_page(page_name)


if __name__ == "__main__":
    app = CampusBeacon()
    app.protocol("WM_DELETE_WINDOW", on_close)
    # 锁定窗口大小
    app.resizable(False, False)
    app.mainloop()
