#!/usr/bin/env python3
"""
TemplateGenerator 模板生成器 - 外贸邮件、合同协议、SOP文档、科幻设定
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json
import re


@dataclass
class Template:
    """模板数据结构"""
    id: str
    name: str
    category: str
    content: str
    variables: List[str]
    description: str


class TemplateGenerator:
    """模板生成工具"""
    
    def __init__(self):
        self.name = "template_generator"
        self.description = "外贸邮件、合同协议、SOP文档、科幻设定模板生成"
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, List[Template]]:
        """加载预设模板库"""
        return {
            "foreign_trade": [
                Template(
                    id="cold_email",
                    name="外贸开发信",
                    category="foreign_trade",
                    content=self._get_cold_email_template(),
                    variables=["recipient_name", "product_name", "company_name", "your_name", "phone"],
                    description="首次联系潜在客户的英文邮件模板"
                ),
                Template(
                    id="quotation",
                    name="产品报价单",
                    category="foreign_trade",
                    content=self._get_quotation_template(),
                    variables=["customer_name", "product_name", "quantity", "unit_price", "port"],
                    description="正式报价单模板"
                ),
            ],
            "contract": [
                Template(
                    id="purchase_contract",
                    name="采购合同",
                    category="contract",
                    content=self._get_contract_template(),
                    variables=["buyer", "seller", "product", "quantity", "price", "payment"],
                    description="标准采购合同框架"
                ),
            ],
            "sop": [
                Template(
                    id="maintenance_sop",
                    name="设备维护SOP",
                    category="sop",
                    content=self._get_sop_template(),
                    variables=["equipment_name", "department", "frequency"],
                    description="标准操作流程模板"
                ),
            ],
            "scifi": [
                Template(
                    id="faction_profile",
                    name="星际势力设定",
                    category="scifi",
                    content=self._get_faction_template(),
                    variables=["faction_name", "origin", "capital", "government", "technology"],
                    description="科幻小说星际势力背景设定"
                ),
            ]
        }
    
    def _get_cold_email_template(self) -> str:
        return """Subject: {product_name} Supplier from China - {company_name}

Dear {recipient_name},

I hope this email finds you well.

This is {your_name} from {company_name}, a professional manufacturer of {product_name} in China.

**Our Advantages:**
- Competitive pricing
- Quality assurance
- Fast delivery
- Excellent after-sales service

I've attached our product catalog for your reference. Could you let me know which items you're interested in?

Looking forward to hearing from you.

Best regards,
{your_name}
{company_name}
Phone: {phone}"""
    
    def _get_quotation_template(self) -> str:
        return """**QUOTATION**

Date: {date}
Quote No.: {quote_number}

To: {customer_name}

| Item | Description | Quantity | Unit Price | Total |
|------|-------------|----------|------------|-------|
| 1    | {product_name} | {quantity} | USD {unit_price} | USD {total} |

- **FOB Port**: {port}
- **Payment Terms**: T/T 30% deposit, 70% against B/L copy
- **Lead Time**: {lead_time} weeks
- **Validity**: 30 days

Please feel free to contact us if you have any questions.

Best regards,
{company_name}"""
    
    def _get_contract_template(self) -> str:
        return """# PURCHASE CONTRACT

**Contract No.**: {contract_number}
**Date**: {date}

## Parties

**Buyer**: {buyer}
**Seller**: {seller}

## Product Details

| Item | Description | Quantity | Unit Price | Amount |
|------|-------------|----------|------------|--------|
| 1    | {product} | {quantity} | USD {price} | USD {total} |

## Terms and Conditions

### 1. Payment
{payment_terms}

### 2. Delivery
- Port of Loading: {loading_port}
- Port of Destination: {destination_port}
- Lead Time: {lead_time}

### 3. Quality
Quality shall conform to sample approved by Buyer.

### 4. Inspection
Buyer has the right to inspect goods before shipment.

### 5. Claims
Any claims must be submitted within 30 days after arrival.

### 6. Force Majeure
Neither party shall be liable for delays caused by force majeure.

## Signatures

Buyer: _________________ Date: _______

Seller: _________________ Date: _______"""
    
    def _get_sop_template(self) -> str:
        return """# {equipment_name} 维护标准操作程序

**文件编号**: SOP-{code}
**版本号**: V1.0
**生效日期**: {date}

---

## 1. 目的
确保{equipment_name}处于良好运行状态，预防故障发生。

## 2. 适用范围
{department}

## 3. 维护周期
- 日常维护: {frequency_daily}
- 周维护: {frequency_weekly}
- 月度维护: {frequency_monthly}

## 4. 操作步骤

### 4.1 日常维护
1. 设备停机并断电
2. 清理设备表面灰尘
3. 检查润滑点
4. 检查紧固件
5. 试运行确认正常

### 4.2 周维护
1. 执行日常维护
2. 检查液压系统
3. 清洁过滤器
4. 记录运行参数

## 5. 安全注意事项
- 维护前必须断电挂牌
- 使用合适的防护用品
- 禁止带病运行

## 6. 记录表单
- 维护记录表
- 异常处理记录"""
    
    def _get_faction_template(self) -> str:
        return """# {faction_name} - 星际势力设定

## 基本信息
- **成立时间**: {origin_date}
- **总部位置**: {capital}
- **政体类型**: {government}
- **核心科技**: {technology}

## 势力概述
{faction_description}

## 组织结构
### 最高决策层
{leadership_structure}

### 行政体系
{administrative_structure}

### 军事力量
{military_force}

## 意识形态
{ideology}

## 关键人物
### 领袖
- **姓名**: {leader_name}
- **背景**: {leader_background}
- **执政理念**: {leader_philosophy}

### 核心成员
- {core_member_1}
- {core_member_2}

## 外交关系
| 势力 | 关系 | 说明 |
|------|------|------|
| {ally_1} | 友好 | {ally_1_desc} |
| {rival_1} | 对立 | {rival_1_desc} |

## 历史事件
### 成立 {founding_year}
{founding_story}

### 关键战役
{key_battles}

## 经济体系
{economic_system}

## 文化特色
{culture}
"""
    
    def render(self, template_id: str, variables: Dict[str, Any],
               category: str = None) -> str:
        """渲染模板
        
        Args:
            template_id: 模板 ID
            variables: 变量字典
            category: 模板类别（可选）
            
        Returns:
            str: 渲染后的内容
        """
        # 查找模板
        template = None
        for cat, templates in self.templates.items():
            if category and cat != category:
                continue
            for t in templates:
                if t.id == template_id:
                    template = t
                    break
            if template:
                break
        
        if not template:
            return f"Template '{template_id}' not found"
        
        # 填充变量
        content = template.content
        
        # 处理日期相关变量
        if "{date}" in content:
            content = content.replace("{date}", datetime.now().strftime("%Y-%m-%d"))
        
        # 替换所有变量
        for key, value in variables.items():
            placeholder = "{" + key + "}"
            content = content.replace(placeholder, str(value))
        
        # 标记未填充的变量
        unfilled = re.findall(r'\{(\w+)\}', content)
        if unfilled:
            content += f"\n\n<!-- 未填充变量: {', '.join(unfilled)} -->"
        
        return content
    
    def list_templates(self, category: str = None) -> List[Dict]:
        """列出可用模板"""
        result = []
        for cat, templates in self.templates.items():
            if category and cat != category:
                continue
            for t in templates:
                result.append({
                    "id": t.id,
                    "name": t.name,
                    "category": cat,
                    "description": t.description,
                    "variables": t.variables
                })
        return result
    
    def add_custom_template(self, template: Template) -> Dict:
        """添加自定义模板"""
        category = template.category
        if category not in self.templates:
            self.templates[category] = []
        
        # 检查是否已存在
        for t in self.templates[category]:
            if t.id == template.id:
                return {"status": "error", "message": f"Template '{template.id}' already exists"}
        
        self.templates[category].append(template)
        return {"status": "success", "message": f"Added template '{template.id}'"}
    
    def get_template(self, template_id: str, category: str = None) -> Optional[Template]:
        """获取模板详情"""
        for cat, templates in self.templates.items():
            if category and cat != category:
                continue
            for t in templates:
                if t.id == template_id:
                    return t
        return None


def main(action: str = "list", **kwargs) -> Dict:
    """主入口函数"""
    generator = TemplateGenerator()
    
    if action == "list":
        category = kwargs.get("category")
        templates = generator.list_templates(category)
        return {
            "status": "success",
            "templates": templates
        }
    
    elif action == "render":
        template_id = kwargs.get("template_id")
        variables = kwargs.get("variables", {})
        category = kwargs.get("category")
        
        if not template_id:
            return {"status": "error", "message": "template_id is required"}
        
        rendered = generator.render(template_id, variables, category)
        return {
            "status": "success",
            "content": rendered
        }
    
    elif action == "get":
        template_id = kwargs.get("template_id")
        category = kwargs.get("category")
        
        if not template_id:
            return {"status": "error", "message": "template_id is required"}
        
        template = generator.get_template(template_id, category)
        if template:
            return {
                "status": "success",
                "template": {
                    "id": template.id,
                    "name": template.name,
                    "category": template.category,
                    "description": template.description,
                    "variables": template.variables,
                    "preview": template.content[:500] + "..."
                }
            }
        else:
            return {"status": "error", "message": f"Template '{template_id}' not found"}
    
    else:
        return {"status": "error", "message": f"Unknown action: {action}"}


if __name__ == "__main__":
    # 测试代码
    # 列出所有模板
    print("=== 可用模板列表 ===")
    result = main("list")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 渲染开发信模板
    print("\n=== 渲染外贸开发信 ===")
    result = main("render", 
                  template_id="cold_email",
                  variables={
                      "recipient_name": "John Smith",
                      "product_name": "Electronic Components",
                      "company_name": "Tech Components Ltd",
                      "your_name": "Li Ming",
                      "phone": "+86 138 0000 0000"
                  })
    print(json.dumps(result, ensure_ascii=False, indent=2))
