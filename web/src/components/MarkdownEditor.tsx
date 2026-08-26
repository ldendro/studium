import { markdown } from '@codemirror/lang-markdown'
import { EditorView } from '@codemirror/view'
import CodeMirror from '@uiw/react-codemirror'

const editorTheme = EditorView.theme(
  {
    '&': {
      height: '100%',
      backgroundColor: '#0e141d',
      color: '#dce2ea',
      fontSize: '13px',
    },
    '.cm-content': {
      padding: '22px 20px 40px',
      caretColor: '#deb66a',
      fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
      lineHeight: '1.65',
    },
    '.cm-gutters': {
      backgroundColor: '#0e141d',
      color: '#4f5b6b',
      border: 'none',
      paddingLeft: '6px',
    },
    '.cm-activeLine, .cm-activeLineGutter': {
      backgroundColor: 'rgba(255,255,255,.025)',
    },
    '&.cm-focused .cm-selectionBackground, ::selection': {
      backgroundColor: 'rgba(120,168,212,.22) !important',
    },
  },
  { dark: true },
)

export function MarkdownEditor({
  value,
  onChange,
  onCreateEditor,
}: {
  value: string
  onChange: (value: string) => void
  onCreateEditor: (view: EditorView) => void
}) {
  return (
    <CodeMirror
      value={value}
      height="100%"
      extensions={[markdown(), editorTheme, EditorView.lineWrapping]}
      onCreateEditor={onCreateEditor}
      onChange={onChange}
      basicSetup={{
        lineNumbers: true,
        foldGutter: true,
        highlightActiveLine: true,
        autocompletion: true,
        bracketMatching: true,
      }}
    />
  )
}
