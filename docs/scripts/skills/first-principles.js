/**
 * Skillix Hub - first-principles Skill Data
 */
window.SKILL_DATA_FIRST_PRINCIPLES = {
    id: 'first-principles',
    name: 'first-principles',
    icon: 'lightbulb',
    description: {
        zh: '第一性原理分析。将问题拆解到不可置疑的基础事实，系统挑战每一个假设，再从地基向上重建解决方案——而非依赖惯例或类比',
        en: 'First principles analysis. Decompose problems to bedrock facts, systematically challenge every assumption, and rebuild solutions from the ground up — instead of relying on convention or analogy'
    },
    tags: [
        { zh: '第一性原理', en: 'First Principles' },
        { zh: '批判性思维', en: 'Critical Thinking' },
        { zh: '假设挑战', en: 'Assumption Challenge' },
        { zh: '架构决策', en: 'Architecture Decision' }
    ],
    features: [
        { zh: '自动复杂度路由：T1 简单直答 → T4 完整分析 + 替代方案', en: 'Auto complexity routing: T1 direct answer → T4 full analysis + alternatives' },
        { zh: '6 个领域心智模型：架构、成本、工程、产品、选型、战略', en: '6 domain mental models: architecture, cost, engineering, product, tech selection, strategy' },
        { zh: '迭代三阶段：拆解假设 → 地基检验 → 重建方案（可回溯）', en: 'Iterative 3-phase: decompose → verify bedrock → rebuild (with backtracking)' },
        { zh: '假设/挑战/判定表：✅ 地基事实 / ⚠️ 需验证 / ❌ 伪约束', en: 'Assumption/Challenge/Verdict table: ✅ bedrock / ⚠️ needs verification / ❌ false constraint' },
        { zh: '6 种领域专属输出模板 + 重建失败协议', en: '6 domain-specific output templates + rebuild failure protocol' }
    ],
    scripts: ['SKILL.md'],
    version: '1.1.0',
    author: 'shetengteng',
    repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/first-principles',
    useCases: [
        {
            title: { zh: '架构决策分析', en: 'Architecture Decision Analysis' },
            userInput: { zh: '我们打算用微服务架构重构单体应用，你觉得怎么样？', en: 'We plan to refactor our monolith into microservices, what do you think?' },
            aiResponse: { zh: '识别为 T3 架构决策 → Phase 1 拆解显式/隐式假设（团队 DevOps 能力、服务边界、数据一致性） → Phase 2 地基检验（标记"单体已成为瓶颈"为伪约束） → Phase 3 推荐 Modular Monolith 先行，验证边界后再拆分', en: 'Detected as T3 architecture → Phase 1 decompose assumptions (DevOps capability, service boundaries, data consistency) → Phase 2 bedrock test (marks "monolith is bottleneck" as false constraint) → Phase 3 recommends Modular Monolith first, then split after boundary validation' }
        },
        {
            title: { zh: '成本质疑', en: 'Cost Challenge' },
            userInput: { zh: '我们的云服务账单每月 5 万，能不能降下来？', en: 'Our cloud bill is $7K/month, can we reduce it?' },
            aiResponse: { zh: '进入成本/约束分析 → 物料分解（计算 2.1万 + 存储 1.5万 + 网络 0.8万） → 发现存储中 60% 为未清理旧备份（伪约束） → 清理 + Reserved Instance → 预计降至 3.2万/月', en: 'Cost/constraint analysis → material decomposition (compute $3K + storage $2.1K + network $1.1K) → found 60% storage is uncleaned old backups (false constraint) → cleanup + Reserved Instance → estimated $4.5K/month' }
        },
        {
            title: { zh: '根因分析', en: 'Root Cause Analysis' },
            userInput: { zh: '部署后 API 响应偶尔超时，重启就好了', en: 'API occasionally times out after deployment, restart fixes it' },
            aiResponse: { zh: '进入根因分析 → 5-Whys: 超时 → 连接池耗尽 → 慢查询占连接 → 缺失索引 + 数据增长 → 根本假设"查询性能不随数据增长退化"是伪假设 → 根因修复：添加索引 + 配置连接池超时', en: 'Root cause analysis → 5-Whys: timeout → connection pool exhausted → slow queries holding connections → missing indexes + data growth → root assumption "query performance doesn\'t degrade with data growth" is false → fix: add indexes + configure pool timeout' }
        }
    ]
};
