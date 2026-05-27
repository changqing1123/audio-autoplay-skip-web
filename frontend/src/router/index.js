import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import ListenedView from '../views/ListenedView.vue'
import PlayerView from '../views/PlayerView.vue'
import SettingsView from '../views/SettingsView.vue'
import { hasAccessToken } from '../state/appState'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/player/:id?',
      name: 'player',
      component: PlayerView,
    },
    {
      path: '/settings',
      name: 'settings',
      component: SettingsView,
    },
    {
      path: '/settings/listened',
      name: 'listened',
      component: ListenedView,
    },
  ],
})

router.beforeEach((to) => {
  if (to.name !== 'settings' && !hasAccessToken()) {
    return { name: 'settings' }
  }
  return true
})

export default router
