import { createVuetify } from 'vuetify'

export const vuetify = createVuetify({
  theme: {
    defaultTheme: 'caseDark',
    themes: {
      caseDark: {
        dark: true,
        colors: {
          background: '#0f1720',
          surface: '#17222d',
          primary: '#35d0ba',
          secondary: '#8b7cf6',
        },
      },
    },
  },
})
