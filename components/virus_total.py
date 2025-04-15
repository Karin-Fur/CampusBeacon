import time
import os
import requests
from PyQt5.QtCore import QThread, pyqtSignal
import hashlib


class VirusTotalThread(QThread):
    # 定义信号，用于任务完成后返回报告内容
    report_signal = pyqtSignal(list)

    def __init__(self, temp_file_paths, api_key):
        super().__init__()
        self.file_paths = temp_file_paths
        self.api_key = api_key
        print(f"测试key{self.api_key}")
        self.file_id = []
        self.completed_reports = []
        # 文件大小限制（字节）
        self.SIZE_LIMIT_SMALL = 32 * 1024 * 1024  # 32MB
        self.SIZE_LIMIT_LARGE = 650 * 1024 * 1024  # 650MB
        
    def run(self):
        try:
            headers = {'x-apikey': self.api_key}
            
            self.file_path_id_map = {}  # 文件路径和 file_id 的映射
            self.completed_reports = []  # 清空
            for file in self.file_paths:
                # 检查文件大小
                file_size = os.path.getsize(file)
                
                # 如果文件超过650MB，标记为"文件过大"并跳过
                if file_size >= self.SIZE_LIMIT_LARGE:
                    oversized_report = self.create_oversized_file_report(file)
                    self.completed_reports.append(oversized_report)
                    continue
                
                # 计算文件的哈希值
                file_hash = self.calculate_file_hash(file)
                # 先通过哈希值查询报告
                report_data = self.get_report_by_hash(file_hash, headers)
                if report_data:
                    # 在报告里嵌入文件路径
                    report_data['file_path'] = file
                    print(f"文件 {file} 的报告已存在，跳过上传")
                    self.completed_reports.append(report_data)
                else:
                    # 根据文件大小选择不同的上传方式
                    if file_size < self.SIZE_LIMIT_SMALL:
                        # 小于32MB的文件使用常规上传
                        self.upload_small_file(file, headers)
                    else:
                        # 大于等于32MB小于650MB的文件使用upload_url
                        self.upload_large_file(file, headers)

            # 轮询所有文件的报告
            self.poll_reports(self.file_id, headers)

            # 任务完成后发射信号，发送所有文件的报告数据回主线程
            self.report_signal.emit(self.completed_reports)

        except Exception as e:
            print(f"任务过程中出错: {e}")
            
    def create_oversized_file_report(self, file_path):
        """
        为超过大小限制的文件创建一个特殊的报告
        """
        # 创建一个模拟的报告结构，标记为"文件过大"
        oversized_report = {
            'file_path': file_path,
            'data': {
                'attributes': {
                    'status': 'completed',
                    'stats': {
                        'malicious': 0,
                        'suspicious': 0,
                        'undetected': 0,
                        'failure': 0
                    },
                    'results': {},
                    'date': int(time.time()),
                },
                'type': 'analysis',
                'id': 'oversized_file',
            },
            'oversized': True  # 添加一个标记表示这是超大文件
        }
        return oversized_report
            
    def upload_small_file(self, file, headers):
        """
        上传小于32MB的文件
        """
        upload_url = 'https://www.virustotal.com/api/v3/files'
        with open(file, 'rb') as f:
            files = {'file': (file, f)}
            response = requests.post(upload_url, files=files, headers=headers)
            if response.status_code == 200:
                result = response.json()
                file_id = result['data']['id']
                self.file_id.append(file_id)
                self.file_path_id_map[file_id] = file  # 保存文件路径和 file_id 的映射
            else:
                print(f"提交文件 {file} 失败: {response.status_code}")
                
    def upload_large_file(self, file, headers):
        """
        上传大于等于32MB小于650MB的文件，使用upload_url端点
        """
        # 首先获取上传URL
        get_url_endpoint = 'https://www.virustotal.com/api/v3/files/upload_url'
        response = requests.get(get_url_endpoint, headers=headers)
        
        if response.status_code == 200:
            upload_url = response.json()['data']
            
            # 使用获取到的URL上传文件
            with open(file, 'rb') as f:
                files = {'file': (file, f)}
                upload_response = requests.post(upload_url, files=files, headers=headers)
                
                if upload_response.status_code == 200:
                    result = upload_response.json()
                    file_id = result['data']['id']
                    self.file_id.append(file_id)
                    self.file_path_id_map[file_id] = file
                else:
                    print(f"使用upload_url提交大文件 {file} 失败: {upload_response.status_code}")
        else:
            print(f"获取upload_url失败: {response.status_code}")

    def poll_reports(self, file_ids, headers):
        """
        轮询多个文件的 VirusTotal 报告，直到所有文件的报告完成。
        """
        reports = {file_id: None for file_id in file_ids}  # 初始化报告字典
        for file_id in file_ids:
            print(file_id)
        while True:
            all_completed = True  # 假设所有文件的报告都完成
            for file_id in file_ids:
                if reports[file_id] is None:  # 仅查询尚未完成的文件
                    report_url = f'https://www.virustotal.com/api/v3/analyses/{file_id}'
                    response = requests.get(report_url, headers=headers)
                    if response.status_code == 200:
                        report_data = response.json()
                        status = report_data['data']['attributes']['status']

                        if status == 'queued':
                            all_completed = False  # 文件还在队列中，报告尚未完成
                            print("文件还在队列中，报告尚未完成")
                        elif status == 'completed':
                            # 报告生成完成，保存结果
                            reports[file_id] = report_data
                            file_id = report_data['data']['id']
                            file_path = self.file_path_id_map.get(file_id)  # 根据 file_id 获取文件路径
                            report_data['file_path'] = file_path    # 嵌入文件路径
                            self.completed_reports.append(report_data)

                        else:
                            # 如果报告尚未完成，继续等待
                            all_completed = False
                    else:
                        print(f"查询报告失败: {response.status_code}")
                        return None

            if all_completed:
                # 如果所有文件都已完成，退出循环并返回所有报告
                break

            time.sleep(15)  # 等待 15 秒后再次查询

    def calculate_file_hash(self, file_path, hash_algorithm='md5'):
        """
        计算文件的哈希值
        """
        hash_func = hashlib.new(hash_algorithm)

        with open(file_path, 'rb') as f:
            # 每次读取文件的一部分数据（较大的文件）
            while chunk := f.read(8192):
                hash_func.update(chunk)
        print(hash_func.hexdigest())
        return hash_func.hexdigest()

    def get_report_by_hash(self, file_hash, headers):
        """
        根据文件哈希值查询报告，如果报告已存在，则返回报告数据
        """
        try:
            url = f'https://www.virustotal.com/api/v3/files/{file_hash}'
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                report_data = response.json()
                # 该报告结构不同，将 'last_analysis_results' 改为 'results'
                report_data['data']['attributes']['results'] = report_data['data']['attributes'].pop(
                    'last_analysis_results')
                report_data['data']['attributes']['date'] = report_data['data']['attributes'].pop(
                    'last_analysis_date')
                return report_data  # 返回已有的报告数据
            elif response.status_code == 400:
                print(f"文件哈希 {file_hash} 未找到报告")
            else:
                print(f"查询报告失败: {response.status_code}")
        except Exception as e:
            print(f"通过hash值获取报告出错{e}")

        return None
