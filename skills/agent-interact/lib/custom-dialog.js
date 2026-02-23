'use strict';

const Ajv = require('ajv');

const LIMITS = {
  maxContent: 40,
  maxDepth: 4,
  maxTableRows: 200,
  maxChartPoints: 1000,
};

const customDialogSchema = {
  type: 'object',
  additionalProperties: false,
  required: ['type', 'content'],
  properties: {
    type: { const: 'custom' },
    schemaVersion: { type: 'string', enum: ['1.0'] },
    title: { type: 'string', maxLength: 200 },
    message: { type: 'string', maxLength: 4000 },
    timeout: { type: 'number', minimum: 1 },
    content: {
      type: 'array',
      minItems: 1,
      maxItems: LIMITS.maxContent,
      items: { $ref: '#/$defs/customNode' },
    },
    actions: {
      type: 'array',
      minItems: 1,
      maxItems: 8,
      items: { $ref: '#/$defs/customAction' },
    },
    meta: {
      type: 'object',
      additionalProperties: false,
      properties: {
        maxWidth: { enum: ['sm', 'md', 'lg', 'xl', '2xl'] },
        scroll: { enum: ['auto', 'content'] },
      },
    },
  },
  $defs: {
    textNode: {
      type: 'object',
      additionalProperties: false,
      required: ['kind', 'value'],
      properties: {
        kind: { const: 'text' },
        value: { type: 'string', maxLength: 20000 },
      },
    },
    headingNode: {
      type: 'object',
      additionalProperties: false,
      required: ['kind', 'value'],
      properties: {
        kind: { const: 'heading' },
        value: { type: 'string', maxLength: 500 },
        level: { type: 'integer', enum: [1, 2, 3, 4] },
      },
    },
    dividerNode: {
      type: 'object',
      additionalProperties: false,
      required: ['kind'],
      properties: {
        kind: { const: 'divider' },
      },
    },
    alertNode: {
      type: 'object',
      additionalProperties: false,
      required: ['kind', 'value'],
      properties: {
        kind: { const: 'alert' },
        value: { type: 'string', maxLength: 2000 },
        level: { enum: ['info', 'warning', 'error', 'success'] },
      },
    },
    tableNode: {
      type: 'object',
      additionalProperties: false,
      required: ['kind', 'columns', 'rows'],
      properties: {
        kind: { const: 'table' },
        columns: {
          type: 'array',
          minItems: 1,
          maxItems: 20,
          items: { type: 'string', maxLength: 200 },
        },
        rows: {
          type: 'array',
          maxItems: LIMITS.maxTableRows,
          items: {
            type: 'array',
            maxItems: 20,
            items: { type: 'string', maxLength: 2000 },
          },
        },
      },
    },
    inputNode: {
      type: 'object',
      additionalProperties: false,
      required: ['kind', 'id', 'label'],
      properties: {
        kind: { const: 'input' },
        id: { type: 'string', pattern: '^[A-Za-z0-9_]+$' },
        label: { type: 'string', minLength: 1, maxLength: 100 },
        required: { type: 'boolean' },
        placeholder: { type: 'string', maxLength: 200 },
        default: { type: 'string', maxLength: 2000 },
      },
    },
    selectNode: {
      type: 'object',
      additionalProperties: false,
      required: ['kind', 'id', 'label', 'options'],
      properties: {
        kind: { const: 'select' },
        id: { type: 'string', pattern: '^[A-Za-z0-9_]+$' },
        label: { type: 'string', minLength: 1, maxLength: 100 },
        options: {
          type: 'array',
          minItems: 1,
          maxItems: 50,
          items: { type: 'string', maxLength: 200 },
        },
        required: { type: 'boolean' },
        default: { type: 'string', maxLength: 200 },
        placeholder: { type: 'string', maxLength: 200 },
      },
    },
    checkboxNode: {
      type: 'object',
      additionalProperties: false,
      required: ['kind', 'id', 'label'],
      properties: {
        kind: { const: 'checkbox' },
        id: { type: 'string', pattern: '^[A-Za-z0-9_]+$' },
        label: { type: 'string', minLength: 1, maxLength: 100 },
        required: { type: 'boolean' },
        default: { type: 'boolean' },
      },
    },
    rowNode: {
      type: 'object',
      additionalProperties: false,
      required: ['kind', 'children'],
      properties: {
        kind: { const: 'row' },
        gap: { enum: ['sm', 'md', 'lg'] },
        children: {
          type: 'array',
          minItems: 1,
          maxItems: 8,
          items: { $ref: '#/$defs/customNode' },
        },
      },
    },
    badgeNode: {
      type: 'object',
      additionalProperties: false,
      required: ['kind', 'value'],
      properties: {
        kind: { const: 'badge' },
        value: { type: 'string', maxLength: 200 },
        variant: { enum: ['default', 'success', 'warning', 'error'] },
      },
    },
    kvNode: {
      type: 'object',
      additionalProperties: false,
      required: ['kind', 'items'],
      properties: {
        kind: { const: 'kv' },
        items: {
          type: 'array',
          minItems: 1,
          maxItems: 30,
          items: {
            type: 'object',
            additionalProperties: false,
            required: ['key', 'value'],
            properties: {
              key: { type: 'string', maxLength: 200 },
              value: { type: 'string', maxLength: 2000 },
            },
          },
        },
      },
    },
    progressNode: {
      type: 'object',
      additionalProperties: false,
      required: ['kind', 'value'],
      properties: {
        kind: { const: 'progress' },
        value: { type: 'number', minimum: 0, maximum: 100 },
        label: { type: 'string', maxLength: 200 },
      },
    },
    chartNode: {
      type: 'object',
      additionalProperties: false,
      required: ['kind', 'chartType', 'data'],
      properties: {
        kind: { const: 'chart' },
        chartType: { enum: ['line', 'bar', 'pie', 'doughnut', 'radar'] },
        data: {
          type: 'object',
          required: ['labels', 'datasets'],
          properties: {
            labels: { type: 'array', items: { type: 'string' } },
            datasets: {
              type: 'array',
              minItems: 1,
              maxItems: 10,
              items: {
                type: 'object',
                required: ['label', 'data'],
                properties: {
                  label: { type: 'string' },
                  data: { type: 'array', items: { type: 'number' } },
                  backgroundColor: {},
                  borderColor: {},
                },
              },
            },
          },
        },
      },
    },
    codeNode: {
      type: 'object',
      additionalProperties: false,
      required: ['kind', 'value'],
      properties: {
        kind: { const: 'code' },
        value: { type: 'string', maxLength: 20000 },
        language: { type: 'string', maxLength: 30 },
      },
    },
    imageNode: {
      type: 'object',
      additionalProperties: false,
      required: ['kind', 'src'],
      properties: {
        kind: { const: 'image' },
        src: { type: 'string', maxLength: 2000, pattern: '^https://' },
        alt: { type: 'string', maxLength: 500 },
        width: { type: 'integer', minimum: 1, maximum: 2000 },
        height: { type: 'integer', minimum: 1, maximum: 2000 },
      },
    },
    textareaNode: {
      type: 'object',
      additionalProperties: false,
      required: ['kind', 'id', 'label'],
      properties: {
        kind: { const: 'textarea' },
        id: { type: 'string', pattern: '^[A-Za-z0-9_]+$' },
        label: { type: 'string', minLength: 1, maxLength: 100 },
        required: { type: 'boolean' },
        placeholder: { type: 'string', maxLength: 200 },
        default: { type: 'string', maxLength: 10000 },
      },
    },
    columnNode: {
      type: 'object',
      additionalProperties: false,
      required: ['kind', 'children'],
      properties: {
        kind: { const: 'column' },
        gap: { enum: ['sm', 'md', 'lg'] },
        children: {
          type: 'array',
          minItems: 1,
          maxItems: 20,
          items: { $ref: '#/$defs/customNode' },
        },
      },
    },
    gridNode: {
      type: 'object',
      additionalProperties: false,
      required: ['kind', 'children'],
      properties: {
        kind: { const: 'grid' },
        columns: { type: 'integer', enum: [2, 3, 4] },
        gap: { enum: ['sm', 'md', 'lg'] },
        children: {
          type: 'array',
          minItems: 1,
          maxItems: 20,
          items: { $ref: '#/$defs/customNode' },
        },
      },
    },
    sectionNode: {
      type: 'object',
      additionalProperties: false,
      required: ['kind', 'children'],
      properties: {
        kind: { const: 'section' },
        title: { type: 'string', maxLength: 200 },
        children: {
          type: 'array',
          minItems: 1,
          maxItems: 20,
          items: { $ref: '#/$defs/customNode' },
        },
      },
    },
    groupNode: {
      type: 'object',
      additionalProperties: false,
      required: ['kind', 'children'],
      properties: {
        kind: { const: 'group' },
        children: {
          type: 'array',
          minItems: 1,
          maxItems: 20,
          items: { $ref: '#/$defs/customNode' },
        },
      },
    },
    customNode: {
      oneOf: [
        { $ref: '#/$defs/textNode' },
        { $ref: '#/$defs/headingNode' },
        { $ref: '#/$defs/dividerNode' },
        { $ref: '#/$defs/alertNode' },
        { $ref: '#/$defs/badgeNode' },
        { $ref: '#/$defs/kvNode' },
        { $ref: '#/$defs/progressNode' },
        { $ref: '#/$defs/chartNode' },
        { $ref: '#/$defs/codeNode' },
        { $ref: '#/$defs/imageNode' },
        { $ref: '#/$defs/tableNode' },
        { $ref: '#/$defs/inputNode' },
        { $ref: '#/$defs/selectNode' },
        { $ref: '#/$defs/checkboxNode' },
        { $ref: '#/$defs/textareaNode' },
        { $ref: '#/$defs/rowNode' },
        { $ref: '#/$defs/columnNode' },
        { $ref: '#/$defs/gridNode' },
        { $ref: '#/$defs/sectionNode' },
        { $ref: '#/$defs/groupNode' },
      ],
    },
    customAction: {
      type: 'object',
      additionalProperties: false,
      required: ['id', 'label'],
      properties: {
        id: { type: 'string', pattern: '^[A-Za-z0-9_]+$' },
        label: { type: 'string', minLength: 1, maxLength: 80 },
        variant: { enum: ['default', 'destructive', 'outline', 'secondary', 'ghost'] },
        submit: { type: 'boolean' },
        requireValid: { type: 'boolean' },
        closeOnSubmit: { type: 'boolean' },
      },
    },
  },
};

const ajv = new Ajv({ allErrors: true, strict: false });
const validateCustomDialog = ajv.compile(customDialogSchema);

function toErrorPath(instancePath, additionalProperty) {
  if (!instancePath && additionalProperty) return `/${additionalProperty}`;
  if (!instancePath) return '/';
  if (!additionalProperty) return instancePath;
  return `${instancePath}/${additionalProperty}`;
}

function formatAjvErrors(errors) {
  if (!errors) return [];
  const formatted = errors.map((err) => {
    const additionalProperty = err.keyword === 'additionalProperties'
      ? err.params && err.params.additionalProperty
      : null;
    return {
      path: toErrorPath(err.instancePath, additionalProperty || null),
      message: err.message || 'invalid value',
    };
  });
  const seen = new Set();
  return formatted.filter((item) => {
    const key = `${item.path}::${item.message}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function isFieldNode(node) {
  return node.kind === 'input' || node.kind === 'select' || node.kind === 'checkbox' || node.kind === 'textarea';
}

function hasChildren(node) {
  return node.kind === 'row' || node.kind === 'column' || node.kind === 'grid' || node.kind === 'section' || node.kind === 'group';
}

function collectTreeErrors(nodes, depth, path, fieldIds, errors) {
  if (depth > LIMITS.maxDepth) {
    errors.push({
      path,
      message: `depth exceeds limit ${LIMITS.maxDepth}`,
    });
    return;
  }

  for (let index = 0; index < nodes.length; index += 1) {
    const node = nodes[index];
    const nodePath = `${path}/${index}`;

    if (node.kind === 'table' && node.rows && node.rows.length > LIMITS.maxTableRows) {
      errors.push({
        path: `${nodePath}/rows`,
        message: `rows exceeds limit ${LIMITS.maxTableRows}`,
      });
    }

    if (node.kind === 'chart' && node.data && node.data.datasets) {
      const totalPoints = node.data.datasets.reduce((sum, ds) => sum + (ds.data ? ds.data.length : 0), 0);
      if (totalPoints > LIMITS.maxChartPoints) {
        errors.push({
          path: `${nodePath}/data`,
          message: `chart total data points (${totalPoints}) exceeds limit ${LIMITS.maxChartPoints}`,
        });
      }
    }

    if (isFieldNode(node)) {
      if (fieldIds.has(node.id)) {
        errors.push({
          path: `${nodePath}/id`,
          message: `duplicate field id "${node.id}"`,
        });
      } else {
        fieldIds.add(node.id);
      }
    }

    if (hasChildren(node)) {
      collectTreeErrors(node.children, depth + 1, `${nodePath}/children`, fieldIds, errors);
    }
  }
}

function normalizeNode(node) {
  if (node.kind === 'heading') {
    return { ...node, level: node.level || 2 };
  }

  if (node.kind === 'alert') {
    return { ...node, level: node.level || 'info' };
  }

  if (node.kind === 'badge') {
    return { ...node, variant: node.variant || 'default' };
  }

  if (node.kind === 'input' || node.kind === 'select' || node.kind === 'checkbox' || node.kind === 'textarea') {
    return { ...node, required: node.required === true };
  }

  if (node.kind === 'row' || node.kind === 'column' || node.kind === 'grid') {
    return {
      ...node,
      gap: node.gap || 'md',
      columns: node.kind === 'grid' ? (node.columns || 2) : undefined,
      children: node.children.map((child) => normalizeNode(child)),
    };
  }

  if (node.kind === 'section' || node.kind === 'group') {
    return {
      ...node,
      children: node.children.map((child) => normalizeNode(child)),
    };
  }

  return { ...node };
}

function normalizeActions(actions) {
  if (!actions || actions.length === 0) {
    return [
      {
        id: 'ok',
        label: '确定',
        submit: false,
        requireValid: false,
        closeOnSubmit: true,
      },
    ];
  }

  return actions.map((action) => ({
    ...action,
    submit: action.submit !== false,
    requireValid: action.requireValid === true,
    closeOnSubmit: action.closeOnSubmit !== false,
  }));
}

function normalizeCustomDialog(dialog) {
  return {
    ...dialog,
    schemaVersion: dialog.schemaVersion || '1.0',
    content: dialog.content.map((node) => normalizeNode(node)),
    actions: normalizeActions(dialog.actions),
  };
}

function validateAndNormalizeCustomDialog(request) {
  const candidate = JSON.parse(JSON.stringify(request));
  if (!candidate.schemaVersion) candidate.schemaVersion = '1.0';

  const valid = validateCustomDialog(candidate);
  const errors = formatAjvErrors(validateCustomDialog.errors);

  if (valid) {
    collectTreeErrors(candidate.content, 1, '/content', new Set(), errors);
  }

  if (errors.length > 0) {
    return { ok: false, errors };
  }

  return { ok: true, value: normalizeCustomDialog(candidate) };
}

module.exports = {
  LIMITS,
  validateAndNormalizeCustomDialog,
};
