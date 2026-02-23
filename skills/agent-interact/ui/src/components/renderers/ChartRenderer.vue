<script setup lang="ts">
import { computed } from 'vue'
import type { ChartNode } from '@/lib/types'
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

const props = defineProps<{ node: ChartNode }>()

const COLORS = [
  'rgb(99, 102, 241)', 'rgb(244, 63, 94)', 'rgb(34, 197, 94)',
  'rgb(234, 179, 8)', 'rgb(168, 85, 247)', 'rgb(14, 165, 233)',
]

const chartData = computed(() => {
  const raw = props.node.data ?? { labels: [], datasets: [] }
  const datasets = raw.datasets.map((ds, i) => {
    const color = COLORS[i % COLORS.length]!
    return {
      ...ds,
      borderColor: ds.borderColor || color,
      backgroundColor: ds.backgroundColor || (
        ['pie', 'doughnut'].includes(props.node.chartType)
          ? COLORS.slice(0, ds.data.length).map((c) => c.replace('rgb', 'rgba').replace(')', ', 0.7)'))
          : color.replace('rgb', 'rgba').replace(')', ', 0.1)')
      ),
      tension: 0.3,
      fill: props.node.chartType === 'line',
    }
  })
  return { labels: raw.labels, datasets }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: 'bottom' as const } },
}

const chartComponent = computed(() => {
  const map = { line: Line, bar: Bar, pie: Pie, doughnut: Doughnut, radar: Radar }
  return map[props.node.chartType] || Line
})
</script>

<template>
  <div class="h-64">
    <component :is="chartComponent" :data="chartData" :options="chartOptions" />
  </div>
</template>
