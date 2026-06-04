<script setup lang="ts">
// TODO: 实现标注工作台
</script>

<template>
  <div class="h-screen flex flex-col">
    <!-- 顶部工具栏 -->
    <header class="h-12 bg-surface border-b border-border flex items-center px-4">
      <router-link to="/app/projects" class="text-muted hover:text-text mr-4">
        返回
      </router-link>
      <h1 class="text-sm font-medium text-text">标注工作台</h1>
    </header>

    <!-- 主要工作区 -->
    <div class="flex-1 flex">
      <!-- 左侧任务队列 -->
      <aside class="w-64 bg-surface border-r border-border">
        <div class="p-4">
          <h3 class="text-sm font-medium text-text mb-2">任务队列</h3>
          <p class="text-xs text-muted">开发中...</p>
        </div>
      </aside>

      <!-- 中间画布区 -->
      <main class="flex-1 bg-background relative">
        <div class="absolute inset-0 flex items-center justify-center text-muted">
          标注画布开发中...
        </div>
      </main>

      <!-- 右侧属性面板 -->
      <aside class="w-72 bg-surface border-l border-border">
        <div class="p-4">
          <h3 class="text-sm font-medium text-text mb-2">属性面板</h3>
          <p class="text-xs text-muted">开发中...</p>
        </div>
      </aside>
    </div>
  </div>
</template>
