import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "YiDocs",
  description: "YiAi 文档",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: '首页', link: '/' },
      { text: 'YiAdmin', link: '/YiAdmin/index.md' }
    ],

    sidebar: [
      {
        text: 'YiAdmin',
        items: [
          { text: 'YiAdmin', link: '/YiAdmin/index.md' }
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/vuejs/vitepress' }
    ]
  }
})
