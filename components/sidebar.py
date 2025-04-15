import customtkinter as ctk
from components.avatar_page import create_circular_image
from PIL import Image



class Sidebar:
    def __init__(self, parent, switch_page_callback):
        """
        Sidebar 初始化函数。

        Args:
            parent: 父窗口组件。
            switch_page_callback: 页面切换的回调函数，用于切换主界面中的页面。
        """
        self.parent = parent
        self.switch_page_callback = switch_page_callback  # 页面切换的回调函数
        self.selected_button = None  # 记录当前选中的按钮
        self.buttons = []  # 存储所有按钮的引用，方便管理样式

        self.setup_sidebar()  # 设置侧边栏布局

    def setup_sidebar(self):
        """
        设置侧边栏的布局，包括头像按钮和文件分类按钮。
        """
        # 侧边栏主框架
        self.frame = ctk.CTkFrame(self.parent, width=280, corner_radius=0, fg_color="#111921")
        self.frame.grid(row=0, column=0, sticky="nsew")
        self.frame.grid_propagate(False)  # 禁止自动调整大小
        self.frame.grid_rowconfigure(10, weight=1)  # 空白区域扩展
        self.frame.grid_columnconfigure(0, weight=1)

        # 添加头像按钮
        self.avatar_image = self.get_avatar_image("icons/default_avatar.png")  # 加载默认头像
        self.avatar_button = ctk.CTkButton(
            self.frame,
            image=self.avatar_image,
            text="",
            width=80,
            height=80,
            corner_radius=40,
            fg_color="#111921",  # 按钮背景色
            hover=False,  # 禁用悬停效果
            command=self.select_avatar_button,  # 点击事件绑定到头像页面
        )
        self.avatar_button.grid(row=0, column=0, pady=(20, 10), padx=0, sticky="n")

        # 添加计算机名称显示
        self.computer_name_label = ctk.CTkLabel(
            self.frame,
            text="单击头像以配置信息",  # 默认名称
            font=ctk.CTkFont(family="微软雅黑", size=18, weight="bold"),
            text_color="#B4BDC4"
        )
        self.computer_name_label.grid(row=1, column=0, pady=(0, 20))

        # 添加文件分类按钮
        self.create_sidebar_button("设备发现", "icons/device_discover.png", 2, "discover")  # 默认选中仪表盘
        self.create_sidebar_button("文件传输", "icons/transfer_dark.png", 3, "transfer")
        self.create_sidebar_button("文件管理", "icons/folder.png", 4, "files")
        self.create_sidebar_button("AI 对话", "icons/ai_dark.png", 5, "ai_chat")
        self.create_sidebar_button("校园网登录", "icons/login_dark.png", 6, "auto_login")
        self.create_sidebar_button("设置", "icons/settings.png", 7, "settings")
        self.create_sidebar_button("关于", "icons/info_dark.png", 8, "about")

    def create_sidebar_button(self, text, image_path, row, page_name, selected=False):
        """
        创建侧边栏中的分类按钮。

        Args:
            text (str): 按钮显示的文本。
            row (int): 按钮所在的行号。
            page_name (str): 关联的页面名称。
            selected (bool): 是否为默认选中的按钮。
            image_path: 图标路径
        """
        # 按钮的背景色和文字颜色，根据是否选中设置
        fg_color = "#1B2B3B" if selected else "transparent"
        text_color = "white" if selected else "#B4BDC4"

        image = ctk.CTkImage(  # 加载文件夹图标
            light_image=Image.open(image_path),
            dark_image=Image.open(image_path),
            size=(30, 30),
        )
        # 创建按钮框架
        frame = ctk.CTkFrame(self.frame, fg_color=fg_color)
        frame.grid(row=row, column=0, padx=20, pady=2, sticky="ew")
        frame.grid_columnconfigure(1, weight=1)

        # 按钮图标
        icon_label = ctk.CTkLabel(frame, image=image, text="")
        icon_label.grid(row=0, column=0, padx=(10, 10), pady=10)

        # 按钮文字
        text_label = ctk.CTkLabel(frame, text=text, text_color=text_color,
                                  font=ctk.CTkFont(family="微软雅黑", size=16, weight="bold"))
        text_label.grid(row=0, column=1, sticky="w")

        # 按钮事件绑定
        frame.bind("<Button-1>", lambda e: self.select_button(frame, page_name))
        icon_label.bind("<Button-1>", lambda e: self.select_button(frame, page_name))
        text_label.bind("<Button-1>", lambda e: self.select_button(frame, page_name))

        # 悬停效果
        frame.bind("<Enter>", lambda e: frame.configure(fg_color="#263844"))
        frame.bind("<Leave>",
                   lambda e: frame.configure(fg_color=fg_color if frame != self.selected_button else "#1B2B3B"))
        # 给卡片中所有子组件绑定事件和悬停样式
        for child in frame.winfo_children():
            child.bind("<Enter>", lambda e: frame.configure(fg_color="#263844"))
            child.bind("<Leave>", lambda e: frame.configure(fg_color=fg_color if frame != self.selected_button else "#1B2B3B"))
        # 设置默认选中状态
        if selected:
            self.selected_button = frame
            frame.configure(fg_color="#1B2B3B")

        # 保存按钮引用
        self.buttons.append(frame)

    def select_button(self, button, page_name):
        """
        切换按钮的选中状态，并切换页面。

        Args:
            button: 被点击的按钮框架。
            page_name (str): 需要切换的页面名称。
        """
        self.clear_selected_button()  # 清除所有按钮的选中状态
        self.selected_button = button  # 更新选中按钮
        button.configure(fg_color="#1B2B3B")  # 设置选中样式
        self.switch_page_callback(page_name)  # 切换页面

    def select_avatar_button(self):
        """
        点击头像按钮的处理函数，清除所有按钮的选中状态，并切换到头像页面。
        """
        self.clear_selected_button()  # 清除所有按钮的选中状态
        self.selected_button = None  # 清空选中按钮
        self.switch_page_callback("avatar")  # 切换到头像页面

    def clear_selected_button(self):
        """
        清除所有按钮的选中状态。
        """
        for button in self.buttons:
            button.configure(fg_color="transparent")

    def get_avatar_image(self, path):
        """
        加载头像图片。

        Args:
            path (str): 头像图片路径。

        Returns:
            CTkImage: 返回一个 CTkImage 对象。
        """
        try:
            image = Image.open(path).resize((80, 80))
            return ctk.CTkImage(light_image=image, dark_image=image, size=(80, 80))
        except:
            return None

    def update_avatar(self, avatar_path, computer_name):
        """更新侧边栏的头像显示为圆形图片。

        Args:
            avatar_path (str): 新的头像文件路径。
        """
        circular_image = create_circular_image(avatar_path, (80, 80))  # 裁剪为圆形
        avatar_image = ctk.CTkImage(
            light_image=circular_image,
            dark_image=circular_image,
            size=(80, 80)
        )
        self.avatar_button.configure(image=avatar_image)
        self.avatar_image = avatar_image  # 保存新的头像图片对象
        # 更新计算机名称
        self.computer_name_label.configure(text=computer_name)
