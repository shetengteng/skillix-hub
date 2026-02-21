/**
 * Skillix Hub - Skills Data Aggregator
 * 聚合所有 skill 独立数据文件，组装为 SKILLS_DATA 数组
 *
 * 每个 skill 的数据存放在 scripts/skills/<id>.js 中，
 * 通过 window.SKILL_DATA_<ID> 变量暴露。
 *
 * 新增 skill 时，只需：
 * 1. 创建 scripts/skills/<id>.js
 * 2. 在 index.html 中添加 <script src="scripts/skills/<id>.js">
 * 3. 在下方 SKILL_KEYS 数组中添加对应的变量名
 */

const SKILL_KEYS = [
    'SKILL_DATA_MEMORY',
    'SKILL_DATA_BEHAVIOR_PREDICTION',
    'SKILL_DATA_CONTINUOUS_LEARNING',
    'SKILL_DATA_UNIAPP_MP_GENERATOR',
    'SKILL_DATA_SWAGGER_API_READER',
    'SKILL_DATA_PLAYWRIGHT',
    'SKILL_DATA_API_TRACER',
    'SKILL_DATA_WEB_CONTENT_READER',
    'SKILL_DATA_SKILL_BUILDER',
];

const SKILLS_DATA = SKILL_KEYS
    .map(key => window[key])
    .filter(Boolean);

const ICON_PATHS = {
    lightbulb: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z',
    document: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
    chart: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
    brain: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z',
    plus: 'M12 6v6m0 0v6m0-6h6m-6 0H6',
    globe: 'M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    folder: 'M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z',
    info: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    code: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4'
};

if (typeof window !== 'undefined') {
    window.SKILLS_DATA = SKILLS_DATA;
    window.ICON_PATHS = ICON_PATHS;
}
