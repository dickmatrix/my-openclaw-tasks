#!/usr/bin/env node
/**
 * 群消息路由核心
 * 根据关键字将消息转发给对应 agent，结果由各 bot 直接回群
 */

const ROUTING_RULES = {
  scout: {
    keywords: ['搜索', '查找', '定位', '在哪', '找', '文件', '函数', '类', '方法', '变量', '模块', '路径', 'import', 'require', '调用', '引用', 'grep', 'find', 'locate', 'search', 'look up'],
    agentId: 'scout'
  },
  writer: {
    keywords: ['写', '生成', '创建', '实现', '编写', '补全', '初始化', '构造', '新建', '代码', 'function', 'class', 'interface', 'api', '接口', 'CRUD', '增删改查'],
    agentId: 'writer'
  },
  censor: {
    keywords: ['审查', '安全', '漏洞', '风险', '攻击', '注入', 'XSS', 'SQL', 'CSRF', '权限', '认证', '加密', '敏感', '泄露', '越权', '绕过', '污点', '威胁', '审计'],
    agentId: 'censor'
  },
  architect: {
    keywords: ['架构', '设计', '模式', '方案', '结构', '模块化', '分层', '微服务', '分布式', '高并发', '可扩展', '解耦', '聚合', 'SOA', 'Event-Driven'],
    agentId: 'architect'
  },
  auditor: {
    keywords: ['调试', '问题', '错误', 'bug', '异常', '崩溃', '卡死', '超时', '失败', '排查', '诊断', '定位', '原因', '修复', 'fix', 'crash', 'issue', 'error', 'warning', 'stack', 'trace'],
    agentId: 'auditor'
  }
};

/**
 * 根据消息内容匹配路由
 * @param {string} message - 用户消息
 * @returns {object} { agentId, matchedKeyword }
 */
function route(message) {
  const lowerMsg = message.toLowerCase();
  
  for (const [name, config] of Object.entries(ROUTING_RULES)) {
    for (const keyword of config.keywords) {
      if (lowerMsg.includes(keyword.toLowerCase())) {
        return { agentId: config.agentId, matchedKeyword: keyword };
      }
    }
  }
  
  return { agentId: 'director', matchedKeyword: null };
}

module.exports = { route, ROUTING_RULES };
