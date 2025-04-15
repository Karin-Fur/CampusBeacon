import socket
import threading
import json
import time

from CTkMessagebox import CTkMessagebox


class DeviceNetwork:
    def __init__(self, device_name, ip, broadcast_port, tcp_port, switch_to_file_page_callback,
                 toggle_search_call_back, on_device_discovered=None):
        """
        初始化网络功能。
        Args:
            device_name (str): 当前设备名称。
            ip (str): 当前设备 IP 地址。
            on_device_discovered (function): 新设备发现的回调函数。
        """
        self.device_name = device_name
        self.ip = ip
        self.broadcast_port = broadcast_port
        self.tcp_port = tcp_port
        self.on_device_discovered = on_device_discovered
        self.switch_to_file_page_callback = switch_to_file_page_callback
        self.toggle_search_call_back = toggle_search_call_back
        self.stop_threads = False  # 用于停止线程
        self.tcp_server_socket = None  # 用于TCP监听的socket
    def broadcast_device_info(self):
        """向局域网广播设备信息"""
        self.stop_threads = False

        def broadcast():
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # 设置为广播模式
                sock.settimeout(1)
                try:
                    while not self.stop_threads:
                        # 如果停止标志已设置，直接退出循环
                        if self.stop_threads:
                            break

                        # 构造广播消息
                        message = json.dumps({
                            "device_name": self.device_name,
                            "ip": self.ip,
                            "tcp_port": self.tcp_port
                        })

                        # 发送广播
                        sock.sendto(message.encode("utf-8"), ("<broadcast>", self.broadcast_port))
                        print(f"广播消息: {message}")
                        time.sleep(2)
                except Exception as e:
                    print(f"广播失败: {e}")
                finally:
                    sock.close()
                    print("广播已停止")

        threading.Thread(target=broadcast, daemon=True).start()

    def listen_for_devices(self):
        """监听局域网设备广播"""
        self.stop_threads = False

        def listen():
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(("", self.broadcast_port))
                sock.settimeout(1.0)  # 设置超时时间为 1 秒
                try:
                    while not self.stop_threads:
                        # 如果停止标志已设置，直接退出循环
                        if self.stop_threads:
                            break
                        try:
                            data, addr = sock.recvfrom(1024)  # 接收数据
                            message = json.loads(data.decode("utf-8"))

                            # 提取设备信息
                            device_name = message.get("device_name")
                            ip = message.get("ip")
                            tcp_port = message.get("tcp_port")

                            # 调用设备发现回调
                            if self.on_device_discovered:
                                self.on_device_discovered(device_name, ip, tcp_port)
                        except socket.timeout:
                            continue
                except Exception as e:
                    print(f"监听失败: {e}")
                finally:
                    sock.close()
                    print("监听已停止")

        threading.Thread(target=listen, daemon=True).start()

    def start_tcp_listener(self):
        """启动TCP监听器以接受其他设备的连接"""
        self.stop_threads = False
        self.tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_server_socket.bind((self.ip, self.tcp_port))
        self.tcp_server_socket.listen(5)  # 最大连接数为5
        self.tcp_server_socket.settimeout(1.0)

        print(f"TCP监听器已启动，正在监听 {self.ip}:{self.tcp_port}")

        def listen():
            try:
                while not self.stop_threads:
                    if self.stop_threads:
                        break
                    try:
                        client_socket, client_address = self.tcp_server_socket.accept()
                        print(f"收到来自 {client_address} 的连接请求")
                        threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()
                    except socket.timeout:
                        continue
            except Exception as e:
                print(f"TCP监听器错误: {e}")
            finally:
                self.tcp_server_socket.close()
                print("TCP监听器已停止")

        threading.Thread(target=listen, daemon=True).start()

    def handle_client(self, client_socket):
        """处理每个连接的客户端"""
        try:
            # 接收客户端发送的数据
            data = json.loads(client_socket.recv(1024).decode("utf-8"))
            print(f"收到数据: {data}")

            # 停止设备发现操作，并跳转至连接页面
            if data.get("action") == "connect":
                msg = CTkMessagebox(title="收到连接", message=f"设备:{data.get('device_name')}\nIP:{data.get('ip')}\n请求连接，是否同意？",
                                    option_1="同意", option_2="拒绝", font=("微软雅黑", 14))
                response = msg.get()
                if response == "同意":
                    print(f"成功连接到设备: {data.get('device_name')}")
                    # 切换搜索状态
                    self.toggle_search_call_back()
                    self.stop_threads = True  # 停止设备发现和广播
                    self.switch_to_file_page_callback(data.get('device_name'), data.get('ip'), data.get('tcp_port'))  # 跳转到文件页面
                    # 向客户端发送连接成功响应
                    response = {"status": "connected", "device_name": self.device_name, "ip": self.ip}
                    client_socket.send(json.dumps(response).encode("utf-8"))
                else:
                    response = {"status": "reject", "device_name": self.device_name, "ip": self.ip}
                    client_socket.send(json.dumps(response).encode("utf-8"))
        except Exception as e:
            print(f"处理客户端连接时出错: {e}")
        finally:
            client_socket.close()
            print("客户端连接已关闭")

    def stop(self):
        """停止广播和监听"""
        self.stop_threads = True
