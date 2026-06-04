<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const activeTab = ref((route.query.tab as string) || 'jobs')

// TODO: 加载项目详情
</script>

<template>
  <div class="p-6">
    <h2 class="text-2xl font-bold text-text mb-6">项目详情</h2>

    <!-- Tab 导航 -->
    <div class="border-b border-border mb-6">
      <nav class="flex space-x-8">
        <router-link
          :to="{ query: { tab: 'jobs' } }"
          class="py-2 px-1 border-b-2 text-sm font-medium"
          :class="activeTab === 'jobs' ? 'border-accent text-accent' : 'border-transparent text-muted'"
        >
          任务
        </router-link>
        <router-link
          :to="{ query: { tab: 'exports' } }"
          class="py-2 px-1 border-b-2 text-sm font-medium"
          :class="activeTab === 'exports' ? 'border-accent text-accent' : 'border-transparent text-muted'"
        >
          导出
        </router-link>
      </nav>
    </div>

    <!-- Tab 内容 -->
    <div>
      <div v-if="activeTab === 'jobs'">
        <!-- TODO: 任务列表 -->
        <p class="text-muted">任务列表开发中...</p>
      </div>
      <div v-else-if="activeTab === 'exports'">
        <!-- TODO: 导出列表 -->
        <p class="text-muted">导出列表开发中...</p>
      </div>
    </div>
  </div>
</template>
