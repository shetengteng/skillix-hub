export interface DialogOption {
  id: string
  label: string
  description?: string
}

export type DialogVariant = 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost'

export interface DialogAction {
  id: string
  label: string
  variant?: DialogVariant
}

export type DialogType = 'confirm' | 'wait' | 'chart' | 'notification' | 'form' | 'approval' | 'progress' | 'custom'

export interface BaseDialog {
  id: string
  type: DialogType
  title?: string
  message?: string
  timeout?: number
}

export interface ConfirmDialog extends BaseDialog {
  type: 'confirm'
  options: DialogOption[]
  allowMultiple?: boolean
}

export interface WaitDialog extends BaseDialog {
  type: 'wait'
  confirmText?: string
  cancelText?: string
}

export interface ChartDialog extends BaseDialog {
  type: 'chart'
  chartType: 'line' | 'bar' | 'pie' | 'doughnut' | 'radar'
  data: {
    labels: string[]
    datasets: Array<{
      label: string
      data: number[]
      backgroundColor?: string | string[]
      borderColor?: string | string[]
    }>
  }
  actions?: DialogAction[]
}

export interface NotificationDialog extends BaseDialog {
  type: 'notification'
  level: 'info' | 'warning' | 'error' | 'success'
  autoClose?: number
}

export interface FormField {
  id: string
  label: string
  type: 'text' | 'number' | 'select' | 'textarea' | 'checkbox'
  default?: string | number | boolean
  options?: string[]
  placeholder?: string
  required?: boolean
}

export interface FormDialog extends BaseDialog {
  type: 'form'
  fields: FormField[]
  submitText?: string
  cancelText?: string
}

export interface ApprovalDialog extends BaseDialog {
  type: 'approval'
  severity: 'low' | 'medium' | 'high' | 'critical'
  details?: Record<string, string>
  approveText?: string
  rejectText?: string
}

export interface ProgressStep {
  id: string
  label: string
  status: 'pending' | 'running' | 'completed' | 'failed'
}

export interface ProgressDialog extends BaseDialog {
  type: 'progress'
  steps: ProgressStep[]
  percent?: number
  actions?: DialogAction[]
}

export type LayoutGap = 'sm' | 'md' | 'lg'

export interface TextNode {
  kind: 'text'
  value: string
}

export interface HeadingNode {
  kind: 'heading'
  value: string
  level?: 1 | 2 | 3 | 4
}

export interface DividerNode {
  kind: 'divider'
}

export interface AlertNode {
  kind: 'alert'
  value: string
  level?: 'info' | 'warning' | 'error' | 'success'
}

export interface TableNode {
  kind: 'table'
  columns: string[]
  rows: string[][]
}

export interface InputNode {
  kind: 'input'
  id: string
  label: string
  required?: boolean
  placeholder?: string
  default?: string
}

export interface SelectNode {
  kind: 'select'
  id: string
  label: string
  options: string[]
  required?: boolean
  placeholder?: string
  default?: string
}

export interface CheckboxNode {
  kind: 'checkbox'
  id: string
  label: string
  required?: boolean
  default?: boolean
}

export interface BadgeNode {
  kind: 'badge'
  value: string
  variant?: 'default' | 'success' | 'warning' | 'error'
}

export interface KvItem {
  key: string
  value: string
}

export interface KvNode {
  kind: 'kv'
  items: KvItem[]
}

export interface ProgressNode {
  kind: 'progress'
  value: number
  label?: string
}

export interface ChartDataset {
  label: string
  data: number[]
  backgroundColor?: string | string[]
  borderColor?: string | string[]
}

export interface ChartData {
  labels: string[]
  datasets: ChartDataset[]
}

export interface ChartNode {
  kind: 'chart'
  chartType: 'line' | 'bar' | 'pie' | 'doughnut' | 'radar'
  data: ChartData
}

export interface CodeNode {
  kind: 'code'
  value: string
  language?: string
}

export interface ImageNode {
  kind: 'image'
  src: string
  alt?: string
  width?: number
  height?: number
}

export interface TextareaNode {
  kind: 'textarea'
  id: string
  label: string
  required?: boolean
  placeholder?: string
  default?: string
}

export interface RowNode {
  kind: 'row'
  gap?: LayoutGap
  children: CustomNode[]
}

export interface ColumnNode {
  kind: 'column'
  gap?: LayoutGap
  children: CustomNode[]
}

export interface GridNode {
  kind: 'grid'
  columns?: 2 | 3 | 4
  gap?: LayoutGap
  children: CustomNode[]
}

export interface SectionNode {
  kind: 'section'
  title?: string
  children: CustomNode[]
}

export interface GroupNode {
  kind: 'group'
  children: CustomNode[]
}

export type CustomNode =
  | TextNode
  | HeadingNode
  | DividerNode
  | AlertNode
  | BadgeNode
  | KvNode
  | ProgressNode
  | ChartNode
  | CodeNode
  | ImageNode
  | TableNode
  | InputNode
  | SelectNode
  | CheckboxNode
  | TextareaNode
  | RowNode
  | ColumnNode
  | GridNode
  | SectionNode
  | GroupNode

export interface CustomAction extends DialogAction {
  submit?: boolean
  requireValid?: boolean
  closeOnSubmit?: boolean
}

export interface CustomDialogMeta {
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl'
  scroll?: 'auto' | 'content'
}

export interface CustomDialog extends BaseDialog {
  type: 'custom'
  schemaVersion: '1.0'
  content: CustomNode[]
  actions?: CustomAction[]
  meta?: CustomDialogMeta
}

export type DialogData =
  | ConfirmDialog
  | WaitDialog
  | ChartDialog
  | NotificationDialog
  | FormDialog
  | ApprovalDialog
  | ProgressDialog
  | CustomDialog

export interface DialogValidationError {
  fieldId?: string
  message: string
}

export interface DialogRespondMeta {
  close?: boolean
  valid?: boolean
  errors?: DialogValidationError[]
}

export interface DialogResponse {
  id: string
  action: string
  data?: unknown
  valid?: boolean
  errors?: DialogValidationError[]
}

export interface WsMessage {
  event: 'dialog:open' | 'dialog:close'
  data: DialogData | { id: string }
}
