/**
 * Skillix Hub - socratic Skill Data
 */
window.SKILL_DATA_SOCRATIC = {
    id: 'socratic',
    name: 'socratic',
    icon: 'lightbulb',
    description: {
        zh: '苏格拉底式批判性思维分析。自动识别需求分析、系统设计、技术选型、数据分析四类场景，智能决定快速结论或深度探索，防止过度追问与草率结论',
        en: 'Socratic critical thinking analysis. Auto-detects requirements, design review, tech research, and data analysis scenarios, intelligently choosing fast-track or deep exploration to prevent over-questioning and hasty conclusions'
    },
    tags: [
        { zh: '批判性思维', en: 'Critical Thinking' },
        { zh: '需求分析', en: 'Requirements Analysis' },
        { zh: '设计评审', en: 'Design Review' },
        { zh: '技术选型', en: 'Tech Research' }
    ],
    features: [
        { zh: '自动识别 4 类场景：需求分析、系统设计、技术选型、数据分析', en: 'Auto-detect 4 scenario types: requirements, design, tech research, data analysis' },
        { zh: '3 种路径：快速结论（≤1问）、评审模式、深度探索（≤5问）', en: '3 paths: Fast Track (≤1 question), Review Mode, Deep Exploration (≤5 questions)' },
        { zh: '4 维度提问框架：定义问题、挑战假设、扩展视角、压力测试', en: '4-dimension questioning: Define, Challenge, Expand, Stress-test' },
        { zh: '5 种领域专属输出模板 + 置信度标注', en: '5 domain-specific output templates + confidence annotation' },
        { zh: '元问题触发机制：识别矛盾答案、沉没成本偏见等信号', en: 'Meta-question trigger: detect contradictory answers, sunk-cost bias signals' }
    ],
    scripts: ['SKILL.md'],
    version: '3.4.0',
    author: 'shetengteng',
    repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/socratic',
    useCases: [
        {
            title: { zh: '技术选型分析', en: 'Tech Selection Analysis' },
            userInput: { zh: '我们想用 Redis 做消息队列，你觉得怎么样？', en: 'We want to use Redis as a message queue, what do you think?' },
            aiResponse: { zh: '识别为 🔬 Research 场景 → 追问核心决策问题、消息可靠性要求、吞吐量预期 → 输出 Research Framework（候选方案对比 + 风险评估 + 推荐下一步）', en: 'Detected as 🔬 Research → asks about core decision, reliability requirements, throughput expectations → outputs Research Framework (candidate comparison + risk assessment + next steps)' }
        },
        {
            title: { zh: '需求评审', en: 'Requirements Review' },
            userInput: { zh: '我们要做一个用户积分系统，用户消费可以获得积分，积分可以兑换优惠券', en: 'We want to build a user points system where users earn points from purchases and redeem coupons' },
            aiResponse: { zh: '识别为 📋 Requirements → 追问目标用户、积分过期策略、反作弊机制 → 输出 Requirements Summary（真实问题、验收标准、待验证假设）', en: 'Detected as 📋 Requirements → asks about target users, points expiry policy, anti-fraud mechanism → outputs Requirements Summary (real problem, acceptance criteria, assumptions to verify)' }
        },
        {
            title: { zh: '设计方案评审', en: 'Design Proposal Review' },
            userInput: { zh: '这是我的微服务拆分方案文档，帮我评审一下 [附文档]', en: 'Here is my microservice decomposition proposal, please review it [document attached]' },
            aiResponse: { zh: '进入 Review Mode → 跳过提问阶段 → 从 4 个维度（问题定义、假设挑战、视角盲点、风险压测）评审 → 输出 Review Output（Top 3 改进项 + 推荐下一步）', en: 'Enters Review Mode → skips questioning → reviews across 4 dimensions (problem definition, assumption challenge, perspective blind spots, risk stress-test) → outputs Review Output (Top 3 improvements + next steps)' }
        }
    ]
};
