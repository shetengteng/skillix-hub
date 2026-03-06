/**
 * Skillix Hub - prompt-helper Skill Data
 */
window.SKILL_DATA_PROMPT_HELPER = {
    id: 'prompt-helper',
    name: 'prompt-helper',
    icon: 'document',
    description: {
        zh: 'Prompt 编写辅助工具，基于 PRISM 框架（Facet 驱动的 Prompt 设计方法论），提供编写、编辑、质量检测、行为诊断四大功能',
        en: 'Prompt writing assistant based on the PRISM framework (Facet-driven Prompt design methodology), providing writing, editing, quality auditing, and behavior diagnosis capabilities'
    },
    tags: [
        { zh: 'Prompt 工程', en: 'Prompt Engineering' },
        { zh: '质量检测', en: 'Quality Audit' },
        { zh: '行为诊断', en: 'Behavior Diagnosis' },
        { zh: '方法论', en: 'Methodology' }
    ],
    features: [
        { zh: '基于 Facet 分类的结构化 Prompt 设计方法', en: 'Structured Prompt design based on Facet classification' },
        { zh: '8 维度质量检测 + 结构化检测报告', en: '8-dimension quality audit with structured reports' },
        { zh: '从行为症状定位 Prompt 缺陷根因的诊断流程', en: 'Diagnosis workflow to locate Prompt defects from behavioral symptoms' },
        { zh: '完整的编辑流程：诊断→设计→修改→自检', en: 'Complete editing workflow: diagnose → design → modify → self-review' },
        { zh: '27 种错误类型到 Facet 的映射表（TRAIL + PRISM）', en: '27 error-to-Facet mapping types (TRAIL + PRISM)' }
    ],
    scripts: ['SKILL.md'],
    version: '1.0',
    author: 'shetengteng',
    repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/prompt-helper',
    useCases: [
        {
            title: { zh: '编写新 Prompt', en: 'Write a new Prompt' },
            userInput: { zh: '帮我为一个数据分类 Agent 编写 Prompt', en: 'Help me write a Prompt for a data classification Agent' },
            aiResponse: { zh: '加载结构设计指南，按 Standard Agent 标准结构设计章节，识别所需 Facet 类型并逐一编写', en: 'Load structure guide, design sections following Standard Agent template, identify required Facet types and write each one' }
        },
        {
            title: { zh: '检查 Prompt 质量', en: 'Audit Prompt quality' },
            userInput: { zh: '检查一下这个 Prompt 的质量', en: 'Check the quality of this Prompt' },
            aiResponse: { zh: '按 8 个维度逐项检查（Facet 识别、覆盖度、结构布局、场景、输出、示例、风格、信息传递），输出结构化检测报告', en: 'Check across 8 dimensions (Facet identification, coverage, structure, scenario, output, examples, style, info passing), output structured audit report' }
        },
        {
            title: { zh: '诊断行为问题', en: 'Diagnose behavior issues' },
            userInput: { zh: '这个 Agent 总是走错分支，帮我诊断一下', en: 'This Agent keeps taking wrong branches, help me diagnose' },
            aiResponse: { zh: '通过错误→Facet 映射表定位根因（场景型 Facet 缺陷），输出诊断报告并创建修复任务列表', en: 'Locate root cause via error-to-Facet mapping (Scenario Facet defect), output diagnosis report and create fix task list' }
        }
    ]
};
