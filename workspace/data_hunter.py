#!/usr/bin/env python3
"""
Data Hunter - Scout Agent for Automated Data Collection & Cleaning
数据猎人 - 自动化数据采集与清洗的侦察员
"""

import subprocess
import json
import os
from datetime import datetime
from typing import List, Dict

class DataHunter:
    """Scout 升级版：具备 Python 自动化分析能力的数据猎人"""
    
    def __init__(self):
        self.workspace = os.getenv('OPENCLAW_WORKSPACE', '/app/workspace')
        self.log_file = f"{self.workspace}/data_hunter.log"
        self.tasks_found = []
        
    def log(self, message: str):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        with open(self.log_file, 'a') as f:
            f.write(log_msg + '\n')
    
    def fetch_github_data_tasks(self) -> List[Dict]:
        """
        从 GitHub 搜索包含数据清洗、采集关键词的 Issue
        """
        self.log("🔍 开始搜索 GitHub 数据任务...")
        
        try:
            # 搜索数据相关的 Issue
            cmd = [
                'gh', 'issue', 'list',
                '--search', 'data cleaning scraping label:agent-take',
                '--json', 'number,title,body,labels'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            tasks = json.loads(result.stdout)
            
            self.log(f"✓ 发现 {len(tasks)} 个数据任务")
            self.tasks_found = tasks
            return tasks
            
        except subprocess.CalledProcessError as e:
            self.log(f"✗ GitHub 搜索失败: {e.stderr}")
            return []
    
    def analyze_task(self, task: Dict) -> Dict:
        """
        分析任务的清洗需求
        """
        self.log(f"📊 分析任务 #{task['number']}: {task['title']}")
        
        analysis = {
            'task_id': task['number'],
            'title': task['title'],
            'body': task['body'],
            'labels': task.get('labels', []),
            'cleaning_type': self._detect_cleaning_type(task),
            'data_source': self._detect_data_source(task),
            'priority': self._calculate_priority(task),
            'status': '#SCOUT_READY'
        }
        
        self.log(f"  - 清洗类型: {analysis['cleaning_type']}")
        self.log(f"  - 数据源: {analysis['data_source']}")
        self.log(f"  - 优先级: {analysis['priority']}")
        
        return analysis
    
    def _detect_cleaning_type(self, task: Dict) -> str:
        """检测清洗类型"""
        body = task.get('body', '').lower()
        
        if 'regex' in body or 'pattern' in body:
            return 'regex_cleaning'
        elif 'outlier' in body or 'anomaly' in body:
            return 'outlier_detection'
        elif 'duplicate' in body:
            return 'deduplication'
        elif 'missing' in body or 'null' in body:
            return 'missing_value_handling'
        else:
            return 'general_cleaning'
    
    def _detect_data_source(self, task: Dict) -> str:
        """检测数据源"""
        body = task.get('body', '').lower()
        
        if 'api' in body:
            return 'api'
        elif 'web' in body or 'scrape' in body:
            return 'web_scraping'
        elif 'csv' in body or 'excel' in body:
            return 'file_upload'
        elif 'database' in body or 'sql' in body:
            return 'database'
        else:
            return 'unknown'
    
    def _calculate_priority(self, task: Dict) -> str:
        """计算优先级"""
        labels = [label.get('name', '').lower() for label in task.get('labels', [])]
        
        if 'urgent' in labels or 'critical' in labels:
            return 'high'
        elif 'important' in labels:
            return 'medium'
        else:
            return 'low'
    
    def trigger_writer(self, analysis: Dict):
        """
        触发 Writer Agent 生成清洗脚本
        """
        self.log(f"✍️  触发 Writer 生成清洗脚本...")
        
        prompt = f"""
        任务 #{analysis['task_id']}: {analysis['title']}
        
        清洗类型: {analysis['cleaning_type']}
        数据源: {analysis['data_source']}
        优先级: {analysis['priority']}
        
        请生成基于 pandas/polars 的清洗脚本，包含:
        1. Schema 校验函数
        2. 异常值处理逻辑
        3. 数据质量检查
        4. 输出验证
        
        标记: #WRITER_PATCHED
        """
        
        # 这里会通过 OpenClaw 系统调用 Writer Agent
        self.log(f"  - 已发送给 Writer Agent")
        self.log(f"  - 等待 #WRITER_PATCHED 标记...")
    
    def generate_report(self):
        """
        生成数据猎人日报
        """
        self.log("📋 生成数据猎人日报...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'tasks_found': len(self.tasks_found),
            'tasks': [self.analyze_task(task) for task in self.tasks_found],
            'status': 'ready_for_processing'
        }
        
        report_file = f"{self.workspace}/data_hunter_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.log(f"✓ 日报已生成: {report_file}")
        return report
    
    def run(self):
        """运行数据猎人"""
        self.log("=" * 60)
        self.log("🚀 数据猎人启动")
        self.log("=" * 60)
        
        # 1. 搜索任务
        tasks = self.fetch_github_data_tasks()
        
        if not tasks:
            self.log("⚠️  未发现数据任务")
            return
        
        # 2. 分析任务
        for task in tasks:
            analysis = self.analyze_task(task)
            self.trigger_writer(analysis)
        
        # 3. 生成报告
        report = self.generate_report()
        
        self.log("=" * 60)
        self.log("✅ 数据猎人执行完成")
        self.log("=" * 60)


if __name__ == '__main__':
    hunter = DataHunter()
    hunter.run()
