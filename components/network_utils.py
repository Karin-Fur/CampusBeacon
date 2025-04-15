import ctypes
import subprocess


def is_admin():
    """检查当前程序是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def disable_network_connectivity_check(disable=True):
    """
    启用或禁用Windows网络连接指示器活动测试
    
    Args:
        disable (bool): True表示禁用活动测试，False表示启用活动测试
    
    Returns:
        bool: 操作是否成功
    """
    try:
        # 设置注册表键值
        value = 1 if disable else 0
        command = f'reg add "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\NlaSvc\\Parameters\\Internet" /v "EnableActiveProbing" /t REG_DWORD /d {value} /f'
        
        if is_admin():
            # 已经有管理员权限，直接执行
            subprocess.run(command, shell=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return True
        else:
            # 需要提权
            ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                "cmd.exe", 
                f"/c {command}", 
                None, 
                0  # SW_HIDE - 隐藏窗口
            )
            return True
    except Exception as e:
        print(f"修改网络连接指示器设置失败: {e}")
        return False

def get_network_connectivity_check_status():
    """
    获取Windows网络连接指示器活动测试的当前状态
    
    Returns:
        bool: True表示活动测试已禁用，False表示活动测试已启用，None表示获取失败
    """
    try:
        # 查询注册表值
        result = subprocess.run(
            'reg query "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\NlaSvc\\Parameters\\Internet" /v "EnableActiveProbing"',
            shell=True,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode == 0:
            # 解析输出以获取值
            for line in result.stdout.splitlines():
                if "EnableActiveProbing" in line:
                    # 检查值是否为1（禁用）
                    return "0x1" in line or "    1    " in line
        return None
    except Exception as e:
        print(f"获取网络连接指示器设置失败: {e}")
        return None
