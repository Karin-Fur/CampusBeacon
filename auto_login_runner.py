import requests
import time
import subprocess
import re
import sys
import os
from plyer import notification  # 使用plyer库显示通知


# 从EXE文件末尾读取配置
def get_config_from_exe():
    """从当前EXE文件中读取配置"""
    try:
        # 判断是否在打包环境中运行
        exe_path = sys.executable if getattr(sys, 'frozen', False) else __file__

        with open(exe_path, 'rb') as f:
            content = f.read()

        start_marker = b'[CONFIG]'
        end_marker = b'[END_CONFIG]'

        start_pos = content.find(start_marker)
        end_pos = content.find(end_marker)

        if start_pos > 0 and end_pos > start_pos:
            config_text = content[start_pos + len(start_marker):end_pos].decode('utf-8')

            config = {}
            for line in config_text.strip().split('\r\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()

            print("已从EXE文件读取配置信息")
            return config

        print("在EXE中未找到配置信息，使用默认值")
        return {
            "USERNAME": "默认用户名",
            "PASSWORD": "默认密码",
            "ISP": "校园网",
            "SCHOOL": "安徽理工大学",
            "ICON_PATH": ""
        }
    except Exception as e:
        print(f"读取配置失败: {str(e)}")
        # 返回默认配置
        return {
            "USERNAME": "默认用户名",
            "PASSWORD": "默认密码",
            "ISP": "校园网",
            "SCHOOL": "安徽理工大学",
            "ICON_PATH": ""
        }


# 获取配置信息
CONFIG = get_config_from_exe()


def show_notification(title, message):
    """显示系统通知"""
    # 使用plyer显示通知，跨平台
    try:
        # 查找图标路径
        icon_path = CONFIG.get("ICON_PATH", "")
        if not icon_path or not os.path.exists(icon_path):
            # 查找可能的图标位置
            possible_paths = [
                os.path.join(os.path.dirname(sys.executable), "icons", "window.ico"),
                os.path.join(os.path.dirname(__file__), "icons", "window.ico"),
                os.path.join(os.getcwd(), "icons", "window.ico")
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    icon_path = path
                    break

        notification.notify(
            title=title,
            message=message,
            app_icon=icon_path,
            timeout=5  # 设置通知显示时间（秒）
        )
    except Exception as e:
        print(f"通知显示失败: {str(e)}")
        # 使用备用方法显示通知 - Windows专用
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, title, 0x40)
        except:
            print(f"通知: {title} - {message}")


def extract_student_id(username):
    """从用户名中提取学号"""
    # 尝试使用正则表达式提取数字部分作为学号
    match = re.search(r'(\d+)', username)
    if match:
        return match.group(1)
    return username  # 如果无法提取，则返回原始用户名


def login_campus_network():
    """尝试登录校园网"""
    # 登录URL
    url = "http://10.255.0.19"

    # 从配置中获取用户名和密码
    username = CONFIG.get("USERNAME", "默认用户名")
    password = CONFIG.get("PASSWORD", "默认密码")
    isp = CONFIG.get("ISP", "校园网")

    # 提取学号
    student_id = extract_student_id(username)

    # 登录数据
    data = {
        "DDDDD": username,
        "upass": password,
        "R1": "0",
        "R3": "1",
        "R6": "0",
        "pare": "00",
        "OMKKey": "123456"
    }

    # 请求头
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Host": "10.255.0.19",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
    }

    try:
        # 发送登录请求
        response = requests.post(url, data=data, headers=headers, timeout=5)

        # 检查响应
        if response.status_code == 200:
            # 安徽理工大学认证系统特殊处理：即使认证成功，也不会在响应中明确提示
            response_data = response.text
            script_match = re.search(r"msga='([^']+)'", response_data)
            # 安徽理工大学校园网无论密码正确与否均返回200，通过msga字段判断
            if script_match:
                # 提取到的 msga 字段值
                msga = script_match.group(1)
                return False, f"登录失败，请检查账号密码({msga})"
            else:
                if check_network():
                    return True, "登录成功！网络连接正常"
                else:
                    return False, "登录成功，但网络连接不正常"
        else:
            return False, f"登录失败，状态码: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"登录失败: {str(e)}"


def check_network():
    """检查网络连通性"""
    command = f"ping -n 1 www.baidu.com"  # 发送一次 ping 请求
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode == 0:
        return True
    else:
        return False


def auto_login():
    """自动登录函数"""
    max_attempts = 3
    attempt = 0
    success = False

    # 从配置获取学校和ISP信息
    username = CONFIG.get("USERNAME", "默认用户名")
    isp = CONFIG.get("ISP", "校园网")
    school = CONFIG.get("SCHOOL", "安徽理工大学")

    # 显示开始登录通知
    show_notification(
        f"{school}校园网登录",
        "正在尝试登录校园网，请稍候..."
    )

    while attempt < max_attempts and not success:
        attempt += 1
        print(f"尝试第{attempt}次登录...")

        # 尝试登录
        success, message = login_campus_network()

        if success:
            print("登录成功！")
            print("网络连接正常，可以访问互联网")

            # 显示成功通知
            show_notification(
                "登录成功",
                f"——已连接至{school}网络\n学号: {extract_student_id(username)}\n运营商: {isp}\n"
            )
            break
        else:
            print(f"{message}")
            if attempt < max_attempts:
                print(f"将在3秒后重试...")
                time.sleep(3)

    if attempt >= max_attempts and not success:
        print("多次尝试登录失败，请手动检查网络或账号密码")

        # 显示失败通知
        show_notification(
            "登录失败",
            "多次尝试登录失败，请手动检查网络或账号密码"
        )


# 程序入口点
if __name__ == "__main__":
    auto_login()

    # 等待一段时间，确保通知显示完成
    time.sleep(6)