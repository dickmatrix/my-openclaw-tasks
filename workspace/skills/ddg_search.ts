import { Tool, ToolSchema, ToolExecutor } from '@openclaw/sdk';

/**
 * DuckDuckGo 免费搜索 Skill
 * 完全免费，无需 API Key
 * 作为 web_search 失败时的 Fallback
 */

export const ddgSearchSchema: ToolSchema = {
  name: 'ddg_search',
  description: 'Free DuckDuckGo search without API key - Fallback for web_search',
  category: 'search',
  parameters: {
    type: 'object',
    properties: {
      query: {
        type: 'string',
        description: 'Search query keywords'
      },
      topK: {
        type: 'number',
        description: 'Number of results to return',
        default: 10,
        minimum: 1,
        maximum: 50
      },
      region: {
        type: 'string',
        description: 'Region code (cn-zh for Chinese, en-us for English, etc)',
        default: 'cn-zh',
        enum: ['cn-zh', 'en-us', 'en-gb', 'de-de', 'fr-fr', 'ja-jp']
      },
      safeSearch: {
        type: 'boolean',
        description: 'Enable safe search',
        default: true
      }
    },
    required: ['query']
  }
};

interface SearchResult {
  title: string;
  url: string;
  snippet: string;
  source: string;
  confidence: number;
}

interface DDGSearchParams {
  query: string;
  topK?: number;
  region?: string;
  safeSearch?: boolean;
}

interface DDGSearchResponse {
  status: 'success' | 'error';
  provider: string;
  query: string;
  count?: number;
  results?: SearchResult[];
  message?: string;
  solution?: string;
}

/**
 * 执行 DuckDuckGo 搜索
 */
export const ddgSearch: ToolExecutor = async (
  params: DDGSearchParams
): Promise<DDGSearchResponse> => {
  const { query, topK = 10, region = 'cn-zh', safeSearch = true } = params;

  // 参数验证
  if (!query || query.trim().length < 2) {
    return {
      status: 'error',
      provider: 'DuckDuckGo',
      query,
      message: 'Query must be at least 2 characters'
    };
  }

  if (query.length > 500) {
    return {
      status: 'error',
      provider: 'DuckDuckGo',
      query,
      message: 'Query must be less than 500 characters'
    };
  }

  try {
    // 调用 Python Skill 或直接实现
    // 这里通过 HTTP 调用本地 Python skill
    const response = await fetch('http://localhost:18789/api/skills/ddg_search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.OPENCLAW_API_TOKEN || ''}`
      },
      body: JSON.stringify({
        query,
        top_k: topK,
        region,
        safe_search: safeSearch
      }),
      timeout: 30000
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();

    return {
      status: 'success',
      provider: 'DuckDuckGo (Free)',
      query,
      count: data.count || 0,
      results: (data.results || []).map((r: any) => ({
        title: r.title,
        url: r.url,
        snippet: r.snippet,
        source: r.source || 'DuckDuckGo',
        confidence: parseFloat(r.confidence) / 100 || 0.95
      }))
    };
  } catch (error) {
    console.error('DuckDuckGo search error:', error);

    return {
      status: 'error',
      provider: 'DuckDuckGo',
      query,
      message: `DuckDuckGo search failed: ${error instanceof Error ? error.message : String(error)}`,
      solution: 'Ensure duckduckgo-search is installed: pip install duckduckgo-search'
    };
  }
};

/**
 * 批量搜索
 */
export const ddgBatchSearch: ToolExecutor = async (
  params: {
    queries: string[];
    topK?: number;
    region?: string;
  }
): Promise<{
  status: 'success' | 'error';
  provider: string;
  total: number;
  results: Record<string, DDGSearchResponse>;
}> => {
  const { queries, topK = 10, region = 'cn-zh' } = params;

  const results: Record<string, DDGSearchResponse> = {};

  for (const query of queries) {
    results[query] = await ddgSearch({ query, topK, region });
  }

  return {
    status: 'success',
    provider: 'DuckDuckGo (Free)',
    total: queries.length,
    results
  };
};

/**
 * Tool 导出
 */
export default {
  schema: ddgSearchSchema,
  execute: ddgSearch,
  batch: ddgBatchSearch,
  fallback: true, // 标记为 web_search 的 fallback
  priority: 'low' // 低优先级，仅在主搜索失败时使用
} as Tool;
