export interface DialogOption {
  id: string
  label: string
  description?: string
}

export interface DialogAction {
  id: string
  label: string
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost'
}

export interface BaseDialog {
  id: string
  type: 'confirm' | 'wait' | 'chart' | 'notification' | 'form' | 'approval' | 'progress'
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

export type DialogData =
  | ConfirmDialog
  | WaitDialog
  | ChartDialog
  | NotificationDialog
  | FormDialog
  | ApprovalDialog
  | ProgressDialog

export interface DialogResponse {
  id: string
  action: string
  data?: unknown
}

export interface WsMessage {
  event: 'dialog:open' | 'dialog:close'
  data: DialogData | { id: string }
}
