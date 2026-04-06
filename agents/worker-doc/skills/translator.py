#!/usr/bin/env python3
"""
Translator 翻译工具 - 多语言互译、术语映射、文化本地化
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json


class Language(Enum):
    """支持的语言"""
    CHINESE = "zh"
    ENGLISH = "en"
    JAPANESE = "ja"
    KOREAN = "ko"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    ARABIC = "ar"


@dataclass
class TranslationResult:
    """翻译结果"""
    source_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    confidence: float
    alternatives: List[str] = None


@dataclass
class TermMapping:
    """术语映射"""
    source_term: str
    target_term: str
    context: str
    source: str


class Translator:
    """多语言翻译工具"""
    
    def __init__(self):
        self.name = "translator"
        self.description = "多语言互译、专业术语映射、文化本地化适配"
        self.supported_languages = [lang.value for lang in Language]
        self.term_library = self._load_term_library()
        self.translation_cache = {}
    
    def _load_term_library(self) -> Dict[str, List[TermMapping]]:
        """加载术语库"""
        # TODO: 从文件或数据库加载专业术语库
        # 示例结构：
        return {
            "en_zh": [
                TermMapping("machine learning", "机器学习", "技术文档", "Industry Standard"),
                TermMapping("artificial intelligence", "人工智能", "技术文档", "Industry Standard"),
            ],
            "zh_en": [
                TermMapping("机器学习", "machine learning", "技术文档", "Industry Standard"),
                TermMapping("人工智能", "artificial intelligence", "技术文档", "Industry Standard"),
            ]
        }
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """检测语言
        
        Returns:
            (language_code, confidence)
        """
        # TODO: 实现语言检测
        # 可使用 langdetect 或 google.trans api
        
        # 简单实现：基于字符集判断
        if re.search(r'[\u4e00-\u9fff]', text):
            return "zh", 0.95
        elif re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text):
            return "ja", 0.9
        elif re.search(r'[\uac00-\ud7af]', text):
            return "ko", 0.9
        else:
            return "en", 0.8
    
    def translate(self, text: str, target_lang: str,
                 source_lang: str = None,
                 use_terms: bool = True,
                 preserve_format: bool = True) -> TranslationResult:
        """翻译文本
        
        Args:
            text: 源文本
            target_lang: 目标语言代码
            source_lang: 源语言代码（自动检测为 None）
            use_terms: 是否使用术语库
            preserve_format: 是否保留原文格式
            
        Returns:
            TranslationResult: 翻译结果
        """
        # 检测源语言
        if not source_lang:
            source_lang, _ = self.detect_language(text)
        
        # 检查缓存
        cache_key = f"{source_lang}:{target_lang}:{hash(text)}"
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]
        
        # 应用术语映射
        processed_text = text
        if use_terms and f"{source_lang}_{target_lang}" in self.term_library:
            for term in self.term_library[f"{source_lang}_{target_lang}"]:
                processed_text = processed_text.replace(
                    term.source_term, 
                    f"[[{term.target_term}]]"  # 标记已翻译术语
                )
        
        # TODO: 调用翻译 API
        # 可使用 Google Translate, DeepL, 有道翻译等
        translated_text = processed_text  # 占位
        
        result = TranslationResult(
            source_text=text,
            translated_text=translated_text,
            source_lang=source_lang,
            target_lang=target_lang,
            confidence=0.85,  # 占位
            alternatives=[]
        )
        
        # 缓存结果
        self.translation_cache[cache_key] = result
        
        return result
    
    def batch_translate(self, texts: List[str], target_lang: str,
                        source_lang: str = None) -> List[TranslationResult]:
        """批量翻译"""
        return [
            self.translate(text, target_lang, source_lang)
            for text in texts
        ]
    
    def translate_document(self, document: str, target_lang: str,
                          source_lang: str = None,
                          preserve_structure: bool = True) -> str:
        """翻译完整文档
        
        Args:
            document: 文档内容
            target_lang: 目标语言
            source_lang: 源语言
            preserve_structure: 保留文档结构（标题、列表等）
        """
        import re
        
        if not preserve_structure:
            return self.translate(document, target_lang, source_lang).translated_text
        
        # 分割段落
        paragraphs = document.split("\n\n")
        translated_paragraphs = []
        
        for para in paragraphs:
            if not para.strip():
                translated_paragraphs.append("")
                continue
            
            # 检测是否为标题（简单规则）
            is_header = para.startswith("#") or (
                len(para) < 100 and 
                not para.endswith(("。", "！", "？", ".", "!", "?"))
            )
            
            if is_header:
                # 标题直接翻译
                result = self.translate(para, target_lang, source_lang)
                translated_paragraphs.append(result.translated_text)
            else:
                # 正文翻译
                result = self.translate(para, target_lang, source_lang)
                translated_paragraphs.append(result.translated_text)
        
        return "\n\n".join(translated_paragraphs)
    
    def localize(self, text: str, target_culture: str,
                 context: str = "general") -> str:
        """文化本地化
        
        Args:
            text: 原文
            target_culture: 目标文化 (如 'en_US', 'zh_CN', 'ja_JP')
            context: 使用场景
        """
        # TODO: 实现文化本地化逻辑
        # 1. 日期/时间格式
        # 2. 货币/数字格式
        # 3. 习语/俚语转换
        # 4. 色彩/图像文化适配
        
        localized = text
        
        # 日期格式转换
        date_pattern = r'\d{4}-\d{2}-\d{2}'
        dates = re.findall(date_pattern, localized)
        for date in dates:
            if target_culture == "en_US":
                # 2024-03-21 -> 03/21/2024
                parts = date.split("-")
                localized = localized.replace(date, f"{parts[1]}/{parts[2]}/{parts[0]}")
        
        return localized
    
    def add_term(self, source_term: str, target_term: str,
                 source_lang: str, target_lang: str,
                 context: str = "general", source: str = "User") -> Dict:
        """添加自定义术语"""
        key = f"{source_lang}_{target_lang}"
        
        if key not in self.term_library:
            self.term_library[key] = []
        
        self.term_library[key].append(TermMapping(
            source_term=source_term,
            target_term=target_term,
            context=context,
            source=source
        ))
        
        return {
            "status": "success",
            "message": f"Added term mapping: {source_term} -> {target_term}"
        }
    
    def clear_cache(self) -> Dict:
        """清除翻译缓存"""
        count = len(self.translation_cache)
        self.translation_cache.clear()
        return {
            "status": "success",
            "cleared_items": count
        }


# 导入 re 用于语言检测
import re


def main(text: str = None, action: str = "translate", **kwargs) -> Dict:
    """主入口函数"""
    translator = Translator()
    
    if action == "translate":
        if not text:
            text = kwargs.get("text", "")
        
        if not text:
            return {"status": "error", "message": "No text provided"}
        
        result = translator.translate(
            text=text,
            target_lang=kwargs.get("target_lang", "en"),
            source_lang=kwargs.get("source_lang"),
            use_terms=kwargs.get("use_terms", True),
            preserve_format=kwargs.get("preserve_format", True)
        )
        
        return {
            "status": "success",
            "source_text": result.source_text,
            "translated_text": result.translated_text,
            "source_lang": result.source_lang,
            "target_lang": result.target_lang,
            "confidence": f"{result.confidence * 100:.1f}%"
        }
    
    elif action == "batch":
        texts = kwargs.get("texts", [])
        if not texts:
            return {"status": "error", "message": "No texts provided"}
        
        results = translator.batch_translate(
            texts=texts,
            target_lang=kwargs.get("target_lang", "en"),
            source_lang=kwargs.get("source_lang")
        )
        
        return {
            "status": "success",
            "translations": [
                {
                    "source": r.source_text,
                    "translated": r.translated_text,
                    "confidence": r.confidence
                }
                for r in results
            ]
        }
    
    elif action == "document":
        document = kwargs.get("document", "")
        if not document:
            return {"status": "error", "message": "No document provided"}
        
        translated = translator.translate_document(
            document=document,
            target_lang=kwargs.get("target_lang", "en"),
            source_lang=kwargs.get("source_lang"),
            preserve_structure=kwargs.get("preserve_structure", True)
        )
        
        return {
            "status": "success",
            "document": translated
        }
    
    elif action == "localize":
        text = kwargs.get("text", "")
        if not text:
            return {"status": "error", "message": "No text provided"}
        
        localized = translator.localize(
            text=text,
            target_culture=kwargs.get("target_culture", "en_US"),
            context=kwargs.get("context", "general")
        )
        
        return {
            "status": "success",
            "original": text,
            "localized": localized
        }
    
    elif action == "add_term":
        result = translator.add_term(
            source_term=kwargs.get("source_term"),
            target_term=kwargs.get("target_term"),
            source_lang=kwargs.get("source_lang"),
            target_lang=kwargs.get("target_lang"),
            context=kwargs.get("context", "general")
        )
        return result
    
    elif action == "detect":
        if not text:
            text = kwargs.get("text", "")
        
        if not text:
            return {"status": "error", "message": "No text provided"}
        
        lang, confidence = translator.detect_language(text)
        return {
            "status": "success",
            "language": lang,
            "confidence": f"{confidence * 100:.1f}%"
        }
    
    else:
        return {"status": "error", "message": f"Unknown action: {action}"}


if __name__ == "__main__":
    # 测试代码
    test_text = "机器学习是人工智能的一个重要分支。"
    result = main(text=test_text, target_lang="en")
    print(json.dumps(result, ensure_ascii=False, indent=2))
