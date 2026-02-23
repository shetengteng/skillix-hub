<script setup lang="ts">
import { computed } from 'vue'
import type {
  CheckboxNode,
  CustomNode,
  GridNode,
  InputNode,
  LayoutGap,
  SelectNode,
  TextareaNode,
} from '@/lib/types'
import AlertRenderer from '@/components/renderers/AlertRenderer.vue'
import BadgeRenderer from '@/components/renderers/BadgeRenderer.vue'
import ChartRenderer from '@/components/renderers/ChartRenderer.vue'
import CheckboxRenderer from '@/components/renderers/CheckboxRenderer.vue'
import CodeRenderer from '@/components/renderers/CodeRenderer.vue'
import DividerRenderer from '@/components/renderers/DividerRenderer.vue'
import HeadingRenderer from '@/components/renderers/HeadingRenderer.vue'
import ImageRenderer from '@/components/renderers/ImageRenderer.vue'
import InputRenderer from '@/components/renderers/InputRenderer.vue'
import KvRenderer from '@/components/renderers/KvRenderer.vue'
import ProgressRenderer from '@/components/renderers/ProgressRenderer.vue'
import SelectRenderer from '@/components/renderers/SelectRenderer.vue'
import TableRenderer from '@/components/renderers/TableRenderer.vue'
import TextRenderer from '@/components/renderers/TextRenderer.vue'
import TextareaRenderer from '@/components/renderers/TextareaRenderer.vue'

defineOptions({ name: 'ContentRenderer' })

const props = defineProps<{
  node: CustomNode
  model: Record<string, unknown>
  errors: Record<string, string>
}>()

const rendererRegistry = {
  text: TextRenderer,
  heading: HeadingRenderer,
  divider: DividerRenderer,
  alert: AlertRenderer,
  badge: BadgeRenderer,
  kv: KvRenderer,
  progress: ProgressRenderer,
  chart: ChartRenderer,
  code: CodeRenderer,
  image: ImageRenderer,
  table: TableRenderer,
  input: InputRenderer,
  select: SelectRenderer,
  checkbox: CheckboxRenderer,
  textarea: TextareaRenderer,
} as const

type RegisteredKind = keyof typeof rendererRegistry
type FieldNode = InputNode | SelectNode | CheckboxNode | TextareaNode

function isRegisteredKind(kind: CustomNode['kind']): kind is RegisteredKind {
  return kind in rendererRegistry
}

function isFieldNode(node: CustomNode): node is FieldNode {
  return node.kind === 'input' || node.kind === 'select' || node.kind === 'checkbox' || node.kind === 'textarea'
}

const renderer = computed(() => {
  if (!isRegisteredKind(props.node.kind)) return null
  return rendererRegistry[props.node.kind]
})

const extraBinding = computed(() => {
  if (isFieldNode(props.node)) {
    return {
      model: props.model,
      error: props.errors[props.node.id] || '',
    }
  }
  return {}
})

const gapMap: Record<LayoutGap, string> = { sm: 'gap-2', md: 'gap-4', lg: 'gap-6' }
const colsMap: Record<number, string> = { 2: 'grid-cols-2', 3: 'grid-cols-3', 4: 'grid-cols-4' }

function resolveGapClass(gap?: LayoutGap) {
  return gap ? gapMap[gap] : gapMap.md
}

function resolveGridClass(node: GridNode) {
  const gap = node.gap ? gapMap[node.gap] : gapMap.md
  const cols = colsMap[node.columns || 2] || colsMap[2]
  return `grid ${cols} ${gap}`
}
</script>

<template>
  <!-- Leaf renderers (no children, no circular dependency) -->
  <component
    v-if="renderer"
    :is="renderer"
    :node="props.node as any"
    v-bind="extraBinding"
  />

  <!-- Layout: row -->
  <div
    v-else-if="props.node.kind === 'row'"
    class="flex flex-wrap items-start"
    :class="resolveGapClass(props.node.gap)"
  >
    <div
      v-for="(child, index) in props.node.children"
      :key="`row-${index}`"
      class="min-w-0 flex-1 basis-0"
    >
      <ContentRenderer :node="child" :model="props.model" :errors="props.errors" />
    </div>
  </div>

  <!-- Layout: column -->
  <div
    v-else-if="props.node.kind === 'column'"
    class="flex flex-col"
    :class="resolveGapClass(props.node.gap)"
  >
    <ContentRenderer
      v-for="(child, index) in props.node.children"
      :key="`col-${index}`"
      :node="child"
      :model="props.model"
      :errors="props.errors"
    />
  </div>

  <!-- Layout: grid -->
  <div
    v-else-if="props.node.kind === 'grid'"
    :class="resolveGridClass(props.node as GridNode)"
  >
    <ContentRenderer
      v-for="(child, index) in (props.node as GridNode).children"
      :key="`grid-${index}`"
      :node="child"
      :model="props.model"
      :errors="props.errors"
    />
  </div>

  <!-- Layout: section -->
  <div
    v-else-if="props.node.kind === 'section'"
    class="space-y-3 rounded-lg border p-4"
  >
    <p v-if="(props.node as any).title" class="text-sm font-semibold">
      {{ (props.node as any).title }}
    </p>
    <ContentRenderer
      v-for="(child, index) in (props.node as any).children"
      :key="`sec-${index}`"
      :node="child"
      :model="props.model"
      :errors="props.errors"
    />
  </div>

  <!-- Layout: group -->
  <div
    v-else-if="props.node.kind === 'group'"
    class="flex flex-wrap items-center gap-2"
  >
    <ContentRenderer
      v-for="(child, index) in (props.node as any).children"
      :key="`grp-${index}`"
      :node="child"
      :model="props.model"
      :errors="props.errors"
    />
  </div>

  <!-- Fallback -->
  <div v-else class="rounded-md border border-dashed p-3 text-sm text-muted-foreground">
    Unsupported component: {{ (props.node as any).kind }}
  </div>
</template>
