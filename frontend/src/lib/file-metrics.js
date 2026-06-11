import { ROOT_FOLDER_ID } from '@/lib/files-constants'

function getParentKey(parentId) {
  return parentId ?? ROOT_FOLDER_ID
}

export function buildFolderSizeCache(items) {
  const activeItems = items.filter((item) => !item.deletedAt)
  const folders = activeItems.filter((item) => item.kind === 'folder')
  const files = activeItems.filter((item) => item.kind === 'file')

  const childrenByParent = folders.reduce((accumulator, folder) => {
    const key = getParentKey(folder.parentId)
    if (!accumulator.has(key)) {
      accumulator.set(key, [])
    }
    accumulator.get(key).push(folder.id)
    return accumulator
  }, new Map())

  const directFileSizeByParent = files.reduce((accumulator, file) => {
    const key = getParentKey(file.parentId)
    accumulator.set(key, (accumulator.get(key) ?? 0) + (file.size ?? 0))
    return accumulator
  }, new Map())

  const cache = new Map()

  function getFolderSize(folderId) {
    if (cache.has(folderId)) {
      return cache.get(folderId)
    }

    const directFilesSize = directFileSizeByParent.get(folderId) ?? 0
    const childFolders = childrenByParent.get(folderId) ?? []

    const nestedSize = childFolders.reduce((total, childFolderId) => total + getFolderSize(childFolderId), 0)
    const totalSize = directFilesSize + nestedSize

    cache.set(folderId, totalSize)
    return totalSize
  }

  folders.forEach((folder) => {
    getFolderSize(folder.id)
  })

  return cache
}

export function getFileStats(items) {
  const folderCount = items.filter((item) => item.kind === 'folder' && !item.deletedAt).length
  const fileCount = items.filter((item) => item.kind === 'file' && !item.deletedAt).length
  const trashCount = items.filter((item) => item.deletedAt).length
  const usedBytes = items.reduce((total, item) => {
    if (item.kind !== 'file' || item.deletedAt) {
      return total
    }

    return total + (item.size ?? 0)
  }, 0)

  return {
    folderCount,
    fileCount,
    trashCount,
    usedBytes,
  }
}

export function getItemEffectiveSize(item, folderSizeCache) {
  if (item.kind === 'file') {
    return item.size ?? 0
  }

  return folderSizeCache.get(item.id) ?? 0
}

export function matchesTypeFilter(item, typeFilter) {
  if (typeFilter === 'all') {
    return true
  }

  if (typeFilter === 'folders') {
    return item.kind === 'folder'
  }

  if (typeFilter === 'files') {
    return item.kind === 'file'
  }

  if (item.kind !== 'file') {
    return false
  }

  if (typeFilter === 'images') {
    return item.mimeType?.startsWith('image/')
  }

  if (typeFilter === 'pdf') {
    return item.mimeType === 'application/pdf'
  }

  if (typeFilter === 'documents') {
    return (
      item.mimeType?.includes('document')
      || item.mimeType?.includes('word')
      || item.mimeType?.includes('spreadsheet')
      || item.mimeType?.includes('excel')
      || item.mimeType?.includes('text/')
    )
  }

  if (typeFilter === 'archives') {
    return item.mimeType?.includes('zip') || item.mimeType?.includes('rar') || item.mimeType?.includes('tar')
  }

  return true
}
