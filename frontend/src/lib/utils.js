import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { getDateLocale, t as translate } from '@/i18n/manager'

export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

export function formatBytes(bytes = 0) {
  if (bytes === 0) {
    return '0 B'
  }

  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const exponent = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  const value = bytes / 1024 ** exponent

  return `${value >= 10 || exponent === 0 ? value.toFixed(0) : value.toFixed(1)} ${units[exponent]}`
}

export function formatDate(dateValue, language) {
  return new Intl.DateTimeFormat(getDateLocale(language), {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(new Date(dateValue))
}

export function getFileTypeLabel(item, t = translate) {
  if (item.kind === 'folder') {
    return t('common.folder')
  }

  if (!item.mimeType) {
    return t('common.file')
  }

  if (item.mimeType.startsWith('image/')) {
    return t('common.image')
  }

  if (item.mimeType === 'application/pdf') {
    return t('common.pdf')
  }

  if (item.mimeType.includes('spreadsheet') || item.mimeType.includes('excel')) {
    return t('common.table')
  }

  if (item.mimeType.includes('word') || item.mimeType.includes('document')) {
    return t('common.document')
  }

  if (item.mimeType.startsWith('text/')) {
    return t('common.text')
  }

  return t('common.file')
}

export function getInitials(value = '') {
  return value
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('')
}
