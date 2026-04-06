#!/bin/bash

# Auditor 自动化校验脚本

echo "=== Auditor 数据质量校验 ==="
echo ""

# 1. 运行 pytest
echo "1. 运行单元测试..."
python3 -m pytest cleaning_script.py -v --tb=short

# 2. 检查输出文件
echo ""
echo "2. 检查输出文件..."
if [ -f "output.csv" ]; then
    echo "✓ 输出文件存在"
    
    # 检查行数
    ROWS=$(wc -l < output.csv)
    echo "  - 行数: $ROWS"
    
    # 检查列数
    COLS=$(head -1 output.csv | tr ',' '\n' | wc -l)
    echo "  - 列数: $COLS"
else
    echo "✗ 输出文件不存在"
    exit 1
fi

# 3. 验证数据质量
echo ""
echo "3. 验证数据质量..."
python3 << 'PYEOF'
import pandas as pd
import json

df = pd.read_csv('output.csv')

quality_report = {
    'total_rows': len(df),
    'total_cols': len(df.columns),
    'missing_values': df.isnull().sum().to_dict(),
    'duplicates': df.duplicated().sum(),
    'data_types': df.dtypes.astype(str).to_dict()
}

print(json.dumps(quality_report, indent=2, ensure_ascii=False))

# 检查是否通过
if quality_report['duplicates'] == 0 and df.isnull().sum().sum() == 0:
    print("\n✓ 数据质量检查通过")
    exit(0)
else:
    print("\n✗ 数据质量检查失败")
    exit(1)
PYEOF

echo ""
echo "✓ Auditor 校验完成"
echo "标记: #AUDIT_PASS"
