"""
Data Validator Decorator Template
数据验证装饰器模板 - Writer 强制使用
"""

import json
import pandas as pd
from typing import Callable, Any, Dict
from functools import wraps

class DataValidationError(Exception):
    """数据验证错误"""
    pass

def validate_schema(schema: Dict[str, str]):
    """
    数据 Schema 验证装饰器
    
    Args:
        schema: 数据结构定义
        {
            'column_name': 'data_type',
            'id': 'int',
            'name': 'str',
            'value': 'float'
        }
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            result = func(*args, **kwargs)
            
            if isinstance(result, pd.DataFrame):
                validate_dataframe(result, schema)
            elif isinstance(result, dict):
                validate_dict(result, schema)
            elif isinstance(result, list):
                for item in result:
                    if isinstance(item, dict):
                        validate_dict(item, schema)
            
            return result
        
        return wrapper
    return decorator

def validate_dataframe(df: pd.DataFrame, schema: Dict[str, str]):
    """验证 DataFrame"""
    for col, dtype in schema.items():
        if col not in df.columns:
            raise DataValidationError(f"缺少列: {col}")
        
        if dtype == 'int' and not pd.api.types.is_integer_dtype(df[col]):
            raise DataValidationError(f"列 {col} 应为整数类型")
        elif dtype == 'float' and not pd.api.types.is_float_dtype(df[col]):
            raise DataValidationError(f"列 {col} 应为浮点数类型")
        elif dtype == 'str' and not pd.api.types.is_string_dtype(df[col]):
            raise DataValidationError(f"列 {col} 应为字符串类型")
    
    if df.isnull().any().any():
        raise DataValidationError("数据包含空值")
    
    return True

def validate_dict(data: Dict, schema: Dict[str, str]):
    """验证字典"""
    for key, dtype in schema.items():
        if key not in data:
            raise DataValidationError(f"缺少键: {key}")
        
        value = data[key]
        
        if dtype == 'int' and not isinstance(value, int):
            raise DataValidationError(f"键 {key} 应为整数类型")
        elif dtype == 'float' and not isinstance(value, (int, float)):
            raise DataValidationError(f"键 {key} 应为数字类型")
        elif dtype == 'str' and not isinstance(value, str):
            raise DataValidationError(f"键 {key} 应为字符串类型")
    
    return True

def handle_outliers(method: str = 'drop'):
    """
    异常值处理装饰器
    
    Args:
        method: 处理方法 ('drop', 'fill', 'clip')
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            result = func(*args, **kwargs)
            
            if isinstance(result, pd.DataFrame):
                if method == 'drop':
                    result = result.dropna()
                elif method == 'fill':
                    result = result.fillna(result.mean())
                elif method == 'clip':
                    result = result.clip(result.quantile(0.01), result.quantile(0.99), axis=1)
            
            return result
        
        return wrapper
    return decorator

@validate_schema({
    'id': 'int',
    'name': 'str',
    'value': 'float'
})
@handle_outliers(method='drop')
def clean_data(data: pd.DataFrame) -> pd.DataFrame:
    """清洗数据示例"""
    return data
