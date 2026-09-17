import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

export const vuetify = createVuetify({
  components,
  directives,
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