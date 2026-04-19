import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import KBDetailView from '../views/KBDetailView.vue'
import TasksView from '../views/TasksView.vue'

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/kb/:id', name: 'kb-detail', component: KBDetailView, props: true },
  { path: '/tasks', name: 'tasks', component: TasksView },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
