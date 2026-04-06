#!/usr/bin/env python3
"""
OpenClaw 免费搜索方案测试脚本
"""
import sys
import json
import os

# 添加 skills 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'skills'))

def test_duckduckgo():
    """测试 DuckDuckGo 搜索"""
    print("\n" + "="*60)
    print("测试 1: DuckDuckGo 搜索（完全免费）")
    print("="*60)
    
    try:
        from duckduckgo_free_search import search_free
        
        result = search_free("白银价格 2024", top_k=5)
        
        if result["status"] == "success":
            print(f"✅ 搜索成功！找到 {result['count']} 个结果")
            print(f"提供商: {result['provider']}")
            print("\n前 3 个结果:")
            for i, r in enumerate(result['results'][:3], 1):
                print(f"\n{i}. {r['title']}")
                print(f"   URL: {r['url']}")
                print(f"   置信度: {r['confidence']}")
        else:
            print(f"❌ 搜索失败: {result['message']}")
            if 'solution' in result:
                print(f"   解决方案: {result['solution']}")
    
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        print("   解决方案: pip install duckduckgo-search")


def test_gemini():
    """测试 Gemini Grounding 搜索"""
    print("\n" + "="*60)
    print("测试 2: Google Gemini Grounding 搜索（1000/天免费）")
    print("="*60)
    
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("⚠️  GEMINI_API_KEY 未设置，跳过此测试")
        print("   获取方式: https://ai.google.dev")
        print("   配置: export GEMINI_API_KEY='your-key'")
        return
    
    try:
        from gemini_grounding_search import search_gemini
        
        result = search_gemini("白银价格 2024", api_key=api_key, top_k=5)
        
        if result["status"] == "success":
            print(f"✅ 搜索成功！找到 {result['count']} 个结果")
            print(f"提供商: {result['provider']}")
            print("\n前 3 个结果:")
            for i, r in enumerate(result['results'][:3], 1):
                print(f"\n{i}. {r['title']}")
                print(f"   URL: {r['url']}")
                print(f"   置信度: {r['confidence']}")
        else:
            print(f"❌ 搜索失败: {result['message']}")
            if 'solution' in result:
                print(f"   解决方案: {result['solution']}")
    
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        print("   解决方案: pip install google-generativeai")


def test_router():
    """测试自动路由器"""
    print("\n" + "="*60)
    print("测试 3: 自动路由器（自动降级）")
    print("="*60)
    
    try:
        from search_router import search
        
        result = search("白银价格 2024", provider="auto", top_k=5)
        
        if result["status"] == "success":
            print(f"✅ 搜索成功！找到 {result['count']} 个结果")
            print(f"提供商: {result['provider']}")
            print("\n前 3 个结果:")
            for i, r in enumerate(result['results'][:3], 1):
                print(f"\n{i}. {r['title']}")
                print(f"   URL: {r['url']}")
                print(f"   置信度: {r['confidence']}")
        else:
            print(f"❌ 搜索失败: {result['message']}")
    
    except Exception as e:
        print(f"❌ 测试异常: {e}")


def test_batch_search():
    """测试批量搜索"""
    print("\n" + "="*60)
    print("测试 4: 批量搜索")
    print("="*60)
    
    try:
        from search_router import batch_search
        
        queries = ["白银价格", "黄金走势", "铜价行情"]
        result = batch_search(queries, provider="auto", top_k=3)
        
        if result["status"] == "success":
            print(f"✅ 批量搜索成功！处理 {result['total_queries']} 个查询")
            print(f"提供商: {result['provider']}")
            
            for query, query_result in result['results'].items():
                if query_result['status'] == 'success':
                    print(f"\n✓ '{query}': 找到 {query_result['count']} 个结果")
                else:
                    print(f"\n✗ '{query}': {query_result['message']}")
        else:
            print(f"❌ 批量搜索失败: {result['message']}")
    
    except Exception as e:
        print(f"❌ 测试异常: {e}")


def main():
    print("\n" + "🔍 OpenClaw 免费搜索方案测试")
    print("="*60)
    
    # 检查依赖
    print("\n检查依赖...")
    
    try:
        import duckduckgo_search
        print("✅ duckduckgo-search 已安装")
    except ImportError:
        print("❌ duckduckgo-search 未安装")
        print("   安装: pip install duckduckgo-search")
    
    try:
        import google.generativeai
        print("✅ google-generativeai 已安装")
    except ImportError:
        print("⚠️  google-generativeai 未安装（可选）")
        print("   安装: pip install google-generativeai")
    
    # 运行测试
    test_duckduckgo()
    test_gemini()
    test_router()
    test_batch_search()
    
    print("\n" + "="*60)
    print("✅ 测试完成！")
    print("="*60)
    print("\n📚 更多信息请查看: FREE_SEARCH_GUIDE.md")


if __name__ == "__main__":
    main()
