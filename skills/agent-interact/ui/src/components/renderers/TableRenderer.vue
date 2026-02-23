<script setup lang="ts">
import type { TableNode } from '@/lib/types'

defineProps<{ node: TableNode }>()
</script>

<template>
  <div class="overflow-x-auto rounded-md border">
    <table class="w-full text-sm">
      <thead class="bg-muted/50">
        <tr>
          <th
            v-for="(column, index) in node.columns"
            :key="`column-${index}`"
            class="px-3 py-2 text-left font-medium"
          >
            {{ column }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(row, rowIndex) in node.rows"
          :key="`row-${rowIndex}`"
          class="border-t"
        >
          <td
            v-for="(cell, cellIndex) in row"
            :key="`cell-${rowIndex}-${cellIndex}`"
            class="px-3 py-2 align-top"
          >
            {{ cell }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
