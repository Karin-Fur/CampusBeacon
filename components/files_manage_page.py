import json
import os
import re
import subprocess
from datetime import datetime
from CTkMessagebox import CTkMessagebox
import customtkinter as ctk
from PIL import Image
from components.virus_total import VirusTotalThread
from components.CustomTools import ToolTip
from components.CustomTools import CustomScrollableFrame
from components.CustomTools import CustomTopWindow


class FilesManagePage:
    def __init__(self, parent):

        self.file_card_dict = {}
        self.file_log_dict = {}
        self.received_files_info = []
        self.path_info = []
        self.deleted_time_stamps = []
        self.auto_delete_flag = False
        self.auto_clear_logs = False
        self.is_scanning = False
        self.one_click = False
        self.api_key = ''
        self.frame = ctk.CTkFrame(parent, fg_color="#111921", corner_radius=0)
        self.frame.columnconfigure(0, weight=0)
        self.frame.columnconfigure(1, weight=0)
        self.frame.columnconfigure(2, weight=1)
        left_border = ctk.CTkFrame(self.frame, width=2, height=700, corner_radius=0)
        left_border.grid(row=0, column=0, sticky="ns", rowspan=2)  # 模拟单侧框线
        self.create_files_manage_page()

    def create_files_manage_page(self):
        image = ctk.CTkImage(light_image=Image.open("icons/folder.png"),
                             dark_image=Image.open("icons/folder.png"),
                             size=(32, 32)
                             )
        self.title_image = ctk.CTkLabel(self.frame, text="", image=image)
        self.title_label = ctk.CTkLabel(self.frame, text="文件管理",
                                        font=ctk.CTkFont("微软雅黑", size=24, weight="bold"))
        self.file_list_frame = CustomScrollableFrame(self.frame, fg_color="transparent", height=620,
                                                     border_color="#7D7D7D")
        scan_icon = ctk.CTkImage(light_image=Image.open("icons/shield_light.png"),
                                 dark_image=Image.open("icons/shield_dark.png"), size=(24, 24))
        self.scan_button = ctk.CTkButton(self.frame, text="一键检测", image=scan_icon, fg_color="#1391DD",
                                         font=ctk.CTkFont(family="微软雅黑", size=14, weight="bold"),
                                         width=60, height=24,
                                         command=self.security_scan_all)
        remove_icon = ctk.CTkImage(light_image=Image.open("icons/trash_light.png"),
                                   dark_image=Image.open("icons/trash_dark.png"), size=(24, 24))
        self.remove_button = ctk.CTkButton(self.frame, text="", image=remove_icon, fg_color="#B54747", width=24,
                                           hover_color="#A64141", command=self.remove_danger_files)
        ToolTip(self.remove_button, "移除风险文件")
        self.title_image.grid(row=0, column=1, sticky="wns", padx=(10, 5), pady=5)
        self.title_label.grid(row=0, column=2, sticky="wns", padx=10, pady=5)
        self.scan_button.grid(row=0, column=3, padx=5, pady=5, sticky="ens")
        self.remove_button.grid(row=0, column=4, padx=5, pady=5, sticky="ens")
        self.file_list_frame.grid(row=1, column=1, columnspan=4, sticky="nsew", padx=5, pady=5)

        #  加载本地配置
        self.load_file_log_dict()
        self.load_received_files_info()
        self.load_deleted_time_stamps()
        #  更新界面
        self.update_files_list()
        self.check_and_clear_logs_on_startup()

    def create_files_card(self, filename, filesize, file_path, receive_time, status):
        file_card = ctk.CTkFrame(self.file_list_frame, fg_color="#111921", corner_radius=10)
        file_card.grid_columnconfigure(4, weight=1)
        # 尝试从缓存中读取图标
        numbers_only = ''.join(re.findall(r'\d', receive_time))
        icon_path = f"temp/{numbers_only}.png"
        if os.path.exists(icon_path):
            icon_light = Image.open(f"temp/{numbers_only}.png")
            icon_dark = Image.open(f"temp/{numbers_only}.png")
        else:
            icon_light = Image.open("icons/filetype/file_light.png")
            icon_dark = Image.open("icons/filetype/file_dark.png")
        file_icon = ctk.CTkImage(light_image=icon_light, dark_image=icon_dark, size=(64, 64))

        # 文件图标和文件名称
        file_icon_label = ctk.CTkLabel(file_card, text="", bg_color="#111921",
                                       image=file_icon)
        file_name_label = ctk.CTkLabel(file_card, text=filename, bg_color="#111921",
                                       font=ctk.CTkFont(family="微软雅黑", size=18, weight="bold"))
        time_label = ctk.CTkLabel(file_card, text=receive_time, bg_color="#111921", text_color="gray",
                                  font=("微软雅黑", 12))
        size_label = ctk.CTkLabel(file_card, text=filesize, bg_color="#111921", font=("微软雅黑", 12),
                                  text_color="gray")
        status_label = ctk.CTkLabel(file_card, text=status, bg_color="#111921", font=("微软雅黑", 12))

        if status == "文件已移除":
            file_name_label.configure(font=ctk.CTkFont(family="微软雅黑", size=18, weight="bold", overstrike=True),
                                      text_color="gray")
            status_label.configure(text_color="gray")
        elif status == "文件安全":
            status_label.configure(font=ctk.CTkFont("微软雅黑", 12, weight="bold"), text_color="green")
        elif status == "文件危险":
            status_label.configure(font=ctk.CTkFont("微软雅黑", 12, weight="bold"), text_color="red")
        elif status == "已自动清除威胁":
            file_name_label.configure(font=ctk.CTkFont(family="微软雅黑", size=18, weight="bold", overstrike=True),
                                      text_color="gray")
            status_label.configure(font=ctk.CTkFont("微软雅黑", 12, weight="bold"), text_color="#1391DD")
        elif status == "文件过大":
            status_label.configure(font=ctk.CTkFont("微软雅黑", 12, weight="bold"), text_color="orange")
        file_icon_label.grid(row=0, column=0, padx=10, pady=10, sticky="we", rowspan=2)
        file_name_label.grid(row=0, column=1, padx=5, pady=(10, 0), sticky="ws", columnspan=3)
        time_label.grid(row=1, column=1, padx=5, pady=5)
        size_label.grid(row=1, column=2, padx=5, pady=5)
        status_label.grid(row=1, column=3, padx=5, pady=5)

        #   名称标签
        file_icon_label.tag = "file_icon_label"
        file_name_label.tag = "file_name_label"
        time_label.tag = "time_label"
        size_label.tag = "size_label"
        status_label.tag = "status_label"

        # 悬停样式
        file_card.bind("<Button-1>", lambda e: self.file_in_explorer(file_path))
        file_card.bind("<Leave>", lambda e: file_card.configure(fg_color="#111921"))
        file_card.bind("<Enter>", lambda e: file_card.configure(fg_color="#1E1F22"))
        # 给卡片中所有子组件绑定事件和悬停样式
        for child in file_card.winfo_children():
            child.bind("<Button-1>", lambda e: self.file_in_explorer(file_path))
            child.bind("<Leave>", lambda e: file_card.configure(fg_color="#111921"))
            child.bind("<Enter>", lambda e: file_card.configure(fg_color="#1E1F22"))

        delete_icon = ctk.CTkImage(light_image=Image.open("icons/x_light.png"),
                                   dark_image=Image.open("icons/x_dark.png"), size=(24, 24))
        delete_button = ctk.CTkButton(file_card, text="", image=delete_icon, fg_color="transparent",
                                      command=lambda: self.delete_file(filename, status, file_path), width=24,
                                      height=24)
        delete_button.grid(row=0, column=6, padx=2, pady=5, sticky="e", rowspan=2)
        ToolTip(delete_button, "移除")

        report_icon = ctk.CTkImage(light_image=Image.open("icons/report_light.png"),
                                   dark_image=Image.open("icons/report_dark.png"), size=(22, 22))
        report_button = ctk.CTkButton(file_card, text="", image=report_icon, fg_color="transparent",
                                      command=lambda: self.create_report_frame(filename, file_path, icon_path),
                                      width=24, height=24)
        ToolTip(report_button, "查看报告")
        report_button.grid(row=0, column=5, padx=2, pady=5, sticky="e", rowspan=2)

        file_scan_icon = ctk.CTkImage(light_image=Image.open("icons/shield_light.png"),
                                      dark_image=Image.open("icons/shield_dark.png"), size=(22, 22))
        file_scan_button = ctk.CTkButton(file_card, text="", image=file_scan_icon, fg_color="transparent",
                                         command=lambda: self.scan_single_file(file_path),
                                         width=24, height=24)
        file_scan_button.grid(row=0, column=4, padx=2, pady=5, sticky="e", rowspan=2)
        ToolTip(file_scan_button, "检测文件")

        file_card.pack(fill="x")
        return file_card

    def update_files_list(self):
        """更新文件列表"""
        for info in self.received_files_info:
            filename = info.get('filename')
            filesize = info.get('filesize')
            receive_time = info.get('receive_time')
            file_path = info.get('file_path')
            # 判断文件是否还存在
            if not os.path.exists(file_path):
                if info["status"] != "已自动清除威胁":
                    info["status"] = "文件已移除"
                self.save_received_files_info()
            status = info.get('status')
            # 判断卡片是否添加过
            frame = self.file_card_dict.get(f"{filename}")
            if not frame:
                # 创建新卡片，并以键值对的形式存在字典中
                file_card = self.create_files_card(filename, filesize, file_path, receive_time, status)
                self.file_card_dict[f"{filename}"] = file_card
            else:
                self.update_file_card(frame, status)

    def update_received_files_info(self, received_files_info):
        self.received_files_info = received_files_info
        self.save_received_files_info()

    def get_path_from_received(self, received_files_info):
        if self.path_info:
            self.path_info.clear()
        for info in received_files_info:
            if not info.get('status') == "文件已移除":
                self.path_info.append(info.get('file_path'))

    def update_file_card(self, file_card, status):
        file_name_label = self.find_by_tag(file_card, "file_name_label")
        status_label = self.find_by_tag(file_card, "status_label")
        if status == "文件已移除":
            if file_name_label and status_label:
                file_name_label.configure(
                    font=ctk.CTkFont(family="微软雅黑", size=18, weight="bold", overstrike=True),
                    text_color="gray")
                status_label.configure(text=status, font=ctk.CTkFont("微软雅黑", 12, weight="bold"), text_color="gray")
            else:
                print("获取组件失败")
        elif status == "文件安全":
            if file_name_label and status_label:
                status_label.configure(text=status, font=ctk.CTkFont("微软雅黑", 12, weight="bold"), text_color="green")
            else:
                print("获取组件失败")
        elif status == "文件危险":
            if file_name_label and status_label:
                status_label.configure(text=status, font=ctk.CTkFont("微软雅黑", 12, weight="bold"), text_color="red")
        elif status == "已自动清除威胁":
            if file_name_label and status_label:
                file_name_label.configure(
                    font=ctk.CTkFont(family="微软雅黑", size=18, weight="bold", overstrike=True),
                    text_color="gray")
                status_label.configure(text=status, font=ctk.CTkFont("微软雅黑", 12, weight="bold"), text_color="#1391DD")
            else:
                print("获取组件失败")
        elif status == "文件过大":
            if file_name_label and status_label:
                status_label.configure(text=status, font=ctk.CTkFont("微软雅黑", 12, weight="bold"), text_color="orange")
            else:
                print("获取组件失败")

    def find_by_tag(self, frame, tag):
        for child in frame.winfo_children():
            if child.tag == tag:
                return child
        else:
            return None

    def delete_file(self, filename, status, file_path):
        if status != "文件已移除" and status != "已自动清除威胁":
            msg = CTkMessagebox(title="删除文件", message="请注意:\n是否同时删除本地文件？",
                                option_2="是", option_1="否", font=("微软雅黑", 14) )
            response = msg.get()
            if response == "是":
                if os.path.exists(file_path):
                    os.remove(file_path)
            elif response == "否":
                pass
            else:
                return
        for info in self.received_files_info:
            if info.get('filename') == filename:
                time_stamp = ''.join(re.findall(r'\d', info.get('receive_time')))
                self.deleted_time_stamps.append(time_stamp)
                self.file_card_dict.get(filename).destroy()
                del self.file_card_dict[filename]
                self.received_files_info.remove(info)
                self.save_received_files_info()
                self.save_deleted_time_stamps()
                # 如果启用了自动清理日志，则清除该文件的日志
                if self.auto_clear_logs:
                    self.clear_file_logs(filename)
                break
        self.update_files_list()

    def file_in_explorer(self, file_path):
        if os.path.exists(file_path):
            # 使用 subprocess 打开资源管理器，并选中文件
            subprocess.run(['explorer', '/select,', file_path.replace("/", "\\")])
        else:
            CTkMessagebox(title="错误", message=f"文件{file_path}已移动或删除", option_1="确定",
                          font=("微软雅黑", 14), )

    def security_scan_all(self):
        self.get_path_from_received(self.received_files_info)
        self.one_click_scan(self.path_info)

    def one_click_scan(self, file_path_list):
        if not self.api_key:
            CTkMessagebox(title="提示", icon="cancel", message="请先前往设置填写密钥", option_1="确定",
                          font=("微软雅黑", 14))
            return
        if not file_path_list:
            CTkMessagebox(title="提示", icon="cancel", message="暂无文件需要扫描", option_1="确定",
                          font=("微软雅黑", 14))
            return
        elif self.is_scanning:
            CTkMessagebox(title="警告", icon="warning", message="已有扫描正在进行", option_1="确定",
                          font=("微软雅黑", 14))
            return
        self.scan_button.configure(text="检测中...", text_color="gray", command=self.cancel_scan)
        # 启动后台线程进行文件上传和报告获取
        self.thread = VirusTotalThread(file_path_list, self.api_key)
        self.thread.report_signal.connect(self.display_report)
        self.thread.start()
        self.is_scanning = True
        self.one_click = True

    def display_report(self, report_data):

        # 遍历每个文件的报告数据
        for report in report_data:
            file_path = report.get('file_path')
            
            # 检查是否是超大文件的特殊报告
            if report.get('oversized', False):
                for info in self.received_files_info:
                    if info.get('file_path') == file_path:
                        info["status"] = "文件过大"
                        self.save_received_files_info()
                continue
                
            # 获取检测结果和文件信息
            is_safe, readable_time, results = self.get_report_details(report)
            for info in self.received_files_info:
                if info.get('file_path') == file_path:
                    if is_safe:
                        info["status"] = "文件安全"
                    else:
                        if self.auto_delete_flag:
                            if os.path.exists(info.get('file_path')):
                                os.remove(info.get('file_path'))
                                info['status'] = "已自动清除威胁"
                        else:
                            info["status"] = "文件危险"
                    self.save_received_files_info()
            self.log_export(file_path, results)

        self.update_files_list()

        # # 创建并添加检测报告的 UI
        # self.add_report_item_to_ui(file_info, is_safe, readable_time, file_path)
        #
        # # 更新日志内容
        if self.one_click:
            self.scan_button.configure(text="一键检测", command=self.security_scan_all, text_color="white")
            CTkMessagebox(title="完成", message="一键检测已完成", icon="check", option_1="确定", font=("微软雅黑", 14))
            self.one_click = False
        else:
            CTkMessagebox(title="完成", message="文件检测已完成", icon="check", option_1="确定", font=("微软雅黑", 14))
        self.is_scanning = False

    def get_report_details(self, report):
        """
        获取文件检测的详细信息，包括文件信息、是否安全、检测时间和检测结果。
        """

        # 检测时间
        detection_time = report['data']['attributes'].get('date', '未知时间')
        readable_time = datetime.fromtimestamp(detection_time)

        # 检测结果
        results = report['data']['attributes']['results']
        is_safe = True  # 假设文件安全
        for engine, result in results.items():
            if result['category'] == 'malicious':
                is_safe = False
                break

        return is_safe, readable_time, results

    def log_export(self, file_path, results):
        """
        记录检测报告到日志。
        """
        # 创建 logs 目录（如果不存在）
        if not os.path.exists('logs'):
            os.makedirs('logs')
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = file_path.split('/')[-1]
        basename, file_extension = os.path.splitext(filename)
        log_filename = f"logs/log_{basename}_{timestamp}.txt"
        report_text = f"文件路径: {file_path}\n"
        report_text += "-" * 70 + "\n"
        for engine, result in results.items():
            report_text += f"引擎: {engine}, 检测结果: {result['category']}, 检测信息: {result['result']}\n"
        report_text += "\n"

        self.file_log_dict[f"{filename}"] = results
        self.save_file_log_dict()
        try:
            with open(log_filename, 'w', encoding='utf-8') as log_file:
                log_file.write(report_text)
        except Exception as e:
            print(f"日志生成失败: {e}")

    def create_report_frame(self, filename, filepath, icon_path):
        # 创建新的窗口
        popup = CustomTopWindow(fg_color="#111921")
        popup.title("检测报告")
        popup.lift()
        # 设置窗口大小
        popup.geometry("1200x630")

        popup.grid_columnconfigure(1, weight=1)
        if os.path.exists(icon_path):
            icon_light = Image.open(icon_path)
            icon_dark = Image.open(icon_path)
        else:
            icon_light = Image.open("icons/filetype/file_light.png")
            icon_dark = Image.open("icons/filetype/file_dark.png")
        file_icon = ctk.CTkImage(light_image=icon_light, dark_image=icon_dark, size=(64, 64))

        file_icon_label = ctk.CTkLabel(popup, text="", bg_color="#111921",
                                       image=file_icon)
        file_name_label = ctk.CTkLabel(popup, text=filename, bg_color="#111921",
                                       font=ctk.CTkFont(family="微软雅黑", size=18, weight="bold"))
        file_path_label = ctk.CTkLabel(popup, text=filepath, bg_color="#111921",
                                       font=ctk.CTkFont(family="微软雅黑", size=18))
        self.report_list = CustomScrollableFrame(popup, fg_color="transparent", height=520,
                                                 border_color="#7D7D7D", border_width=1)

        file_icon_label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew", rowspan=2)
        file_name_label.grid(row=0, column=1, padx=(5, 0), pady=(10, 0), sticky="nsw")
        file_path_label.grid(row=1, column=1, padx=(5, 0), pady=(0, 10), sticky="nsw")
        self.report_list.grid(row=2, column=0, padx=10, sticky="nsew", columnspan=2)

        self.show_report(filename)

    def create_report_card(self, engine, category, result, bold=False):
        report_card = ctk.CTkFrame(self.report_list, fg_color="#111921")
        engine_label = ctk.CTkLabel(report_card, text=engine, font=ctk.CTkFont(family="微软雅黑", size=18))
        category_label = ctk.CTkLabel(report_card, text=category, font=ctk.CTkFont(family="微软雅黑", size=18))
        if category == "undetected":
            category_label.configure(text_color="green")
        elif category == "malicious":
            category_label.configure(text_color="red")
        elif category == "检测结果":
            pass
        else:
            category_label.configure(text_color="gray")
        result_label = ctk.CTkLabel(report_card, text=result, font=ctk.CTkFont(family="微软雅黑", size=18))
        # 表头加粗
        if bold:
            engine_label.configure(font=ctk.CTkFont(family="微软雅黑", size=18, weight="bold"))
            category_label.configure(font=ctk.CTkFont(family="微软雅黑", size=18, weight="bold"))
            result_label.configure(font=ctk.CTkFont(family="微软雅黑", size=18, weight="bold"))
        report_card.pack(fill="x")
        engine_label.grid(row=0, column=0, padx=(15, 0), pady=0, sticky="nsw")
        category_label.grid(row=0, column=1, padx=0, pady=0, sticky="nsw")
        result_label.grid(row=0, column=2, padx=0, pady=0, sticky="nsw")

        report_card.grid_columnconfigure(0, weight=0, minsize=500)
        report_card.grid_columnconfigure(1, weight=0, minsize=500)
        report_card.grid_columnconfigure(2, weight=0, minsize=500)

    def show_report(self, filename):
        info = self.file_log_dict.get(filename)
        if info:
            self.create_report_card('引擎', '检测结果', '详情信息', bold=True)
            for engine, result in info.items():
                self.create_report_card(engine, result['category'], result['result'] if result['result'] else "")

        else:
            report_card = ctk.CTkFrame(self.report_list, fg_color="#111921")
            report_card.pack(fill="both")
            text_label = ctk.CTkLabel(report_card, text="暂无检测报告信息",
                                      font=ctk.CTkFont(family="微软雅黑", size=18),
                                      text_color="gray")
            text_label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
            report_card.grid_columnconfigure(0, weight=1)

    def cancel_scan(self):
        msg = CTkMessagebox(title="终止扫描", message="是否终止扫描？", icon="question", font=("微软雅黑", 14),
                            option_1="否", option_2="是")
        response = msg.get()
        if response == "是":
            if self.thread.isRunning():
                self.thread.terminate()
                self.scan_button.configure(text="安全检测", text_color="white", command=self.security_scan_all)
        else:
            pass

    def remove_danger_files(self):
        count = 0
        msg = CTkMessagebox(title="清除风险文件", message="此操作会彻底删除所有风险文件，是否继续？", icon="question",
                            option_1="否", option_2="是", font=("微软雅黑", 14))
        response = msg.get()
        if response == "是":
            for info in self.received_files_info:
                if info['status'] == "文件危险":
                    os.remove(info['file_path'])
                    self.file_card_dict.get(info['filename']).destroy()
                    self.received_files_info.remove(info)
                    self.update_files_list()
                    count += 1
            CTkMessagebox(title="清除风险文件", message=f"{count}个风险文件已清除", font=("微软雅黑", 14),
                          icon="check",
                          option_1="确认")
        else:
            pass
        self.save_received_files_info()

    def save_file_log_dict(self):
        """保存文件日志信息到本地 JSON 文件"""
        if not os.path.exists("data"):
            os.mkdir("data")
        try:
            with open('data/file_log_dict.json', 'w', encoding='utf-8') as f:
                json.dump(self.file_log_dict, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存文件日志信息失败: {e}")

    def load_file_log_dict(self):
        """从本地 JSON 文件加载文件日志信息"""
        if os.path.exists('data/file_log_dict.json'):
            try:
                with open('data/file_log_dict.json', 'r', encoding='utf-8') as f:
                    self.file_log_dict = json.load(f)
            except Exception as e:
                print(f"加载文件日志信息失败: {e}")

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

    def save_deleted_time_stamps(self):
        """保存接收到的文件信息到本地 JSON 文件"""
        if not os.path.exists("data"):
            os.mkdir("data")
        try:
            with open('data/deleted_time_stamps.json', 'w', encoding='utf-8') as f:
                json.dump(self.deleted_time_stamps, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存删除时间戳信息失败: {e}")

    def load_deleted_time_stamps(self):
        """从本地 JSON 文件加载接收到的文件信息"""
        if os.path.exists('data/deleted_time_stamps.json'):
            try:
                with open('data/deleted_time_stamps.json', 'r', encoding='utf-8') as f:
                    self.deleted_time_stamps = json.load(f)
            except Exception as e:
                print(f"加载删除时间戳信息失败: {e}")

    def scan_single_file(self, file_path):
        if not self.api_key:
            CTkMessagebox(title="提示", icon="cancel", message="请先前往设置填写密钥", option_1="确定",
                          font=("微软雅黑", 14))
            return
        if self.is_scanning:
            CTkMessagebox(title="警告", icon="warning", message="已有扫描正在进行", option_1="确定",
                          font=("微软雅黑", 14))
            return
        if not os.path.exists(file_path):
            CTkMessagebox(title="错误", icon="cancel", message="该文件已被删除或移动", option_1="确定",
                          font=("微软雅黑", 14))
            return
        file = [file_path]
        # 启动后台线程进行文件上传和报告获取
        self.thread = VirusTotalThread(file, self.api_key)
        self.thread.report_signal.connect(self.display_report)
        self.thread.start()
        self.is_scanning = True

    def clear_temp(self):
        # 倒序遍历列表，避免移除操作造成索引混乱
        for item in reversed(self.deleted_time_stamps):
            if os.path.exists(f"temp/{item}.png"):
                os.remove(f"temp/{item}.png")
                self.deleted_time_stamps.remove(item)
            else:
                print(f"未找到文件{item}.png")
        self.save_deleted_time_stamps()

    def clear_file_logs(self, filename):
        """清除指定文件的所有日志"""
        if not os.path.exists('logs'):
            return
            
        # 从文件日志字典中移除
        if filename in self.file_log_dict:
            del self.file_log_dict[filename]
            self.save_file_log_dict()
            
        # 删除对应的日志文件
        basename, _ = os.path.splitext(filename)
        
        # 获取所有日志文件
        all_log_files = os.listdir('logs')
        
        # 使用更精确的匹配方式，确保能匹配到包含特殊字符的文件名
        log_pattern = f"log_{re.escape(basename)}_"
        log_files = [f for f in all_log_files if re.match(f"^{log_pattern}\\d+\\.txt$", f)]
        
        print(f"正在清理文件 '{filename}' 的日志，找到 {len(log_files)} 个匹配的日志文件")
        
        for log_file in log_files:
            try:
                os.remove(os.path.join('logs', log_file))
                print(f"已删除日志文件: {log_file}")
            except Exception as e:
                print(f"删除日志文件失败: {e}")
                
    def check_and_clear_logs_on_startup(self):
        """启动时检查并清理不存在文件的日志"""
        if not self.auto_clear_logs:
            print("日志自动清理已关闭")
            return
            
        print("日志自动清理已开启，正在检查...")
        
        # 1. 首先清理日志字典中不在当前文件列表中的文件日志
        current_filenames = [info.get('filename') for info in self.received_files_info]
        log_filenames = list(self.file_log_dict.keys())
        
        for filename in log_filenames:
            if filename not in current_filenames:
                self.clear_file_logs(filename)
                print(f"已清理不存在文件的日志: {filename}")
        
        # 2. 然后检查是否有"野文件"（在logs目录中但不在file_log_dict中的日志文件）
        self.clean_orphaned_log_files()
        
    def clean_orphaned_log_files(self):
        """清理孤立的日志文件（在logs目录中但不在file_log_dict中的日志文件）"""
        if not os.path.exists('logs'):
            return
            
        print("正在检查孤立的日志文件...")
        
        # 获取所有日志文件
        all_log_files = os.listdir('logs')
        
        # 获取当前所有文件的基本名称（不含扩展名）
        current_filenames = [os.path.splitext(info.get('filename'))[0] for info in self.received_files_info]
        
        # 检查每个日志文件
        orphaned_files = []
        for log_file in all_log_files:
            # 日志文件格式应该是 log_basename_timestamp.txt
            if log_file.startswith('log_') and log_file.endswith('.txt'):
                # 尝试提取文件基本名称
                try:
                    # 去掉 'log_' 前缀和 '_timestamp.txt' 后缀
                    parts = log_file[4:].split('_')
                    if len(parts) >= 2:
                        # 最后一部分是时间戳，前面的部分组成文件名
                        timestamp = parts[-1].split('.')[0]  # 去掉 .txt
                        basename = '_'.join(parts[:-1])
                        
                        # 检查这个文件名是否在当前文件列表中
                        file_exists = False
                        for current_name in current_filenames:
                            if basename == current_name:
                                file_exists = True
                                break
                                
                        if not file_exists:
                            orphaned_files.append(log_file)
                except Exception as e:
                    print(f"解析日志文件名失败: {log_file}, 错误: {e}")
        
        # 删除孤立的日志文件
        for orphaned_file in orphaned_files:
            try:
                os.remove(os.path.join('logs', orphaned_file))
                print(f"已删除孤立的日志文件: {orphaned_file}")
            except Exception as e:
                print(f"删除孤立的日志文件失败: {orphaned_file}, 错误: {e}")
