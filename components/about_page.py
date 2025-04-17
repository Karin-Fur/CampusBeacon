import customtkinter as ctk
from PIL import Image
from components.CustomTools import CustomScrollableFrame
import webbrowser


class AboutPage:
    def __init__(self, parent):
        """
        关于页面初始化函数。

        Args:
            parent: 父窗口组件。
        """
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        """设置关于页面的UI"""
        # 主框架
        self.frame = ctk.CTkFrame(self.parent, fg_color="#111921", corner_radius=0)
        self.frame.grid_columnconfigure(0, weight=1)

        # 标题
        title_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        title_frame.grid_columnconfigure(0, weight=0)
        title_frame.grid_columnconfigure(0, weight=0)

        title_image = ctk.CTkImage(light_image=Image.open("icons/campus_beacon.png"),
                                   dark_image=Image.open("icons/campus_beacon.png"),
                                   size=(64, 64))
        image_label = ctk.CTkLabel(title_frame, image=title_image, text='')
        image_label.grid(row=0, column=0, sticky="w", rowspan=2, padx=(5, 20))

        title_label = ctk.CTkLabel(
            title_frame,
            text="关于 CampusBeacon",
            font=ctk.CTkFont(family="微软雅黑", size=24, weight="bold")
        )
        title_label.grid(row=0, column=1, sticky="w")

        # 软件版本
        version_label = ctk.CTkLabel(
            title_frame,
            text="版本 1.0.0",
            font=ctk.CTkFont(family="微软雅黑", size=14),
            text_color="#B4BDC4"
        )
        version_label.grid(row=1, column=1, sticky="w", pady=(0, 10))

        scrollable_frame = CustomScrollableFrame(self.frame, fg_color="transparent", height=560)
        scrollable_frame.columnconfigure(0, weight=1)
        scrollable_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))

        # 软件描述
        description_frame = ctk.CTkFrame(scrollable_frame, fg_color="#263844", corner_radius=10)

        description_label = ctk.CTkLabel(
            description_frame,
            text="CampusBeacon 是一款专为校园网络环境设计的多功能工具软件，\n"
                 "集成了设备发现、文件传输、文件管理、AI对话和校园网自动登录等功能。\n"
                 "本软件旨在提高校园网络使用效率，为用户提供便捷的文件传输和管理体验。",
            font=ctk.CTkFont(family="微软雅黑", size=16),
            wraplength=600,
            justify="left"
        )
        description_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")
        description_frame.grid(row=0, pady=10, sticky="nsew")

        # 常见问题与解答
        faq_frame = ctk.CTkFrame(scrollable_frame, fg_color="#263844", corner_radius=10)

        faq_title = ctk.CTkLabel(
            faq_frame,
            text="常见问题与解答",
            font=ctk.CTkFont(family="微软雅黑", size=18, weight="bold")
        )
        faq_title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # FAQ 1
        faq1_title = ctk.CTkLabel(
            faq_frame,
            text="Q: 为什么我不能正常发现设备？",
            font=ctk.CTkFont(family="微软雅黑", size=14, weight="bold"),
            text_color="#4CC2FF"
        )
        faq1_title.grid(row=1, column=0, padx=20, pady=(10, 5), sticky="w")

        faq1_answer = ctk.CTkLabel(
            faq_frame,
            text="A: 部分校园网会对广播域进行隔离，以及经iperf3测试，UDP数据包会由被大量拦截，从而导致无法实现设备发现，\n"
                 "该情况下请使用手动连接模式。",
            font=ctk.CTkFont(family="微软雅黑", size=14),
            justify="left"
        )
        faq1_answer.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="w")

        # FAQ 2
        faq2_title = ctk.CTkLabel(
            faq_frame,
            text="Q: 文件传输速度不理想怎么办？",
            font=ctk.CTkFont(family="微软雅黑", size=14, weight="bold"),
            text_color="#4CC2FF"
        )
        faq2_title.grid(row=3, column=0, padx=20, pady=(10, 5), sticky="w")

        faq2_answer = ctk.CTkLabel(
            faq_frame,
            text="A: 经测试，在正常局域网环境下，本软件传输速度可达1Gbps，但在校园网环境下可能只有100Mbps，在尝试了多线程、\n改用UDP数据包、"
                 "流量伪装等测试后，推断校园网采用了内部流量限速(QoS策略)，针对IP限制了内部传输的流量。不过，\n您仍可以通过使用私人的路由器建立一个局域网"
                 "以实现更高速度的传输。",
            font=ctk.CTkFont(family="微软雅黑", size=14),
            justify="left"
        )
        faq2_answer.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="w")

        # FAQ 3
        faq3_title = ctk.CTkLabel(
            faq_frame,
            text="Q: 病毒扫描怎么一直在检测？",
            font=ctk.CTkFont(family="微软雅黑", size=14, weight="bold"),
            text_color="#4CC2FF"
        )
        faq3_title.grid(row=5, column=0, padx=20, pady=(10, 5), sticky="w")

        faq3_answer = ctk.CTkLabel(
            faq_frame,
            text="A: 本软件通过接入VirusTotal实现病毒扫描，当您选择扫描时，软件会首先尝试hash值匹配，若命中则说明近期该文件\n"
                 "有被其他人上传扫描过，则会快速返回结果；否则需要等待文件上传以及排队扫描，该情况用时几十秒到数分钟不等，\n烦请耐心等待。",
            font=ctk.CTkFont(family="微软雅黑", size=14),
            justify="left"
        )
        faq3_answer.grid(row=6, column=0, padx=20, pady=(0, 20), sticky="w")
        faq_frame.grid(row=1, pady=10, sticky="nsew")

        # 联系信息
        contact_frame = ctk.CTkFrame(scrollable_frame, fg_color="#263844", corner_radius=10)
        contact_frame.columnconfigure(0, weight=0)

        contact_title = ctk.CTkLabel(
            contact_frame,
            text="联系我们",
            font=ctk.CTkFont(family="微软雅黑", size=18, weight="bold")
        )
        contact_title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w", columnspan=2)

        # 文字信息
        contact_email = ctk.CTkLabel(
            contact_frame,
            text="如有任何问题或建议，请联系我们：",
            font=ctk.CTkFont(family="微软雅黑", size=14),
            justify="left"
        )
        contact_email.grid(row=1, column=0, padx=20, sticky="w", columnspan=2)

        # 邮箱信息
        contact_email = ctk.CTkLabel(
            contact_frame,
            text="邮箱: 18325838861@163.com",
            font=ctk.CTkFont(family="微软雅黑", size=14),
            justify="left"
        )
        contact_email.grid(row=2, column=0, padx=20, sticky="w", columnspan=2)

        # GitHub
        github_text_label = ctk.CTkLabel(
            contact_frame,
            text=f"GitHub: ",
            font=ctk.CTkFont(family="微软雅黑", size=14),
        )
        github_text_label.grid(row=3, column=0, padx=(20, 0), pady=(0, 20), sticky="w")

        # GitHub链接（可点击）
        github_link = "https://github.com/Karin-Fur/CampusBeacon"
        github_label = ctk.CTkLabel(
            contact_frame,
            text=f"{github_link}",
            font=ctk.CTkFont(family="微软雅黑", size=14, underline=True),
            text_color="#4CC2FF",  # 使用蓝色突出显示链接
            cursor="hand2"  # 鼠标悬停时显示手型光标
        )
        github_label.grid(row=3, column=1, padx=0, pady=(0, 20), sticky="w")

        # 绑定点击事件
        github_label.bind("<Button-1>", lambda e: webbrowser.open(github_link))

        contact_frame.grid(row=2, pady=10, sticky="nsew")
