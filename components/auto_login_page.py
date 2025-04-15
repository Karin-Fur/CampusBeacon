import os
import sys
import threading
import subprocess
import customtkinter as ctk
from tkinter import filedialog
from CTkMessagebox import CTkMessagebox
from components.CustomTools import CustomTopWindow
from PIL import Image
from components.CustomTools import CustomScrollableFrame, ToolTip, create_custom_help_button
import shutil
import traceback


class AutoLoginPage:
    def __init__(self, parent):
        """
        初始化自动登录页面
        
        Args:
            parent: 父窗口组件
        """
        self.parent = parent
        self.frame = ctk.CTkFrame(parent, fg_color="#111921", corner_radius=0)
        
        self.frame.columnconfigure(0, weight=0)
        self.frame.columnconfigure(1, weight=0)
        self.frame.columnconfigure(2, weight=1)
        
        # 创建左侧边框
        left_border = ctk.CTkFrame(self.frame, width=2, height=700, corner_radius=0)
        left_border.grid(row=0, column=0, sticky="ns", rowspan=2)  # 模拟单侧框线
        
        # 初始化学校列表
        self.school_list = [
            "安徽理工大学"
        ]
        
        # 初始化运营商列表
        self.isp_list = [
            "中国电信",
            "中国移动",
            "中国联通",
        ]
        
        # 默认脚本保存路径
        self.script_path = os.path.join(os.path.expanduser("~"), "Desktop")
        
        self.create_auto_login_page()
        
        # 检查开机自启状态
        self.check_autostart_status()
    
    def create_auto_login_page(self):
        """创建自动登录页面的UI组件"""
        # 页面标题
        try:
            image = ctk.CTkImage(
                light_image=Image.open("icons/login_light.png"),
                dark_image=Image.open("icons/login_dark.png"),
                size=(32, 32)
            )
            self.title_image = ctk.CTkLabel(self.frame, text="", image=image)
            self.title_image.grid(row=0, column=1, sticky="wns", padx=(10, 5), pady=5)
        except:
            # 如果图标不存在，则跳过
            pass
            
        self.title_label = ctk.CTkLabel(
            self.frame, 
            text="校园网自动登录",
            font=ctk.CTkFont("微软雅黑", size=24, weight="bold")
        )
        self.title_label.grid(row=0, column=2, sticky="wns", padx=10, pady=5)
        
        # 创建滚动框架
        self.content_frame = CustomScrollableFrame(
            self.frame, 
            fg_color="transparent", 
            height=620,
            border_color="#7D7D7D"
        )
        self.content_frame.grid(row=1, column=1, columnspan=3, sticky="nsew", padx=5, pady=5)
        
        # 添加说明文本
        self.description_frame = ctk.CTkFrame(self.content_frame, fg_color="#111921")
        self.description_label_1 = ctk.CTkLabel(
            self.description_frame, 
            text="-生成校园网自动登录程序，实现一键登录校园网，开发阶段仅适配本校",
            font=ctk.CTkFont("微软雅黑", size=16),
            text_color="#B4BDC4"
        )
        self.description_label_2 = ctk.CTkLabel(
            self.description_frame,
            text="-通过模拟网页请求实现，所有信息均储存在本地，无隐私问题",
            font=ctk.CTkFont("微软雅黑", size=16),
            text_color="#B4BDC4"
        )
        self.description_label_1.grid(row=0, column=0, sticky="w", padx=10, pady=0)
        self.description_label_2.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 10))
        self.description_frame.pack(fill="x", pady=(0, 10))
        
        # 学校选择
        self.school_frame = ctk.CTkFrame(self.content_frame, fg_color="#111921")
        self.school_label = ctk.CTkLabel(
            self.school_frame, 
            text="选择学校",
            font=ctk.CTkFont("微软雅黑", size=18)
        )
        self.school_combobox = ctk.CTkComboBox(
            self.school_frame,
            values=self.school_list,
            width=500,
            font=ctk.CTkFont("微软雅黑", size=16),
            dropdown_font=ctk.CTkFont("微软雅黑", size=16)
        )
        self.school_combobox.set(self.school_list[0])
        
        self.school_label.grid(row=0, column=0, sticky="wns", padx=(40, 10), pady=10)
        self.school_combobox.grid(row=0, column=1, sticky="wns", padx=5, pady=10)
        self.school_frame.columnconfigure(0, weight=0, minsize=310)
        self.school_frame.pack(fill="x", pady=(0, 10))
        
        # 学号输入
        self.student_id_frame = ctk.CTkFrame(self.content_frame, fg_color="#111921")
        self.student_id_label = ctk.CTkLabel(
            self.student_id_frame, 
            text="学号/账号",
            font=ctk.CTkFont("微软雅黑", size=18)
        )
        self.student_id_entry = ctk.CTkEntry(
            self.student_id_frame, 
            placeholder_text="请输入学号或账号", 
            width=500,
            font=ctk.CTkFont("微软雅黑", size=16)
        )
        
        self.student_id_label.grid(row=0, column=0, sticky="wns", padx=(40, 10), pady=10)
        self.student_id_entry.grid(row=0, column=1, sticky="wns", padx=5, pady=10)
        self.student_id_frame.columnconfigure(0, weight=0, minsize=310)
        self.student_id_frame.pack(fill="x", pady=(0, 10))
        
        # 密码输入
        self.password_frame = ctk.CTkFrame(self.content_frame, fg_color="#111921")
        self.password_label = ctk.CTkLabel(
            self.password_frame, 
            text="密码",
            font=ctk.CTkFont("微软雅黑", size=18)
        )
        self.password_entry = ctk.CTkEntry(
            self.password_frame, 
            placeholder_text="请输入密码", 
            width=500,
            font=ctk.CTkFont("微软雅黑", size=16),
            show="*"
        )
        
        self.password_label.grid(row=0, column=0, sticky="wns", padx=(40, 10), pady=10)
        self.password_entry.grid(row=0, column=1, sticky="wns", padx=5, pady=10)
        self.password_frame.columnconfigure(0, weight=0, minsize=310)
        self.password_frame.pack(fill="x", pady=(0, 10))
        
        # 运营商选择
        self.isp_frame = ctk.CTkFrame(self.content_frame, fg_color="#111921")
        self.isp_label = ctk.CTkLabel(
            self.isp_frame, 
            text="运营商",
            font=ctk.CTkFont("微软雅黑", size=18)
        )
        self.isp_combobox = ctk.CTkComboBox(
            self.isp_frame,
            values=self.isp_list,
            width=500,
            font=ctk.CTkFont("微软雅黑", size=16),
            dropdown_font=ctk.CTkFont("微软雅黑", size=16)
        )
        self.isp_combobox.set(self.isp_list[0])
        
        self.isp_label.grid(row=0, column=0, sticky="wns", padx=(40, 10), pady=10)
        self.isp_combobox.grid(row=0, column=1, sticky="wns", padx=5, pady=10)
        self.isp_frame.columnconfigure(0, weight=0, minsize=310)
        self.isp_frame.pack(fill="x", pady=(0, 10))
        
        # 脚本保存路径
        self.script_path_frame = ctk.CTkFrame(self.content_frame, fg_color="#111921")
        self.script_path_label = ctk.CTkLabel(
            self.script_path_frame, 
            text="保存路径",
            font=ctk.CTkFont("微软雅黑", size=18)
        )
        self.script_path_entry = ctk.CTkEntry(
            self.script_path_frame, 
            placeholder_text=self.script_path, 
            width=400,
            font=ctk.CTkFont("微软雅黑", size=16),
            state="normal"
        )
        self.script_path_entry.insert(0, self.script_path)
        
        self.script_path_button = ctk.CTkButton(
            self.script_path_frame, 
            text="浏览", 
            fg_color="#1F6AA5",
            hover_color="#144870",
            font=ctk.CTkFont("微软雅黑", size=16, weight="bold"),
            command=self.open_folder_dialog,
            width=80
        )
        
        # 禁用编辑：通过绑定事件来禁止用户输入
        self.script_path_entry.bind("<Key>", self.disable_entry)
        self.script_path_entry.bind("<Button-1>", self.disable_entry)  # 禁止点击编辑
        
        self.script_path_label.grid(row=0, column=0, sticky="wns", padx=(40, 10), pady=10)
        self.script_path_entry.grid(row=0, column=1, sticky="wns", padx=5, pady=10)
        self.script_path_button.grid(row=0, column=2, sticky="wns", padx=5, pady=10)
        self.script_path_frame.columnconfigure(0, weight=0, minsize=310)
        self.script_path_frame.pack(fill="x", pady=(0, 10))
        
        # 生成EXE按钮
        self.generate_frame = ctk.CTkFrame(self.content_frame, fg_color="#111921")
        self.generate_button = ctk.CTkButton(
            self.generate_frame, 
            text="生成EXE文件", 
            fg_color="#1F6AA5",
            hover_color="#144870",
            font=ctk.CTkFont("微软雅黑", size=18, weight="bold"),
            command=self.on_generate_exe_click,
            width=200,
            height=40
        )
        # 开机自启开关
        self.autostart_switch = ctk.CTkSwitch(
            self.generate_frame,
            text="开机自启",
            command=self.on_autostart_switch_change,
            font=ctk.CTkFont("微软雅黑", size=16)
        )
        # 说明
        self.auotostart_help = create_custom_help_button(self.generate_frame)
        ToolTip(self.auotostart_help, "开启后，自动登录程序将开机自启")
        self.generate_button.grid(row=0, column=0, sticky="nsew", padx=(220, 10), pady=20)
        self.autostart_switch.grid(row=0, column=1, sticky="wns", padx=(10, 5), pady=20)
        self.auotostart_help.grid(row=0, column=2, sticky="wns", padx=(5, 10), pady=20)
        self.generate_frame.pack(fill="x", pady=(0, 10))
        


    
    def disable_entry(self, event):
        """禁止用户直接编辑输入框"""
        return "break"
    
    def open_folder_dialog(self):
        """打开文件夹选择对话框"""
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.script_path = folder_path
            self.script_path_entry.configure(state="normal")
            self.script_path_entry.delete(0, "end")
            self.script_path_entry.insert(0, folder_path)
            self.script_path_entry.configure(state="readonly")
    
    def on_generate_exe_click(self):
        """生成EXE文件"""
        # 获取用户输入
        school = self.school_combobox.get()
        student_id = self.student_id_entry.get()
        password = self.password_entry.get()
        isp = self.isp_combobox.get()
        
        # 验证输入
        if not student_id or not password:
            CTkMessagebox(
                title="输入错误", 
                message="请填写完整的信息！",
                icon="cancel",
                option_1="确定",
                font=("微软雅黑", 14),
                title_color="#FF5555"
            )
            return
        
        # 显示进度提示
        self.show_progress_window()
        
        # 创建并启动线程
        threading.Thread(
            target=self.generate_exe_thread, 
            args=(school, student_id, password, isp),
            daemon=True
        ).start()
    
    def show_progress_window(self):
        """显示进度窗口"""
        self.progress_window = CustomTopWindow(self.parent)
        self.progress_window.title("生成进度")
        self.progress_window.configure(fg_color="#111921")
        
        # 设置窗口大小和位置
        screen_width = self.progress_window.winfo_screenwidth()
        screen_height = self.progress_window.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 180) // 2
        self.progress_window.geometry(f"400x180+{x}+{y}")
        
        # 设置窗口置顶
        self.progress_window.attributes("-topmost", True)
        
        # 添加标题
        ctk.CTkLabel(
            self.progress_window, 
            text="正在生成自动登录程序", 
            font=ctk.CTkFont("微软雅黑", size=18, weight="bold"),
            text_color="#FFFFFF"
        ).pack(pady=(20, 10))
        
        # 添加进度条
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_window, 
            width=300,
            progress_color="#1F6AA5"
        )
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        
        # 添加状态标签
        self.progress_label = ctk.CTkLabel(
            self.progress_window, 
            text="准备中...", 
            font=("微软雅黑", 14),
            text_color="#B4BDC4"
        )
        self.progress_label.pack(pady=10)
        
        # 禁用窗口关闭按钮
        self.progress_window.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # 更新窗口
        self.progress_window.update()
    
    def update_progress(self, message, progress=None):
        """更新进度信息"""
        if hasattr(self, 'progress_label') and self.progress_label:
            self.progress_label.configure(text=message)
            
            if progress is not None and hasattr(self, 'progress_bar') and self.progress_bar:
                self.progress_bar.set(progress)
            
            self.progress_window.update()
    
    def generate_exe_thread(self, school, student_id, password, isp):
        """在线程中生成EXE文件"""
        try:
            # 直接使用用户输入的信息生成EXE
            self.update_progress("准备生成登录程序...", 0.05)
            
            # 处理用户名（与运营商相关的后缀）
            username = student_id
            
            # 安徽理工大学特殊处理
            if school == "安徽理工大学":
                if isp == "中国电信":
                    if not student_id.endswith("@aust"):
                        username = f"{student_id}@aust"
                elif isp == "中国联通":
                    if not student_id.endswith("@unicom"):
                        username = f"{student_id}@unicom"
                elif isp == "中国移动":
                    if not student_id.endswith("@cmcc"):
                        username = f"{student_id}@cmcc"
            
            # 生成EXE文件
            exe_path = self.package_to_exe(school, username, password, isp)
            
            if not exe_path:
                self.show_error("生成登录程序失败")
                return
                
            # 成功完成
            self.update_progress("登录程序已成功生成！", 1.0)
            self.close_progress_window()
            
            # 提示用户生成成功
            CTkMessagebox(
                title="成功", 
                message=f"登录程序已成功生成\n位置: {exe_path}",
                icon="check",
                option_1="确定",
                font=("微软雅黑", 14)
            )
            
            # 打开资源管理器，显示文件位置
            subprocess.Popen(f'explorer /select,"{exe_path}"')
        except Exception as e:
            print(f"生成登录程序时出错: {str(e)}")
            self.show_error(f"生成登录程序失败: {str(e)}")
            
    def show_error(self, message):
        """显示错误信息并关闭进度窗口"""
        self.close_progress_window()
        CTkMessagebox(
            title="错误", 
            message=message,
            icon="cancel",
            option_1="确定",
            font=("微软雅黑", 14),
            title_color="#FF5555"
        )
    
    def package_to_exe(self, school, username, password, isp):
        """打包为EXE（使用预编译模板）"""
        try:
            # 查找预编译模板
            self.update_progress("正在查找预编译模板...", 0.1)
            
            # 获取资源路径 - 考虑多种可能路径
            possible_paths = []
            
            # 方法1: 获取项目主目录
            main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            possible_paths.append(os.path.join(main_dir, "resources", "auto_login_runner.exe"))
            
            # 方法2: 获取运行文件所在目录
            if getattr(sys, 'frozen', False):
                # 如果是打包后的环境
                exe_dir = os.path.dirname(sys.executable)
                possible_paths.append(os.path.join(exe_dir, "resources", "auto_login_runner.exe"))
                # PyInstaller临时文件夹中的资源
                base_dir = getattr(sys, '_MEIPASS', exe_dir)
                possible_paths.append(os.path.join(base_dir, "resources", "auto_login_runner.exe"))
            
            # 方法3: 尝试相对于当前文件的路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            possible_paths.append(os.path.join(current_dir, "resources", "auto_login_runner.exe"))
            
            # 方法4: 尝试临时目录中可能的路径
            temp_dir = os.environ.get('TEMP', '')
            if temp_dir:
                # 查找所有_MEI开头的文件夹
                for item in os.listdir(temp_dir):
                    if item.startswith('_MEI') and os.path.isdir(os.path.join(temp_dir, item)):
                        mei_path = os.path.join(temp_dir, item, "resources", "auto_login_runner.exe")
                        possible_paths.append(mei_path)
            
            # 尝试所有可能路径
            template_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    template_path = path
                    print(f"找到模板: {template_path}")
                    break
            
            if not template_path:
                paths_str = "\n".join(possible_paths)
                print(f"错误: 预编译模板不存在。尝试了以下路径:\n{paths_str}")
                self.update_progress("错误: 预编译模板不存在", 1.0)
                CTkMessagebox(
                    title="错误", 
                    message=f"预编译模板不存在，请确保resources目录中包含auto_login_runner.exe文件",
                    font=("微软雅黑", 14),
                    icon="cancel",
                    option_1="确定"
                )
                return None
            
            # 生成输出路径 - 使用用户设置的路径
            save_path = self.script_path_entry.get()
            if not save_path:
                # 如果用户未设置路径，则默认使用桌面
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                save_path = desktop_path
            
            final_exe_path = os.path.join(save_path, f"Auto_Login.exe")
            
            # 确保目录存在
            os.makedirs(os.path.dirname(final_exe_path), exist_ok=True)
            
            # 复制模板EXE到目标位置
            self.update_progress("正在创建登录程序...", 0.4)
            if os.path.exists(final_exe_path):
                os.remove(final_exe_path)
            shutil.copy2(template_path, final_exe_path)
            
            # 查找图标文件
            icon_paths = []
            # 项目图标目录
            icon_paths.append(os.path.join(main_dir, "icons", "window.ico"))
            # 资源目录中的图标
            if template_path:
                icon_paths.append(os.path.join(os.path.dirname(os.path.dirname(template_path)), "icons", "window.ico"))
            # 打包环境
            if getattr(sys, 'frozen', False):
                base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
                icon_paths.append(os.path.join(base_dir, "icons", "window.ico"))
            
            window_icon_path = ""
            for path in icon_paths:
                if os.path.exists(path):
                    window_icon_path = path
                    print(f"找到图标: {window_icon_path}")
                    break
            
            # 附加配置数据到EXE末尾
            self.update_progress("正在写入配置信息...", 0.7)
            with open(final_exe_path, 'ab') as f:
                f.write(b"\r\n[CONFIG]\r\n")
                f.write(f"USERNAME={username}\r\n".encode('utf-8'))
                f.write(f"PASSWORD={password}\r\n".encode('utf-8'))
                f.write(f"ISP={isp}\r\n".encode('utf-8'))
                f.write(f"SCHOOL={school}\r\n".encode('utf-8'))
                if window_icon_path:
                    f.write(f"ICON_PATH={window_icon_path}\r\n".encode('utf-8'))
                f.write(b"[END_CONFIG]\r\n")
            
            self.update_progress("完成", 1.0)
            
            return final_exe_path
        except Exception as e:
            print(f"创建登录程序时出错: {str(e)}")
            traceback.print_exc()
            self.update_progress("错误", 1.0)
            CTkMessagebox(
                title="错误", 
                message=f"创建登录程序时出错:\n{str(e)}",
                font=("微软雅黑", 14),
                icon="cancel",
                option_1="确定"
            )
            return None
    
    def set_autostart(self, enable=True):
        """设置或取消开机自启"""
        # 获取启动文件夹路径
        startup_folder = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")
        
        # 获取EXE文件路径
        exe_path = self.script_path_entry.get()
        if not exe_path.endswith(".exe"):
            exe_path = os.path.join(exe_path, "auto_login.exe")
        
        # 快捷方式路径
        shortcut_path = os.path.join(startup_folder, "校园网自动登录.lnk")
        
        if enable:
            # 检查EXE文件是否存在
            if not os.path.exists(exe_path):
                CTkMessagebox(
                    title="设置失败", 
                    message="请先生成EXE文件，确保Auto_Login.exe存在",
                    icon="cancel",
                    option_1="确定",
                    font=("微软雅黑", 14),
                    title_color="#FF5555"
                )
                # 重置开关状态
                self.autostart_switch.deselect()
                return False
                
            try:
                # 创建快捷方式
                import pythoncom
                from win32com.client import Dispatch
                
                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.Targetpath = exe_path
                shortcut.WorkingDirectory = os.path.dirname(exe_path)
                shortcut.Description = "校园网自动登录程序"
                shortcut.save()
                
                CTkMessagebox(
                    title="设置成功", 
                    message="已设置开机自启动！",
                    icon="check",
                    option_1="确定",
                    font=("微软雅黑", 14)
                )
                return True
            except Exception as e:
                CTkMessagebox(
                    title="设置失败", 
                    message=f"设置开机自启失败：{str(e)}",
                    icon="cancel",
                    option_1="确定",
                    font=("微软雅黑", 14),
                    title_color="#FF5555"
                )
                # 重置开关状态
                self.autostart_switch.deselect()
                return False
        else:
            # 删除快捷方式
            if os.path.exists(shortcut_path):
                try:
                    os.remove(shortcut_path)
                    CTkMessagebox(
                        title="设置成功", 
                        message="已取消开机自启动！",
                        icon="check",
                        option_1="确定",
                        font=("微软雅黑", 14)
                    )
                    return True
                except Exception as e:
                    CTkMessagebox(
                        title="设置失败", 
                        message=f"取消开机自启失败：{str(e)}",
                        icon="cancel",
                        option_1="确定",
                        font=("微软雅黑", 14),
                        title_color="#FF5555"
                    )
                    # 重置开关状态
                    self.autostart_switch.select()
                    return False
            return True
    
    def on_autostart_switch_change(self):
        """处理开机自启开关状态变化"""
        is_enabled = self.autostart_switch.get()
        self.set_autostart(is_enabled)
    
    def check_autostart_status(self):
        """检查开机自启状态"""
        # 获取启动文件夹路径
        startup_folder = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")
        
        # 快捷方式路径
        shortcut_path = os.path.join(startup_folder, "校园网自动登录.lnk")
        
        # 检查快捷方式是否存在
        if os.path.exists(shortcut_path):
            self.autostart_switch.select()
        else:
            self.autostart_switch.deselect()
    
    def close_progress_window(self):
        """关闭进度窗口"""
        if hasattr(self, 'progress_window') and self.progress_window:
            self.progress_window.destroy()
            self.progress_window = None
