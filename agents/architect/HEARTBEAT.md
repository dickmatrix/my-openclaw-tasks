# HEARTBEAT.md - Quant_Analyst 定时调度

## 定时调度任务 (Cron Jobs)

### 任务1：每3小时执行一次数据迭代与模型计算
```
0 */3 * * * : 执行 fetch_and_analyze_incremental_data
```
读取过去3小时的全球经济数据、美股/港股异动、宏观事件，与30年历史知识图谱进行特征比对，更新内部状态。

### 任务2：每日早上8点生成策略报告
```
0 8 * * * : 执行 generate_daily_strategy
```
提取最近24小时的计算结果，直接向通讯通道输出美股与港股（重点覆盖科技/资源）的日内投资清单。

### 任务3：每日收盘后补充当日数据 (UTC+8 16:05)
```
5 16 * * * : 执行 daily_data_supplement
```
当日盘结束后，拉取并写入当日宏观数据更新 + 最新行情切片至 `macro_indicators` 和 `market_data`，触发特征向量生成。

### 任务4：每日不定时生成金融关注点日报
```
运行脚本: scripts/daily_report.py
```
融合行情异动分析（美股+32只港股）+ 财经新闻（财新+东方财富）+ 宏观快照，输出 Markdown 日报至 docs/daily_report_YYYYMMDD.md，同步输出 JSON 摘要至 output/daily_report_YYYYMMDD.json。

### 任务5：每周知识归纳压缩 (每周一 09:00)
```
0 9 * * 1 : 执行 macro_weekly_compress
```
扫描最近30天宏观异动因子（Z-score 显著），归纳写入 MEMORY.md 的 `macro_weekly` 分区。

### 任务6：每月模型校准 (每月1日 09:00)
```
0 9 1 * * : 执行 model_calibration
```
汇总上月 `strategy_decisions` 胜率实际 vs 预测偏差，更新概率模型参数。

## 数据源说明
- 美股: AKShare stock_us_daily (3年历史)
- 港股: Tencent Finance API (web.ifzq.gtimg.cn，替代被封的Eastmoney，3年历史)
- 宏观: AKShare (部分)

## 状态监测 (常规 Heartbeat)
- API_Check: 校验历史数据源、实时行情API的连接存活状态
- DB_Check: 校验 PostgreSQL + TimescaleDB + pgvector 连接状态
- News_Check: 校验财新/东方财富新闻API连通性

## 任务7：每日记忆维护 (Heartbeat 内)
每次 heartbeat 时：
1. 读取 memory/YYYY-MM-DD.md 检查是否有新内容
2. 若有重要进展，更新 MEMORY.md
3. 定期将每日日志中的重要内容提炼到 MEMORY.md
