import customtkinter as ctk
from PIL import Image
import datetime
import os
import re
from tkinter import filedialog
from components.deepseek_api import DeepSeekAPI
import threading
import mimetypes

class AIChatPage:
    """AI聊天页面"""
    
    def __init__(self, parent, controller):
        """
        初始化 AI 对话页面。
        
        Args:
            parent: 父窗口组件。
            controller: 控制器对象，用于与主程序交互。
        """
        self.parent = parent
        self.controller = controller
        self.messages = []
        self.attachments = []
        
        # 创建主框架
        self.frame = ctk.CTkFrame(parent, fg_color="#1B2B3B", corner_radius=10)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)  # 让聊天内容区域可以扩展
        
        # 创建页面内容
        self.create_chat_page()
        
        # 初始化 DeepSeek API 客户端
        self.api = DeepSeekAPI()
        
        # 消息历史，用于发送给 API
        self.message_history = []
        
        # 在初始化时添加 AI 自我介绍
        self.simulate_ai_introduction()

    def create_chat_page(self):
        """创建 AI 对话页面的 UI 元素"""
        # 标题栏框架
        self.title_frame = ctk.CTkFrame(self.frame, fg_color="#1B2B3B", height=40, corner_radius=10)
        self.title_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.title_frame.grid_columnconfigure(0, weight=0)  # 标题左对齐
        self.title_frame.grid_columnconfigure(1, weight=1)  # 中间空白区域
        self.title_frame.grid_columnconfigure(2, weight=0)  # 新对话按钮右对齐
        
        # 加载AI图标
        try:
            self.ai_icon = ctk.CTkImage(
                light_image=Image.open("icons/ai_dark.png"),
                dark_image=Image.open("icons/ai_dark.png"),
                size=(24, 24)
            )
            # 标题带图标
            self.title_label = ctk.CTkLabel(
                self.title_frame, 
                text="AI 对话", 
                font=ctk.CTkFont(family="微软雅黑", size=24, weight="bold"),
                text_color="white",
                image=self.ai_icon,
                compound="left",
                padx=10
            )
        except Exception as e:
            print(f"无法加载AI图标: {e}")
            # 标题不带图标
            self.title_label = ctk.CTkLabel(
                self.title_frame, 
                text="AI 对话", 
                font=ctk.CTkFont(family="微软雅黑", size=24, weight="bold"),
                text_color="white"
            )
        
        self.title_label.grid(row=0, column=0, sticky="w")
        
        # 新对话按钮
        self.new_chat_button = ctk.CTkButton(
            self.title_frame,
            text="新对话",
            font=ctk.CTkFont(family="微软雅黑", size=14),
            width=80,
            height=30,
            corner_radius=10,
            command=self.start_new_chat
        )
        self.new_chat_button.grid(row=0, column=2, padx=(0, 0), pady=0, sticky="e")
        
        # 聊天内容滚动框架
        self.chat_container = ctk.CTkScrollableFrame(
            self.frame,
            fg_color="#263844",
            corner_radius=10,
            width=800,
            height=450
        )
        self.chat_container.grid(row=1, column=0, padx=20, pady=(10, 10), sticky="nsew")
        self.chat_container.grid_columnconfigure(0, weight=1)
        
        # 附件信息框架 - 还原到输入框上方
        self.attachment_frame = ctk.CTkFrame(self.frame, fg_color="#1B2B3B", height=30)
        self.attachment_frame.grid(row=2, column=0, padx=20, pady=(0, 0), sticky="ew")
        self.attachment_frame.grid_columnconfigure(0, weight=1)
        
        # 附件标签（初始隐藏）
        self.attachment_label = ctk.CTkLabel(
            self.attachment_frame,
            text="",
            font=ctk.CTkFont(family="微软雅黑", size=12, weight="bold"),
            text_color="#4A90E2"
        )
        self.attachment_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # 清除附件按钮（初始隐藏）
        self.clear_attachment_button = ctk.CTkButton(
            self.attachment_frame,
            text="x",
            font=ctk.CTkFont(family="微软雅黑", size=14, weight="bold"),
            width=20,
            height=20,
            corner_radius=10,
            fg_color="#4A90E2",
            command=self.clear_attachment
        )
        self.clear_attachment_button.grid(row=0, column=1, padx=(0, 10), pady=5, sticky="e")
        self.clear_attachment_button.grid_remove()  # 初始时隐藏清除按钮
        
        # 隐藏附件框架，但保留其空间
        self.attachment_frame.grid()
        self.attachment_label.configure(text="")
        
        # 底部输入区域框架
        self.input_frame = ctk.CTkFrame(self.frame, fg_color="#1B2B3B", height=80)
        self.input_frame.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.input_frame.grid_columnconfigure(1, weight=1)
        
        # 附件按钮
        try:
            self.paperclip_image = ctk.CTkImage(
                light_image=Image.open("icons/paperclip_light.png"),
                dark_image=Image.open("icons/paperclip_dark.png"),
                size=(20, 20)
            )
            self.attachment_button = ctk.CTkButton(
                self.input_frame,
                text="",
                image=self.paperclip_image,
                width=40,
                height=40,
                corner_radius=10,
                fg_color="transparent",  # 透明背景
                hover_color="#263844",   # 悬停颜色
                command=self.select_attachment
            )
        except Exception as e:
            print(f"无法加载附件图标: {e}")
            self.attachment_button = ctk.CTkButton(
                self.input_frame,
                text="📎",
                width=40,
                height=40,
                corner_radius=10,
                fg_color="transparent",  # 透明背景
                hover_color="#263844",   # 悬停颜色
                command=self.select_attachment
            )
        
        self.attachment_button.grid(row=0, column=0, padx=(0, 10), pady=20)
        
        # 输入框
        self.input_box = ctk.CTkTextbox(
            self.input_frame,
            width=600,
            height=40,
            font=ctk.CTkFont(family="微软雅黑", size=16),
            corner_radius=10
        )
        self.input_box.grid(row=0, column=1, padx=(0, 10), pady=20, sticky="ew")
        
        # 发送按钮
        self.send_button = ctk.CTkButton(
            self.input_frame,
            text="发送",
            font=ctk.CTkFont(family="微软雅黑", size=16, weight="bold"),
            width=80,
            height=40,
            corner_radius=10,
            command=self.send_message
        )
        self.send_button.grid(row=0, column=2, padx=(0, 0), pady=20)
        
        # 绑定回车键发送消息
        self.input_box.bind("<Return>", lambda event: self.send_message())
        
    def start_new_chat(self):
        """开始新对话，清除现有聊天记录"""
        # 清除聊天容器中的所有内容
        for widget in self.chat_container.winfo_children():
            widget.destroy()
            
        # 清空消息列表
        self.messages = []
        
        # 清除附件
        self.clear_attachment()
        
        # 模拟AI发送自我介绍
        self.simulate_ai_introduction()
        
    def simulate_ai_introduction(self):
        """模拟 AI 自我介绍"""
        intro_message = "您好！我是您的 AI 助手，基于 DeepSeek 模型。我可以帮助您回答问题、提供信息或进行一般性的对话。请随时告诉我您需要什么帮助！"
        self.add_message("ai", intro_message)
        
        # 添加到消息历史
        self.message_history.append({"role": "assistant", "content": intro_message})

    def select_attachment(self):
        """选择附件文件"""
        file_path = filedialog.askopenfilename(
            title="选择文件",
            filetypes=[
                ("文本文件", "*.txt;*.md;*.py;*.java;*.cpp;*.c;*.html;*.css;*.js;*.json"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_path:
            # 获取文件名
            file_name = os.path.basename(file_path)
            
            # 检测文件类型
            mime_type, _ = mimetypes.guess_type(file_path)
            is_text = mime_type and mime_type.startswith('text/') or file_path.endswith(('.py', '.java', '.cpp', '.c', '.js', '.html', '.css', '.json'))
            
            try:
                if is_text:
                    # 读取文本文件内容
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 保存附件信息
                    self.attachments.append({
                        'path': file_path,
                        'name': file_name,
                        'content': content,
                        'type': 'text'
                    })
                    
                    # 更新UI显示
                    self.attachment_label.configure(text=f"📄 {file_name} (文本文件)")
                    self.clear_attachment_button.grid()  # 显示清除按钮
                    
                else:
                    # 非文本文件
                    self.attachments.append({
                        'path': file_path,
                        'name': file_name,
                        'type': 'binary'
                    })
                    self.attachment_label.configure(text=f"📎 {file_name} (非文本文件)")
                    self.clear_attachment_button.grid()
            
            except Exception as e:
                print(f"读取文件失败: {e}")
                self.controller.show_error("文件读取失败", str(e))
                return

    def send_message(self):
        """发送消息"""
        message = self.input_box.get("1.0", "end-1c").strip()
        if not message and not self.attachments:
            return
            
        # 清空输入框
        self.input_box.delete("1.0", "end")
        
        # 构建显示消息（用于UI显示）
        display_message = message
        if self.attachments:
            for attachment in self.attachments:
                display_message += f"\n📎 附件: {attachment['name']}"
        
        # 构建发送给AI的完整消息（包含文件内容）
        ai_message = message
        if self.attachments:
            for attachment in self.attachments:
                if attachment['type'] == 'text':
                    ai_message += f"\n\n[文件内容开始]\n{attachment['content']}\n[文件内容结束]"
        
        # 添加用户消息到界面（只显示附件名）
        self.add_message("user", display_message)
        
        # 清除附件
        self.clear_attachment()
        
        # 添加到消息历史
        self.message_history.append({"role": "user", "content": ai_message})
        
        # 在新线程中获取 AI 响应（发送包含文件内容的消息）
        threading.Thread(target=self.get_ai_response, daemon=True).start()

    def get_ai_response(self):
        """处理 AI 响应"""
        try:
            # 显示正在输入提示
            self.frame.after(0, lambda: self.show_typing_indicator())
            
            # 清理之前的流式内容
            if hasattr(self, 'streaming_content'):
                delattr(self, 'streaming_content')
            
            # 调用 API 获取流式响应
            self.api.chat_stream(
                self.message_history, 
                callback=self.update_streaming_message
            )
            
        except Exception as e:
            print(f"获取 AI 响应失败: {e}")
            self.frame.after(0, lambda: self.hide_typing_indicator())
            error_message = f"抱歉，获取响应时出现错误: {str(e)}"
            self.frame.after(0, lambda: self.add_message("ai", error_message))
    
    def update_streaming_message(self, text_chunk):
        """更新流式消息"""
        # 处理错误消息
        if text_chunk.startswith("错误:"):
            # 如果是API密钥错误，提供更友好的提示
            if "未设置 API 密钥" in text_chunk:
                text_chunk = "请在程序中设置有效的 DeepSeek API 密钥。目前使用模拟响应。"
                # 添加一个模拟响应
                if len(self.message_history) > 0 and self.message_history[-1]["role"] == "user":
                    user_message = self.message_history[-1]["content"]
                    text_chunk += "\n" + self.get_fallback_response(user_message)
            
            # 隐藏正在输入提示并添加 AI 消息
            self.frame.after(0, lambda: self.hide_typing_indicator())
            self.frame.after(0, lambda: self.add_message("ai", text_chunk))
            
            # 添加到消息历史
            self.message_history.append({"role": "assistant", "content": text_chunk})
            return
            
        # 如果这是第一个块，隐藏正在输入提示并创建消息
        if not hasattr(self, 'streaming_content') or not self.streaming_content:
            self.streaming_content = text_chunk
            self.frame.after(0, lambda: self.hide_typing_indicator())
            self.frame.after(0, lambda: self.add_message("ai", self.streaming_content))
        else:
            # 否则更新内容和现有消息
            self.streaming_content += text_chunk
            self.frame.after(0, lambda: self.update_last_ai_message(self.streaming_content))
    
    def update_last_ai_message(self, content):
        """更新最后一条AI消息的内容"""
        # 确保有消息且最后一条是AI消息
        if not self.messages or self.messages[-1]["type"] != "ai":
            print("没有找到最后一条AI消息")
            return
            
        # 处理Markdown文本
        processed_content = self.process_markdown(content)
        
        # 查找最后一个消息框架
        last_message_frame = self.chat_container.winfo_children()[-1]
        if not isinstance(last_message_frame, ctk.CTkFrame):
            print("最后一个元素不是Frame")
            return
            
        # 查找消息气泡
        message_bubble = None
        for child in last_message_frame.winfo_children():
            if isinstance(child, ctk.CTkFrame) and child.cget("corner_radius") == 15:
                message_bubble = child
                break
                
        if not message_bubble:
            print("没有找到消息气泡")
            return
            
        # 查找消息标签
        message_label = None
        for child in message_bubble.winfo_children():
            if isinstance(child, ctk.CTkLabel):
                message_label = child
                break
                
        if not message_label:
            print("没有找到消息标签")
            return
            
        # 更新消息标签
        message_label.configure(text=processed_content)
        
        # 更新消息内容
        self.messages[-1]["content"] = content
        
        # 更新消息历史
        if len(self.message_history) > 0:
            # 检查最后一条消息是否是AI消息
            if self.message_history[-1]["role"] == "assistant":
                self.message_history[-1]["content"] = content
            else:
                # 如果最后一条不是AI消息，添加一条新的
                self.message_history.append({"role": "assistant", "content": content})
    
    def get_fallback_response(self, user_message):
        """获取备用响应，当 API 调用失败时使用"""
        if "这个文件内容是什么" in user_message or "文件内容" in user_message:
            if "[文件内容开始]" in user_message:
                return "这是一个文本文件，我已经读取了它的内容。让我分析一下这个文件..."
        elif "你好" in user_message or "您好" in user_message:
            return "您好！我是您的 AI 助手。很高兴为您服务。"
        else:
            return "抱歉，我现在无法正确处理您的请求。请稍后再试或换个问题。"
    
    def show_typing_indicator(self):
        """显示正在输入提示"""
        # 创建消息框架
        message_frame = ctk.CTkFrame(self.chat_container, fg_color="transparent")
        message_frame.grid(row=len(self.messages), column=0, sticky="ew", padx=10, pady=5)
        message_frame.grid_columnconfigure(0, weight=1)
        
        # AI名标签
        header_frame = ctk.CTkFrame(message_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 0))
        header_frame.grid_columnconfigure(0, weight=0)
        header_frame.grid_columnconfigure(1, weight=1)
        
        ai_label = ctk.CTkLabel(
            header_frame,
            text="AI 助手正在输入...",
            font=ctk.CTkFont(family="微软雅黑", size=12, weight="bold"),
            text_color="#10A37F"
        )
        ai_label.grid(row=0, column=0, sticky="w")
        
        # 保存引用以便稍后删除
        self.typing_indicator = message_frame
    
    def hide_typing_indicator(self):
        """隐藏正在输入提示"""
        if hasattr(self, 'typing_indicator'):
            self.typing_indicator.destroy()
            delattr(self, 'typing_indicator')

    def add_message(self, role, message):
        """
        添加消息到聊天框
        
        Args:
            role: 消息角色，"user" 或 "ai"
            message: 消息内容
        """
        # 预处理Markdown文本
        message = self.process_markdown(message)
        
        # 创建消息框架
        message_frame = ctk.CTkFrame(self.chat_container, fg_color="transparent")
        message_frame.grid(row=len(self.messages), column=0, sticky="ew", padx=10, pady=5)
        message_frame.grid_columnconfigure(0, weight=1)
        
        # 获取当前时间
        current_time = self.get_current_time()
        
        # 名称和时间标签
        header_frame = ctk.CTkFrame(message_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 0))
        if role == "user":
            header_frame.grid_columnconfigure(0, weight=1)  # 空白
            header_frame.grid_columnconfigure(1, weight=0)  # 时间
            header_frame.grid_columnconfigure(2, weight=0)  # 用户名
        else:
            header_frame.grid_columnconfigure(0, weight=0)  # AI名
            header_frame.grid_columnconfigure(1, weight=0)  # 时间
            header_frame.grid_columnconfigure(2, weight=1)  # 空白
        
        if role == "user":
            # 用户名标签
            user_label = ctk.CTkLabel(
                header_frame,
                text="您",
                font=ctk.CTkFont(family="微软雅黑", size=12, weight="bold"),
                text_color="#4A90E2"
            )
            user_label.grid(row=0, column=2, sticky="e")
            
            # 时间标签
            time_label = ctk.CTkLabel(
                header_frame,
                text=current_time,
                font=ctk.CTkFont(family="微软雅黑", size=10),
                text_color="#6C757D"
            )
            time_label.grid(row=0, column=1, padx=(0, 10), sticky="e")
            
            # 消息内容 - 创建气泡效果
            message_bubble = ctk.CTkFrame(message_frame, fg_color="#4A90E2", corner_radius=15)
            message_bubble.grid(row=1, column=0, sticky="e", padx=(100, 10), pady=(5, 10))
            message_bubble.grid_columnconfigure(0, weight=1)
            
            try:
                # 使用自定义函数处理Markdown格式
                processed_text = self.process_markdown(message)
                
                # 使用普通标签显示处理后的文本
                message_label = ctk.CTkLabel(
                    message_bubble,
                    text=processed_text,
                    font=ctk.CTkFont(family="微软雅黑", size=14),
                    text_color="white",
                    justify="left",
                    wraplength=500,  # 文本换行宽度
                    anchor="w"
                )
                message_label.grid(row=0, column=0, sticky="w", padx=15, pady=10)
            except Exception as e:
                print(f"文本处理错误: {e}")
                # 如果处理失败，显示原始文本
                message_label = ctk.CTkLabel(
                    message_bubble,
                    text=message,
                    font=ctk.CTkFont(family="微软雅黑", size=14),
                    text_color="white",
                    justify="left",
                    wraplength=500,  # 文本换行宽度
                    anchor="w"
                )
                message_label.grid(row=0, column=0, sticky="w", padx=15, pady=10)
        else:
            # AI名标签
            ai_label = ctk.CTkLabel(
                header_frame,
                text="AI 助手",
                font=ctk.CTkFont(family="微软雅黑", size=12, weight="bold"),
                text_color="#10A37F"  # AI绿色
            )
            ai_label.grid(row=0, column=0, sticky="w")
            
            # 时间标签
            time_label = ctk.CTkLabel(
                header_frame,
                text=current_time,
                font=ctk.CTkFont(family="微软雅黑", size=10),
                text_color="#6C757D"
            )
            time_label.grid(row=0, column=1, padx=(10, 0), sticky="w")
            
            # 消息内容 - 创建气泡效果
            message_bubble = ctk.CTkFrame(message_frame, fg_color="#2E3B4E", corner_radius=15)
            message_bubble.grid(row=1, column=0, sticky="w", padx=(10, 100), pady=(5, 10))
            message_bubble.grid_columnconfigure(0, weight=1)
            
            try:
                # 使用自定义函数处理Markdown格式
                processed_text = self.process_markdown(message)
                
                # 使用普通标签显示处理后的文本
                message_label = ctk.CTkLabel(
                    message_bubble,
                    text=processed_text,
                    font=ctk.CTkFont(family="微软雅黑", size=14),
                    text_color="white",
                    justify="left",
                    wraplength=500,  # 文本换行宽度
                    anchor="w"
                )
                message_label.grid(row=0, column=0, sticky="w", padx=15, pady=10)
            except Exception as e:
                print(f"文本处理错误: {e}")
                # 如果处理失败，显示原始文本
                message_label = ctk.CTkLabel(
                    message_bubble,
                    text=message,
                    font=ctk.CTkFont(family="微软雅黑", size=14),
                    text_color="white",
                    justify="left",
                    wraplength=500,  # 文本换行宽度
                    anchor="w"
                )
                message_label.grid(row=0, column=0, sticky="w", padx=15, pady=10)
        
        # 保存消息
        self.messages.append({"type": role, "content": message, "time": current_time})
        
        # 自动滚动到最新消息
        self.chat_container._parent_canvas.yview_moveto(1.0)
        
    def process_markdown(self, text):
        """
        预处理Markdown文本，转换为普通文本
        
        Args:
            text: 原始Markdown文本
            
        Returns:
            处理后的普通文本
        """
        # 处理标题
        text = re.sub(r'###\s+(.*?)(?:\n|$)', r'\1\n', text)  # 三级标题
        text = re.sub(r'##\s+(.*?)(?:\n|$)', r'\1\n', text)   # 二级标题
        text = re.sub(r'#\s+(.*?)(?:\n|$)', r'\1\n', text)    # 一级标题
        
        # 处理加粗和斜体
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # 加粗
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # 斜体
        text = re.sub(r'__(.*?)__', r'\1', text)      # 加粗
        text = re.sub(r'_(.*?)_', r'\1', text)        # 斜体
        
        # 处理代码块
        text = re.sub(r'```.*?\n(.*?)```', r'\1', text, flags=re.DOTALL)  # 代码块
        text = re.sub(r'`(.*?)`', r'\1', text)  # 行内代码
        
        # 处理列表
        text = re.sub(r'^\s*[-*+]\s+(.*?)$', r'• \1', text, flags=re.MULTILINE)  # 无序列表
        text = re.sub(r'^\s*\d+\.\s+(.*?)$', r'• \1', text, flags=re.MULTILINE)  # 有序列表
        
        return text
        
    def get_current_time(self):
        """获取当前时间字符串"""
        now = datetime.datetime.now()
        return now.strftime("%H:%M:%S")

    def clear_attachment(self):
        """清除当前附件"""
        self.attachments = []
        # 保留框架但清除文本
        self.attachment_label.configure(text="")
        self.clear_attachment_button.grid_remove()
