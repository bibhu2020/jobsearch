<script setup lang="ts">
import { watch, onBeforeUnmount } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'

const props = defineProps<{
  modelValue: string
  placeholder?: string
  formatting?: boolean   // show AI-format button in toolbar
}>()

const emit = defineEmits<{
  'update:modelValue': [val: string]
  'format-request': [text: string]  // fired when user wants AI formatting
}>()

const formatState = defineModel<'idle' | 'formatting'>('formatState', { default: 'idle' })

const editor = useEditor({
  content: props.modelValue,
  extensions: [
    StarterKit,
    Placeholder.configure({ placeholder: props.placeholder ?? 'Paste or type a job description…' }),
  ],
  editorProps: {
    handlePaste(view, event) {
      // Only intercept plain-text pastes (not HTML from another rich editor)
      const types = event.clipboardData?.types ?? []
      const hasHtml = types.includes('text/html')
      const text = event.clipboardData?.getData('text/plain') ?? ''

      if (!hasHtml && text.length > 150) {
        // Let Tiptap insert the plain text normally first, then request AI format
        setTimeout(() => emit('format-request', text), 0)
      }
      return false  // don't block default paste
    },
  },
  onUpdate({ editor }) {
    emit('update:modelValue', editor.getHTML())
  },
})

// Keep editor in sync when parent resets the value externally
watch(
  () => props.modelValue,
  (val) => {
    if (editor.value && editor.value.getHTML() !== val) {
      editor.value.commands.setContent(val, false as any)
    }
  },
)

onBeforeUnmount(() => editor.value?.destroy())
</script>

<template>
  <div class="rich-editor-wrapper">
    <!-- Toolbar -->
    <div class="flex flex-wrap items-center gap-0.5 px-2 py-1.5 bg-slate-700/60 border border-slate-600 border-b-0 rounded-t-lg">
      <!-- Headings -->
      <button type="button" title="Heading"
        :class="['toolbar-btn', editor?.isActive('heading', { level: 2 }) && 'active']"
        @mousedown.prevent="editor?.chain().focus().toggleHeading({ level: 2 }).run()">
        H
      </button>

      <div class="w-px h-4 bg-slate-600 mx-1"></div>

      <!-- Bold -->
      <button type="button" title="Bold"
        :class="['toolbar-btn font-bold', editor?.isActive('bold') && 'active']"
        @mousedown.prevent="editor?.chain().focus().toggleBold().run()">
        B
      </button>

      <!-- Italic -->
      <button type="button" title="Italic"
        :class="['toolbar-btn italic', editor?.isActive('italic') && 'active']"
        @mousedown.prevent="editor?.chain().focus().toggleItalic().run()">
        I
      </button>

      <div class="w-px h-4 bg-slate-600 mx-1"></div>

      <!-- Bullet list -->
      <button type="button" title="Bullet list"
        :class="['toolbar-btn', editor?.isActive('bulletList') && 'active']"
        @mousedown.prevent="editor?.chain().focus().toggleBulletList().run()">
        <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16"/>
          <circle cx="1.5" cy="6" r="1.5" fill="currentColor" stroke="none"/>
          <circle cx="1.5" cy="12" r="1.5" fill="currentColor" stroke="none"/>
          <circle cx="1.5" cy="18" r="1.5" fill="currentColor" stroke="none"/>
        </svg>
      </button>

      <!-- Ordered list -->
      <button type="button" title="Numbered list"
        :class="['toolbar-btn', editor?.isActive('orderedList') && 'active']"
        @mousedown.prevent="editor?.chain().focus().toggleOrderedList().run()">
        <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 6h11M9 12h11M9 18h11"/>
          <text x="0" y="7" class="text-[7px]" font-size="7" fill="currentColor" stroke="none">1</text>
          <text x="0" y="13" class="text-[7px]" font-size="7" fill="currentColor" stroke="none">2</text>
          <text x="0" y="19" class="text-[7px]" font-size="7" fill="currentColor" stroke="none">3</text>
        </svg>
      </button>

      <div class="w-px h-4 bg-slate-600 mx-1"></div>

      <!-- Clear formatting -->
      <button type="button" title="Clear formatting"
        class="toolbar-btn"
        @mousedown.prevent="editor?.chain().focus().unsetAllMarks().run()">
        <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>

      <!-- AI format button -->
      <template v-if="formatting">
        <div class="flex-1"></div>
        <button type="button"
          :disabled="formatState === 'formatting'"
          class="flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium bg-indigo-700/40 hover:bg-indigo-600/50 text-indigo-300 border border-indigo-600/40 disabled:opacity-50 transition"
          @mousedown.prevent="$emit('format-request', editor?.getText() ?? '')">
          <svg v-if="formatState === 'formatting'" class="animate-spin h-3 w-3" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
          </svg>
          <svg v-else class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z"/>
          </svg>
          {{ formatState === 'formatting' ? 'Formatting…' : '✦ Format with AI' }}
        </button>
      </template>
    </div>

    <!-- Editor area -->
    <EditorContent
      :editor="editor"
      class="rich-editor-content"
    />
  </div>
</template>

<style scoped>
.rich-editor-wrapper {
  @apply w-full;
}

.toolbar-btn {
  @apply px-2 py-1 rounded text-xs text-slate-400 hover:text-slate-100 hover:bg-slate-600/60 transition flex items-center justify-center min-w-[26px] h-6;
}
.toolbar-btn.active {
  @apply bg-indigo-700/50 text-indigo-300;
}
</style>

<style>
/* Global because Tiptap renders content outside scoped context */
.rich-editor-content .tiptap {
  @apply min-h-[200px] px-3 py-2.5 bg-slate-700/50 border border-slate-600 rounded-b-lg text-slate-100 text-sm outline-none focus:border-indigo-500 focus:bg-slate-700 transition overflow-y-auto;
  max-height: 480px;
}
.rich-editor-content .tiptap:focus {
  box-shadow: 0 0 0 1px theme('colors.indigo.500');
}
.rich-editor-content .tiptap p.is-editor-empty:first-child::before {
  content: attr(data-placeholder);
  @apply text-slate-500 pointer-events-none float-left h-0;
}
.rich-editor-content .tiptap h2 {
  @apply text-base font-semibold text-slate-100 mt-4 mb-1.5 first:mt-0;
}
.rich-editor-content .tiptap p {
  @apply mb-2 text-slate-300;
}
.rich-editor-content .tiptap ul {
  @apply list-disc pl-5 mb-2 space-y-0.5 text-slate-300;
}
.rich-editor-content .tiptap ol {
  @apply list-decimal pl-5 mb-2 space-y-0.5 text-slate-300;
}
.rich-editor-content .tiptap strong {
  @apply font-semibold text-slate-100;
}
.rich-editor-content .tiptap em {
  @apply italic;
}
</style>
