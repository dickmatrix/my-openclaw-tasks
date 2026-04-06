#!/usr/bin/env python3
"""
FileStitcher 长文本拼接工具 - 多源内容整合与上下文连贯性维护
"""
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import re
import json


class StitchStrategy(Enum):
    """拼接策略"""
    SEQUENTIAL = "sequential"  # 顺序拼接
    SEMANTIC = "semantic"      # 语义聚合
    HYBRID = "hybrid"          # 混合策略


@dataclass
class ContentChunk:
    """内容块"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


@dataclass
class StitchResult:
    """拼接结果"""
    content: str
    sources: List[str]
    word_count: int
    sections: List[Dict]


class FileStitcher:
    """长文本拼接器"""
    
    def __init__(self):
        self.name = "file_stitcher"
        self.description = "长文本分段拼接、上下文连贯性维护、多源内容整合"
        self.max_chunk_size = 2000  # 最大块大小（token）
        self.overlap_size = 100     # 重叠大小
    
    def split_by_length(self, text: str, max_length: int = None) -> List[str]:
        """按长度分割文本
        
        Args:
            text: 输入文本
            max_length: 最大长度（字符）
            
        Returns:
            List[str]: 文本块列表
        """
        max_len = max_length or self.max_chunk_size
        chunks = []
        
        # 按段落分割
        paragraphs = text.split("\n\n")
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= max_len:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # 如果单个段落超过最大长度，按句子分割
                if len(para) > max_len:
                    sentences = re.split(r'(?<=[。！？.!?])', para)
                    current_chunk = ""
                    for sent in sentences:
                        if len(current_chunk) + len(sent) <= max_len:
                            current_chunk += sent
                        else:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = sent
                else:
                    current_chunk = para + "\n\n"
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def split_by_sentence(self, text: str) -> List[str]:
        """按句子分割（保留完整性）"""
        # 中英文句子边界识别
        pattern = r'(?<=[。！？.!?\n])\s*'
        sentences = re.split(pattern, text)
        return [s.strip() for s in sentences if s.strip()]
    
    def merge_chunks(self, chunks: List[ContentChunk], 
                     strategy: StitchStrategy = StitchStrategy.SEQUENTIAL) -> str:
        """合并内容块
        
        Args:
            chunks: 内容块列表
            strategy: 拼接策略
            
        Returns:
            str: 合并后的文本
        """
        if strategy == StitchStrategy.SEQUENTIAL:
            return self._merge_sequential(chunks)
        elif strategy == StitchStrategy.SEMANTIC:
            return self._merge_semantic(chunks)
        elif strategy == StitchStrategy.HYBRID:
            return self._merge_hybrid(chunks)
        else:
            return self._merge_sequential(chunks)
    
    def _merge_sequential(self, chunks: List[ContentChunk]) -> str:
        """顺序拼接"""
        result = []
        for i, chunk in enumerate(chunks):
            if i > 0:
                result.append("\n\n---\n\n")  # 分隔符
            result.append(chunk.content)
        return "".join(result)
    
    def _merge_semantic(self, chunks: List[ContentChunk]) -> str:
        """语义聚合（需要 embedding 支持）"""
        # TODO: 实现语义聚类
        # 1. 计算每个 chunk 的 embedding
        # 2. 使用 K-means 或层次聚类
        # 3. 按主题排序后拼接
        return self._merge_sequential(chunks)
    
    def _merge_hybrid(self, chunks: List[ContentChunk]) -> str:
        """混合策略：先按主题分组，再顺序拼接"""
        # TODO: 实现混合策略
        return self._merge_sequential(chunks)
    
    def add_transitions(self, chunks: List[str]) -> List[str]:
        """添加过渡句，保持上下文连贯"""
        if len(chunks) <= 1:
            return chunks
        
        transitions = [
            "继续上述讨论，",
            "基于上述内容，",
            "此外，",
            "值得注意的是，",
            "综上所述，",
            "进一步分析表明，",
        ]
        
        result = [chunks[0]]  # 保留第一块
        for i, chunk in enumerate(chunks[1:], 1):
            # 选择一个过渡句（简单循环选择）
            transition = transitions[i % len(transitions)]
            result.append(f"{transition}{chunk}")
        
        return result
    
    def detect_repetition(self, text: str, threshold: float = 0.8) -> List[Dict]:
        """检测重复内容"""
        chunks = self.split_by_length(text, max_length=500)
        repetitions = []
        
        for i, chunk_a in enumerate(chunks):
            for j, chunk_b in enumerate(chunks[i+1:], i+1):
                similarity = self._calculate_similarity(chunk_a, chunk_b)
                if similarity > threshold:
                    repetitions.append({
                        "chunk_a": i,
                        "chunk_b": j,
                        "similarity": similarity
                    })
        
        return repetitions
    
    def _calculate_similarity(self, text_a: str, text_b: str) -> float:
        """简单文本相似度计算"""
        # TODO: 使用更高级的相似度算法（如 Jaccard, Cosine）
        set_a = set(text_a.split())
        set_b = set(text_b.split())
        
        if not set_a or not set_b:
            return 0.0
        
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        
        return intersection / union if union > 0 else 0.0
    
    def stitch(self, sources: List[str], add_transitions: bool = True,
               strategy: StitchStrategy = StitchStrategy.SEQUENTIAL,
               format_output: str = "markdown") -> StitchResult:
        """主拼接方法
        
        Args:
            sources: 源文本列表
            add_transitions: 是否添加过渡句
            strategy: 拼接策略
            format_output: 输出格式 (markdown/html/plain)
            
        Returns:
            StitchResult: 拼接结果
        """
        # 构建内容块
        chunks = []
        for i, source in enumerate(sources):
            chunk = ContentChunk(
                id=f"chunk_{i}",
                content=source,
                metadata={"source_index": i, "length": len(source)}
            )
            chunks.append(chunk)
        
        # 合并
        merged = self.merge_chunks(chunks, strategy)
        
        # 添加过渡
        if add_transitions:
            text_chunks = [c.content for c in chunks]
            transitioned = self.add_transitions(text_chunks)
            merged = "\n\n---\n\n".join(transitioned)
        
        # 格式化
        if format_output == "markdown":
            final_content = f"# 整合文档\n\n{merged}"
        elif format_output == "html":
            final_content = f"<article>\n{merged}\n</article>"
        else:
            final_content = merged
        
        return StitchResult(
            content=final_content,
            sources=[f"Source {i+1}" for i in range(len(sources))],
            word_count=len(final_content),
            sections=[{"index": i, "preview": c[:100]} for i, c in enumerate([s.content for s in chunks])]
        )


def main(sources: List[str] = None, action: str = "stitch", **kwargs) -> Dict:
    """主入口函数"""
    stitcher = FileStitcher()
    
    if action == "stitch":
        if not sources:
            sources = kwargs.get("source_list", [])
        
        if not sources:
            return {"status": "error", "message": "No sources provided"}
        
        result = stitcher.stitch(
            sources=sources,
            add_transitions=kwargs.get("add_transitions", True),
            strategy=StitchStrategy(kwargs.get("strategy", "sequential")),
            format_output=kwargs.get("format", "markdown")
        )
        
        return {
            "status": "success",
            "content": result.content,
            "word_count": result.word_count,
            "source_count": len(result.sources),
            "sections": result.sections
        }
    
    elif action == "split":
        text = kwargs.get("text", "")
        if not text:
            return {"status": "error", "message": "No text provided"}
        
        chunks = stitcher.split_by_length(text, kwargs.get("max_length"))
        
        return {
            "status": "success",
            "chunks": chunks,
            "chunk_count": len(chunks)
        }
    
    elif action == "check_repetition":
        text = kwargs.get("text", "")
        if not text:
            return {"status": "error", "message": "No text provided"}
        
        repetitions = stitcher.detect_repetition(text)
        
        return {
            "status": "success",
            "has_repetition": len(repetitions) > 0,
            "repetitions": repetitions
        }
    
    else:
        return {"status": "error", "message": f"Unknown action: {action}"}


if __name__ == "__main__":
    # 测试代码
    test_sources = [
        "这是第一部分内容，介绍了基本概念。",
        "第二部分详细说明了技术细节和实现方法。",
        "第三部分讨论了应用场景和最佳实践。"
    ]
    
    result = main(sources=test_sources)
    print(json.dumps(result, ensure_ascii=False, indent=2))
