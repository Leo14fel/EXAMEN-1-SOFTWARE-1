import { config } from '@vue/test-utils'
import { vuetify } from '../plugins/vuetify'

// Register the same plugin as the application for every Vue component test.
config.global.plugins = [vuetify]
