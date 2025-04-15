import customtkinter as ctk
import tkinter as tk
from PIL import Image

# 全局变量，用于存储help_icon
help_icon = None

# 设置图标的函数
def set_help_icon(icon):
    """
    设置帮助图标
    :param icon: CTkImage对象
    """
    global help_icon
    help_icon = icon


class CustomTopWindow(ctk.CTkToplevel):
    def __init__(self, master=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        # 确保窗口总是位于最前面
        self.attributes("-topmost", True)
        # 锁定所有输入事件到当前窗口
        self.grab_set()
        # 重载关闭窗口事件，确保关闭时释放输入锁定
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        # 在窗口关闭时释放输入锁定
        self.grab_release()
        self.destroy()


class CustomScrollableFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, *args, **kwargs):
        # 调用父类构造方法
        super().__init__(master, *args, **kwargs)

        # 隐藏滚动条
        self._scrollbar.grid(padx=10)
        self._scrollbar.grid_forget()  # 隐藏滚动条
        self._parent_canvas.grid(padx=5)


class ToolTip:
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay  # 延迟显示时间，单位为毫秒
        self.tooltip = None
        self.tooltip_id = None  # 用于存储定时任务ID
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)

    def on_enter(self, event):
        # 当鼠标进入时，启动一个延迟任务来显示工具提示
        self.tooltip_id = self.widget.after(self.delay, self.show_tooltip)

    def on_leave(self, event):
        # 当鼠标离开时，取消延迟任务并隐藏工具提示
        if self.tooltip_id:
            self.widget.after_cancel(self.tooltip_id)
        self.hide_tooltip()

    def show_tooltip(self):
        # 获取鼠标当前位置
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 35  # 添加一些偏移量
        y += self.widget.winfo_rooty() + 55  # 添加一些偏移量

        # 创建一个新的顶级窗口来显示提示信息
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)  # 去除窗口边框
        self.tooltip.wm_geometry(f"+{x}+{y}")  # 设置位置

        # 创建一个标签来显示悬浮提示
        label = tk.Label(self.tooltip, text=self.text, background="#111921", fg="white", font=("微软雅黑", 12))
        label.pack()

    def hide_tooltip(self):
        if self.tooltip:
            self.tooltip.destroy()  # 销毁工具提示窗口


def create_custom_help_button(parent):
    global help_icon
    if help_icon is None:
        # 如果图标未设置，使用默认图标（这种情况应该避免）
        print("警告: 帮助图标未设置，使用默认图标可能会导致错误")
        try:
            help_icon = ctk.CTkImage(light_image=Image.open("icons/help_light.png"),
                                    dark_image=Image.open("icons/help_dark.png"), size=(18, 18))
        except Exception as e:
            print(f"错误: 无法加载默认图标 - {str(e)}")
            return ctk.CTkButton(parent, text="?", state="disabled", width=24,
                                height=24, fg_color="transparent")
    
    return ctk.CTkButton(parent, text="", image=help_icon, state="disabled", width=24,
                         height=24, fg_color="transparent")
