#!/usr/bin/env python3
"""
Data Hunter - Scout Agent Enhancement
数据猎人 - Scout Agent 增强版本
自动从 GitHub 发现数据采集和清洗任务
"""

import subprocess
import json
import os
from datetime import datetime
from typing import List, Dict

class DataHunter:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN', '')
        self.openclaw_workspace = os.getenv('OPENCLAW_WORKSPACE', '/app/workspace')
        self.log_file = f"{self.openclaw_workspace}/data_hunter/logs/hunt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
    def log(self, message: str):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        with open(self.log_file, 'a') as f:
            f.write(log_msg + '\n')
    
    def fetch_github_data_tasks(self) -> List[Dict]:
        """从 GitHub 搜索数据采集和清洗任务"""
        self.log("开始搜索 GitHub 数据任务...")
        
        try:
            cmd = [
                'gh', 'issue', 'list',
                '--search', 'label:data-cleaning OR label:web-scraping OR label:data-collection',
                '--json', 'number,title,body,labels,createdAt',
                '--limit', '10'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            tasks = json.loads(result.stdout)
            
            self.log(f"发现 {len(tasks)} 个数据任务")
            return tasks
            
        except subprocess.CalledProcessError as e:
            self.log(f"GitHub 搜索失败: {e.stderr}")
            return []
    
    def analyze_task(self, task: Dict) -> Dict:
        """分析任务的清洗需求"""
        self.log(f"分析任务 #{task['number']}: {task['title']}")
        
        analysis = {
            'task_id': task['number'],
            'title': task['title'],
            'type': self._detect_task_type(task),
            'complexity': self._estimate_complexity(task),
            'required_tools': self._identify_tools(task),
            'estimated_time': self._estimate_time(task)
        }
        
        return analysis
    
    def _detect_task_type(self, task: Dict) -> str:
        """检测任务类型"""
        body = task.get('body', '').lower()
        
        if 'scrape' in body or 'crawl' in body:
            return 'web_scraping'
        elif 'clean' in body or 'normalize' in body:
            return 'data_cleaning'
        elif 'extract' in body:
            return 'data_extraction'
        else:
            return 'data_processing'
    
    def _estimate_complexity(self, task: Dict) -> str:
        """估计任务复杂度"""
        body = task.get('body', '')
        
        if len(body) > 1000:
            return 'high'
        elif len(body) > 500:
            return 'medium'
        else:
            return 'low'
    
    def _identify_tools(self, task: Dict) -> List[str]:
        """识别所需工具"""
        body = task.get('body', '').lower()
        tools = []
        
        if 'json' in body:
            tools.append('json')
        if 'csv' in body or 'excel' in body:
            tools.append('pandas')
        if 'regex' in body or 'pattern' in body:
            tools.append('regex')
        if 'api' in body:
            tools.append('requests')
        if 'html' in body or 'xml' in body:
            tools.append('beautifulsoup')
        
        return tools if tools else ['pandas', 'regex']
    
    def _estimate_time(self, task: Dict) -> str:
        """估计完成时间"""
        complexity = self._estimate_complexity(task)
        
        if complexity == 'high':
            return '2-4 hours'
        elif complexity == 'medium':
            return '1-2 hours'
        else:
            return '30 minutes'
    
    def generate_scout_report(self, tasks: List[Dict]) -> str:
        """生成 Scout 侦察报告"""
        self.log("生成 Scout 侦察报告...")
        
        report = "# Scout 数据任务侦察报告\n\n"
        report += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"**发现任务数**: {len(tasks)}\n\n"
        
        for task in tasks:
            analysis = self.analyze_task(task)
            report += f"## 任务 #{analysis['task_id']}: {analysis['title']}\n\n"
            report += f"- **类型**: {analysis['type']}\n"
            report += f"- **复杂度**: {analysis['complexity']}\n"
            report += f"- **所需工具**: {', '.join(analysis['required_tools'])}\n"
            report += f"- **预计时间**: {analysis['estimated_time']}\n\n"
        
        report += "**#SCOUT_READY**\n"
        
        return report
    
    def run(self):
        """运行数据猎人"""
        self.log("=" * 60)
        self.log("数据猎人启动")
        self.log("=" * 60)
        
        tasks = self.fetch_github_data_tasks()
        
        if not tasks:
            self.log("未发现新任务")
            return
        
        report = self.generate_scout_report(tasks)
        
        report_file = f"{self.openclaw_workspace}/data_hunter/results/scout_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        self.log(f"报告已保存: {report_file}")
        self.log("=" * 60)
        self.log("数据猎人完成")
        self.log("=" * 60)

if __name__ == '__main__':
    hunter = DataHunter()
    hunter.run()
