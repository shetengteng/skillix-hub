<script setup lang="ts">
import { computed } from 'vue'
import type { ChartDialog as ChartDialogType } from '@/lib/types'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, ArcElement, RadialLinearScale,
  Title, Tooltip, Legend, Filler,
} from 'chart.js'
import { Line, Bar, Pie, Doughnut, Radar } from 'vue-chartjs'

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, ArcElement, RadialLinearScale,
  Title, Tooltip, Legend, Filler,
)

const props = defineProps<{ dialog: ChartDialogType }>()
const emit = defineEmits<{ respond: [action: string, data?: unknown] }>()

const COLORS = [
  'rgb(99, 102, 241)', 'rgb(244, 63, 94)', 'rgb(34, 197, 94)',
  'rgb(234, 179, 8)', 'rgb(168, 85, 247)', 'rgb(14, 165, 233)',
]

const chartData = computed(() => {
  const raw = props.dialog.data ?? { labels: [], datasets: [] }
  const datasets = raw.datasets.map((ds, i) => {
    const color = COLORS[i % COLORS.length]!
    return {
    ...ds,
    borderColor: ds.borderColor || color,
    backgroundColor: ds.backgroundColor || (
      ['pie', 'doughnut'].includes(props.dialog.chartType)
        ? COLORS.slice(0, ds.data.length).map((c) => c.replace('rgb', 'rgba').replace(')', ', 0.7)'))
        : color.replace('rgb', 'rgba').replace(')', ', 0.1)')
    ),
    tension: 0.3,
    fill: props.dialog.chartType === 'line',
  }})
  return { labels: raw.labels, datasets }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: 'bottom' as const } },
}

const chartComponent = computed(() => {
  const map = { line: Line, bar: Bar, pie: Pie, doughnut: Doughnut, radar: Radar }
  return map[props.dialog.chartType] || Line
})

const actions = computed(() =>
  props.dialog.actions?.length ? props.dialog.actions : [{ id: 'ok', label: '了解' }]
)
</script>

<template>
  <Dialog :open="true">
    <DialogContent class="sm:max-w-2xl" @interact-outside.prevent>
      <DialogHeader>
        <DialogTitle>{{ dialog.title || '图表' }}</DialogTitle>
        <DialogDescription v-if="dialog.message">{{ dialog.message }}</DialogDescription>
      </DialogHeader>

      <div class="h-80 py-4">
        <component :is="chartComponent" :data="chartData" :options="chartOptions" />
      </div>

      <DialogFooter class="gap-2">
        <Button
          v-for="act in actions"
          :key="act.id"
          :variant="(act as any).variant || 'default'"
          @click="emit('respond', act.id)"
        >
          {{ act.label }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
