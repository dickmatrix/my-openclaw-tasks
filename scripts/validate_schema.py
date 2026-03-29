#!/usr/bin/env python3
"""
Schema Registry Guard - Schema 自动化治理
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List

class SchemaRegistryGuard:
    def __init__(self):
        self.registry_dir = Path(__file__).parent.parent / 'schema_registry'
        self.master_file = self.registry_dir / 'master.json'
        self.master_registry = self._load_master_registry()
    
    def _load_master_registry(self) -> Dict:
        """加载主索引"""
        if self.master_file.exists():
            with open(self.master_file, 'r') as f:
                return json.load(f)
        return {'schemas': {}, 'version': '1.0.0'}
    
    def validate_schema_format(self, schema_file: Path) -> bool:
        """验证 Schema 格式"""
        print(f"[Schema Guard] 验证格式: {schema_file}")
        
        try:
            with open(schema_file, 'r') as f:
                schema = json.load(f)
            
            # 检查必需字段
            required_fields = ['name', 'version', 'fields']
            for field in required_fields:
                if field not in schema:
                    print(f"  ✗ 缺少必需字段: {field}")
                    return False
            
            print(f"  ✓ 格式验证通过")
            return True
        
        except json.JSONDecodeError as e:
            print(f"  ✗ JSON 格式错误: {e}")
            return False
    
    def calculate_similarity(self, schema1: Dict, schema2: Dict) -> float:
        """计算 Jaccard 相似度"""
        fields1 = set(schema1.get('fields', {}).keys())
        fields2 = set(schema2.get('fields', {}).keys())
        
        if not fields1 and not fields2:
            return 1.0
        
        intersection = len(fields1 & fields2)
        union = len(fields1 | fields2)
        
        return intersection / union if union > 0 else 0
    
    def check_duplicates(self, new_schema: Dict) -> bool:
        """检查重复 Schema"""
        print("[Schema Guard] 检查重复...")
        
        for schema_name, existing_schema in self.master_registry['schemas'].items():
            similarity = self.calculate_similarity(new_schema, existing_schema)
            
            if similarity > 0.9:
                print(f"  ✗ 与 {schema_name} 相似度过高 ({similarity:.2%})")
                print(f"    建议: 归并或重命名")
                return False
        
        print(f"  ✓ 无重复 Schema")
        return True
    
    def add_semver_tag(self, schema: Dict) -> Dict:
        """添加 SemVer 标签"""
        print("[Schema Guard] 添加版本标签...")
        
        if 'version' not in schema:
            schema['version'] = '1.0.0'
        
        schema['_metadata'] = {
            'created_at': __import__('datetime').datetime.now().isoformat(),
            'semver': schema['version']
        }
        
        print(f"  ✓ 版本标签: {schema['version']}")
        return schema
    
    def register_schema(self, schema_file: Path) -> bool:
        """注册 Schema"""
        print(f"[Schema Guard] 注册 Schema: {schema_file}")
        
        # 验证格式
        if not self.validate_schema_format(schema_file):
            return False
        
        # 加载新 Schema
        with open(schema_file, 'r') as f:
            new_schema = json.load(f)
        
        # 检查重复
        if not self.check_duplicates(new_schema):
            return False
        
        # 添加版本标签
        new_schema = self.add_semver_tag(new_schema)
        
        # 注册到主索引
        schema_name = new_schema.get('name', schema_file.stem)
        self.master_registry['schemas'][schema_name] = new_schema
        
        # 保存主索引
        self.master_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.master_file, 'w') as f:
            json.dump(self.master_registry, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Schema 已注册: {schema_name}")
        return True
    
    def validate_all_schemas(self) -> bool:
        """验证所有 Schema"""
        print("[Schema Guard] 验证所有 Schema...")
        
        schema_files = list(self.registry_dir.glob('*.json'))
        schema_files = [f for f in schema_files if f.name != 'master.json']
        
        all_valid = True
        for schema_file in schema_files:
            if not self.validate_schema_format(schema_file):
                all_valid = False
        
        return all_valid

if __name__ == '__main__':
    guard = SchemaRegistryGuard()
    
    # 验证所有 Schema
    if guard.validate_all_schemas():
        print("\n✓ 所有 Schema 验证通过")
        sys.exit(0)
    else:
        print("\n✗ Schema 验证失败")
        sys.exit(1)
