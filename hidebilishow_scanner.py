#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站会员购项目Hide状态扫描器
用于扫描指定ID范围内的项目，检查hide字段是否为1
"""

import requests
import time
import json
import sys
import os
import re
from datetime import datetime
from typing import List, Dict, Optional


def get_version():
    """获取程序版本号"""
    try:
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        version_file = os.path.join(base_path, "version_info.txt")
        
        if os.path.exists(version_file):
            with open(version_file, 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.search(r"StringStruct\(u'ProductVersion',\s*u'([^']+)'\)", content)
                if match:
                    return match.group(1)
        
        return "1.0.0"
    except Exception as e:
        return "未知版本"


def show_muse_banner():
    """显示MUSE横幅"""
    banner = r"""
          _____                    _____                    _____                    _____          
         /\    \                  /\    \                  /\    \                  /\    \         
        /::\____\                /::\____\                /::\    \                /::\    \        
       /::::|   |               /:::/    /               /::::\    \              /::::\    \       
      /:::::|   |              /:::/    /               /::::::\    \            /::::::\    \      
     /::::::|   |             /:::/    /               /:::/\:::\    \          /:::/\:::\    \     
    /:::/|::|   |            /:::/    /               /:::/__\:::\    \        /:::/__\:::\    \    
   /:::/ |::|   |           /:::/    /                \:::\   \:::\    \      /::::\   \:::\    \   
  /:::/  |::|___|______    /:::/    /      _____    ___\:::\   \:::\    \    /::::::\   \:::\    \  
 /:::/   |::::::::\    \  /:::/____/      /\    \  /\   \:::\   \:::\    \  /:::/\:::\   \:::\    \ 
/:::/    |:::::::::\____\|:::|    /      /::\____\/::\   \:::\   \:::\____\/:::/__\:::\   \:::\____\
\::/    / ~~~~~/:::/    /|:::|____\     /:::/    /\:::\   \:::\   \::/    /\:::\   \:::\   \::/    /
 \/____/      /:::/    /  \:::\    \   /:::/    /  \:::\   \:::\   \/____/  \:::\   \:::\   \/____/ 
             /:::/    /    \:::\    \ /:::/    /    \:::\   \:::\    \       \:::\   \:::\    \     
            /:::/    /      \:::\    /:::/    /      \:::\   \:::\____\       \:::\   \:::\____\    
           /:::/    /        \:::\__/:::/    /        \:::\  /:::/    /        \:::\   \::/    /    
          /:::/    /          \::::::::/    /          \:::\/:::/    /          \:::\   \/____/     
         /:::/    /            \::::::/    /            \::::::/    /            \:::\    \         
        /:::/    /              \::::/    /              \::::/    /              \:::\____\        
        \::/    /                \::/____/                \::/    /                \::/    /        
         \/____/                  ~~                       \/____/                  \/____/                                                                                                        
    """
    print(banner)
    version = get_version()
    print(f"MUSE-HideBiliShow-Scanner v{version}")
    print("=" * 88)
    print()


class BilibiliShowScanner:
    """B站会员购项目扫描器"""
    
    def __init__(self):
        self.api_url = "https://show.bilibili.com/api/ticket/project/getV2?id="
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://show.bilibili.com/',
        })
        self.hidden_projects = []
        self.scan_results = []
        
    def get_project_info(self, project_id: int) -> Optional[Dict]:
        """
        获取项目信息
        
        Args:
            project_id: 项目ID
            
        Returns:
            项目信息字典，如果请求失败返回None
        """
        try:
            url = f"{self.api_url}{project_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('code') == 0:
                return data.get('data')
            else:
                print(f"API返回错误 ID {project_id}: {data.get('message', '未知错误')}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"请求失败 ID {project_id}: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON解析失败 ID {project_id}: {str(e)}")
            return None
        except Exception as e:
            print(f"未知错误 ID {project_id}: {str(e)}")
            return None
    
    def scan_project(self, project_id: int) -> Dict:
        """
        扫描单个项目
        
        Args:
            project_id: 项目ID
            
        Returns:
            扫描结果字典
        """
        result = {
            'id': project_id,
            'hide': None,
            'name': None,
            'status': 'unknown',
            'error': None
        }
        
        project_info = self.get_project_info(project_id)
        
        if project_info is None:
            result['status'] = 'error'
            result['error'] = '无法获取项目信息'
            return result
        
        result['hide'] = project_info.get('hide')
        result['name'] = project_info.get('name', '未知项目')
        result['status'] = 'success'
        
        # 如果hide为1，添加到隐藏项目列表
        if result['hide'] == 1:
            self.hidden_projects.append(result)
            
        return result
    
    def scan_range(self, start_id: int, end_id: int, interval: float = 0.5):
        """
        扫描指定范围的项目ID
        
        Args:
            start_id: 起始ID
            end_id: 结束ID
            interval: 扫描间隔（秒）
        """
        print(f"开始扫描项目ID范围: {start_id} - {end_id}")
        print(f"扫描间隔: {interval}秒")
        print("-" * 60)
        
        total_count = end_id - start_id + 1
        scanned_count = 0
        error_count = 0
        
        start_time = datetime.now()
        
        for project_id in range(start_id, end_id + 1):
            scanned_count += 1
            
            # 显示进度
            progress = (scanned_count / total_count) * 100
            print(f"[{progress:.1f}%] 扫描ID: {project_id}", end=" ")
            
            # 扫描项目
            result = self.scan_project(project_id)
            self.scan_results.append(result)
            
            if result['status'] == 'error':
                error_count += 1
                print(f"❌ 错误: {result['error']}")
            elif result['hide'] == 1:
                print(f"发现隐藏项目: {result['name']}")
            else:
                print(f"hide={result['hide']}")
            
            # 如果不是最后一个ID，等待间隔时间
            if project_id < end_id:
                time.sleep(interval)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("-" * 60)
        print("扫描完成!")
        print(f"总耗时: {duration}")
        print(f"扫描总数: {total_count}")
        print(f"成功扫描: {total_count - error_count}")
        print(f"错误数量: {error_count}")
        print(f"发现隐藏项目: {len(self.hidden_projects)}")
        
        if self.hidden_projects:
            print("\n隐藏项目列表:")
            for project in self.hidden_projects:
                print(f"  ID: {project['id']} - {project['name']}")
    
    def save_results(self, filename: str = None):
        """
        保存扫描结果到JSON文件
        
        Args:
            filename: 文件名，如果为None则使用时间戳
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bilibili_scan_results_{timestamp}.json"
        
        results_data = {
            'scan_time': datetime.now().isoformat(),
            'total_scanned': len(self.scan_results),
            'hidden_count': len(self.hidden_projects),
            'hidden_projects': self.hidden_projects,
            'all_results': self.scan_results
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, ensure_ascii=False, indent=2)
            print(f"\n扫描结果已保存到: {filename}")
        except Exception as e:
            print(f"❌ 保存结果失败: {str(e)}")


def get_user_input():
    """获取用户输入的ID范围"""
    
    while True:
        try:
            start_id = int(input("请输入起始ID: "))
            if start_id <= 0:
                print("❌ 起始ID必须大于0")
                continue
            break
        except ValueError:
            print("❌ 请输入有效的数字")
    
    while True:
        try:
            end_id = int(input("请输入结束ID: "))
            if end_id < start_id:
                print("❌ 结束ID必须大于等于起始ID")
                continue
            break
        except ValueError:
            print("❌ 请输入有效的数字")
    
    return start_id, end_id


def main():
    """主函数"""
    while True:
        try:
            # 显示横幅
            show_muse_banner()
            
            # 获取用户输入
            start_id, end_id = get_user_input()
            
            # 创建扫描器实例
            scanner = BilibiliShowScanner()
            
            # 开始扫描
            scanner.scan_range(start_id, end_id)
            
            # 询问是否保存结果
            save_choice = input("\n是否保存扫描结果到文件? (y/n): ").lower().strip()
            if save_choice in ['y', 'yes', '是', '保存']:
                scanner.save_results()
            
            print("\n程序执行完毕!")
            
        except KeyboardInterrupt:
            print("\n\n⚠️ 用户中断扫描")
        except Exception as e:
            import traceback
            print(f"\n❌ 程序执行出错: {str(e)}")
            print("\n完整错误详情:")
            print(traceback.format_exc())
        
        # 退出选择
        while True:
            choice = input("\n退出(T)/重新开始(S): ").strip().upper()
            if choice == 'T':
                print("程序已退出")
                return
            elif choice == 'S':
                print("\n重新开始程序...\n")
                break
            else:
                print("请输入 T 或 S")


if __name__ == "__main__":
    main()