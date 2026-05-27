export function formatDate(value) {
  if (!value) {
    return '--'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return '--'
  }
  return `${date.getFullYear()}.${date.getMonth() + 1}.${date.getDate()}`
}

export function formatDuration(seconds) {
  const total = Number(seconds || 0)
  if (!Number.isFinite(total) || total <= 0) {
    return '0:00'
  }
  const rounded = Math.floor(total)
  const minutes = Math.floor(rounded / 60)
  const remain = rounded % 60
  return `${minutes}:${String(remain).padStart(2, '0')}`
}

export function truncateText(value, maxLength = 16) {
  if (!value) {
    return ''
  }
  return value.length > maxLength ? `${value.slice(0, maxLength)}...` : value
}

export function getProgressPercent(currentTime, duration) {
  const total = Number(duration || 0)
  const current = Number(currentTime || 0)
  if (!Number.isFinite(total) || total <= 0 || !Number.isFinite(current) || current <= 0) {
    return 0
  }
  return Math.min(100, Math.max(0, Math.round((current / total) * 100)))
}
