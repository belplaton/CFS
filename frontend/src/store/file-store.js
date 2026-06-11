import { create } from 'zustand'
import { persist } from 'zustand/middleware'

import client from '@/api/client'
import { ROOT_FOLDER_ID } from '@/lib/files-constants'

function normalizeParentId(parentId) {
  return parentId ?? null
}

function toFolderParam(folderId) {
  return folderId === ROOT_FOLDER_ID ? null : folderId
}

function derivePreviewType(mimeType) {
  if (!mimeType) {
    return 'generic'
  }

  if (mimeType.startsWith('image/')) {
    return 'image'
  }

  if (mimeType === 'application/pdf') {
    return 'pdf'
  }

  if (
    mimeType.includes('document')
    || mimeType.includes('word')
    || mimeType.includes('spreadsheet')
    || mimeType.includes('excel')
  ) {
    return 'document'
  }

  if (mimeType.startsWith('text/')) {
    return 'text'
  }

  return 'generic'
}

function normalizeItem(item) {
  const mimeType = item.mime_type ?? null
  const createdAt = item.created_at ?? item.deleted_at ?? new Date().toISOString()
  const updatedAt = item.updated_at ?? item.deleted_at ?? createdAt

  return {
    id: String(item.id),
    kind: item.kind,
    name: item.name,
    size: item.size ?? 0,
    mimeType,
    parentId: normalizeParentId(item.parent_id ?? item.original_parent_id),
    createdAt,
    updatedAt,
    deletedAt: item.deleted_at ?? null,
    preview: derivePreviewType(mimeType),
  }
}

async function downloadFileBlob(fileId) {
  const response = await client.get(`/files/${fileId}/download`, {
    responseType: 'blob',
  })
  return response.data
}

async function loadFolderListing(folderId) {
  const params = {
    limit: 200,
  }
  const apiFolderId = toFolderParam(folderId)
  if (apiFolderId) {
    params.folder_id = apiFolderId
  }

  const response = await client.get('/files/', { params })
  return [
    ...response.data.folders.map(normalizeItem),
    ...response.data.files.map(normalizeItem),
  ]
}

async function loadSearchResults(query) {
  const response = await client.get('/search/', {
    params: { q: query },
  })

  return {
    items: response.data.results.map(normalizeItem),
    total: response.data.total ?? 0,
    query: response.data.query ?? query,
  }
}

async function collectFolders(parentId = null, accumulator = [], seen = new Set()) {
  const response = await client.get('/folders/', {
    params: { parent_id: parentId ?? undefined, limit: 200, offset: 0 },
  })
  const folders = response.data.map(normalizeItem)

  for (const folder of folders) {
    if (seen.has(folder.id)) {
      continue
    }
    seen.add(folder.id)
    accumulator.push(folder)
    await collectFolders(folder.id, accumulator, seen)
  }

  return accumulator
}

function collectDescendantIds(items, itemId) {
  const children = items.filter((item) => item.parentId === itemId)
  return children.reduce(
    (accumulator, child) => [...accumulator, child.id, ...collectDescendantIds(items, child.id)],
    [],
  )
}

function canMoveItem(items, id, parentId) {
  const item = items.find((entry) => entry.id === id)
  const normalizedParentId = parentId === ROOT_FOLDER_ID ? null : parentId

  if (!item) {
    return false
  }

  if (item.parentId === normalizedParentId) {
    return false
  }

  if (item.kind !== 'folder') {
    return true
  }

  if (item.id === parentId) {
    return false
  }

  const descendantIds = collectDescendantIds(items, item.id)
  return !descendantIds.includes(parentId)
}

const initialState = {
  items: [],
  allFolders: [],
  trashItems: [],
  searchResults: [],
  searchTotal: 0,
  quota: { used: 0, total: 0, percent: 0 },
  currentFolderId: ROOT_FOLDER_ID,
  searchQuery: '',
  sortBy: 'updatedAt',
  view: 'list',
  previewItemId: null,
  isLoading: false,
  isTrashLoading: false,
  isSearching: false,
  isMutating: false,
  error: null,
  fileError: null,
  trashError: null,
}

export const useFileStore = create(
  persist(
    (set, get) => ({
      ...initialState,

      clearError: () => set({ error: null, fileError: null, trashError: null }),

      setSearchQuery: (searchQuery) => set({ searchQuery }),
      setSortBy: (sortBy) => set({ sortBy }),
      setView: (view) => set({ view }),
      openPreview: (id) => set({ previewItemId: id }),
      closePreview: () => set({ previewItemId: null }),

      clearSearch: () => set({ searchQuery: '', searchResults: [], searchTotal: 0, isSearching: false }),

      searchItems: async (query) => {
        const normalizedQuery = query.trim()

        if (!normalizedQuery) {
          set({ searchResults: [], searchTotal: 0, isSearching: false, fileError: null })
          return []
        }

        set({ isSearching: true, fileError: null })
        try {
          const result = await loadSearchResults(normalizedQuery)
          if (get().searchQuery.trim() !== normalizedQuery) {
            return result.items
          }

          set({
            searchResults: result.items,
            searchTotal: result.total,
            isSearching: false,
          })
          return result.items
        } catch (error) {
          set({
            isSearching: false,
            fileError: error.response?.data?.detail || 'Unable to search files',
          })
          return []
        }
      },

      refreshQuota: async () => {
        try {
          const response = await client.get('/files/quota')
          set({ quota: response.data })
          return response.data
        } catch (error) {
          return null
        }
      },

      refreshFolderTree: async () => {
        try {
          const allFolders = await collectFolders()
          set({ allFolders })
          return allFolders
        } catch (error) {
          return []
        }
      },

      loadFolder: async (folderId = get().currentFolderId) => {
        set({ isLoading: true, fileError: null })
        try {
          const items = await loadFolderListing(folderId)
          set({
            items,
            currentFolderId: folderId,
            isLoading: false,
            fileError: null,
          })
          return items
        } catch (error) {
          set({
            isLoading: false,
            fileError: error.response?.data?.detail || 'Unable to load files',
          })
          return []
        }
      },

      fetchTrash: async () => {
        set({ isTrashLoading: true, trashError: null })
        try {
          const response = await client.get('/trash/')
          const payload = Array.isArray(response.data)
            ? response.data
            : Array.isArray(response.data?.items)
              ? response.data.items
              : []
          const trashItems = payload.map(normalizeItem)
          set({ trashItems, isTrashLoading: false, trashError: null })
          return trashItems
        } catch (error) {
          set({
            isTrashLoading: false,
            trashError: error.response?.data?.detail || 'Unable to load trash',
          })
          return []
        }
      },

      bootstrap: async () => {
        await Promise.all([
          get().refreshFolderTree(),
          get().refreshQuota(),
          get().fetchTrash(),
          get().loadFolder(get().currentFolderId || ROOT_FOLDER_ID),
        ])
      },

      openFolder: async (folderId) => {
        await get().loadFolder(folderId)
      },

      goToRoot: async () => {
        await get().loadFolder(ROOT_FOLDER_ID)
      },

      createFolder: async ({ name, parentId }) => {
        set({ isMutating: true, fileError: null })
        try {
          await client.post('/folders/', {
            name,
            parent_id: toFolderParam(parentId),
          })
          await Promise.all([
            get().refreshFolderTree(),
            get().searchQuery.trim()
              ? get().searchItems(get().searchQuery)
              : get().loadFolder(get().currentFolderId),
          ])
          return true
        } catch (error) {
          set({ fileError: error.response?.data?.detail || 'Unable to create folder' })
          return false
        } finally {
          set({ isMutating: false })
        }
      },

      uploadFiles: async (files, parentId) => {
        if (!files.length) {
          return
        }

        set({ isMutating: true, fileError: null })
        try {
          for (const file of files) {
            const formData = new FormData()
            formData.append('file', file)
            const apiFolderId = toFolderParam(parentId)
            await client.post('/files/upload', formData, {
              params: { folder_id: apiFolderId ?? undefined },
              headers: { 'Content-Type': 'multipart/form-data' },
            })
          }
          await Promise.all([
            get().refreshQuota(),
            get().searchQuery.trim()
              ? get().searchItems(get().searchQuery)
              : get().loadFolder(get().currentFolderId),
          ])
        } catch (error) {
          set({ fileError: error.response?.data?.detail || 'Unable to upload files' })
        } finally {
          set({ isMutating: false })
        }
      },

      renameItem: async ({ id, kind, name }) => {
        set({ isMutating: true, fileError: null })
        try {
          if (kind === 'folder') {
            await client.patch(`/folders/${id}`, { name })
            await get().refreshFolderTree()
          } else {
            await client.patch(`/files/${id}/rename`, { name })
          }
          if (get().searchQuery.trim()) {
            await get().searchItems(get().searchQuery)
          } else {
            await get().loadFolder(get().currentFolderId)
          }
        } catch (error) {
          set({ fileError: error.response?.data?.detail || 'Unable to rename item' })
        } finally {
          set({ isMutating: false })
        }
      },

      moveItem: async ({ id, kind, parentId }) => {
        set({ isMutating: true, fileError: null })
        try {
          const targetParentId = toFolderParam(parentId)
          if (kind === 'folder') {
            await client.patch(`/folders/${id}`, { parent_id: targetParentId })
            await get().refreshFolderTree()
          } else {
            await client.post(`/files/${id}/move`, { folder_id: targetParentId })
          }
          if (get().searchQuery.trim()) {
            await get().searchItems(get().searchQuery)
          } else {
            await get().loadFolder(get().currentFolderId)
          }
        } catch (error) {
          set({ fileError: error.response?.data?.detail || 'Unable to move item' })
        } finally {
          set({ isMutating: false })
        }
      },

      moveItems: async ({ items, parentId }) => {
        set({ isMutating: true, fileError: null })
        try {
          const targetParentId = toFolderParam(parentId)
          for (const item of items) {
            if (item.kind === 'folder') {
              await client.patch(`/folders/${item.id}`, { parent_id: targetParentId })
            } else {
              await client.post(`/files/${item.id}/move`, { folder_id: targetParentId })
            }
          }
          await Promise.all([
            get().refreshFolderTree(),
            get().searchQuery.trim()
              ? get().searchItems(get().searchQuery)
              : get().loadFolder(get().currentFolderId),
          ])
        } catch (error) {
          set({ fileError: error.response?.data?.detail || 'Unable to move selection' })
        } finally {
          set({ isMutating: false })
        }
      },

      moveToTrash: async (item) => {
        set({ isMutating: true, fileError: null })
        try {
          if (item.kind === 'folder') {
            await client.delete(`/folders/${item.id}`)
          } else {
            await client.delete(`/files/${item.id}`)
          }
          await Promise.all([
            get().refreshFolderTree(),
            get().fetchTrash(),
            get().searchQuery.trim()
              ? get().searchItems(get().searchQuery)
              : get().loadFolder(get().currentFolderId),
          ])
        } catch (error) {
          set({ fileError: error.response?.data?.detail || 'Unable to move item to trash' })
        } finally {
          set({ isMutating: false })
        }
      },

      moveItemsToTrash: async (items) => {
        set({ isMutating: true, fileError: null })
        try {
          for (const item of items) {
            if (item.kind === 'folder') {
              await client.delete(`/folders/${item.id}`)
            } else {
              await client.delete(`/files/${item.id}`)
            }
          }
          await Promise.all([
            get().refreshFolderTree(),
            get().fetchTrash(),
            get().searchQuery.trim()
              ? get().searchItems(get().searchQuery)
              : get().loadFolder(get().currentFolderId),
          ])
        } catch (error) {
          set({ fileError: error.response?.data?.detail || 'Unable to move selection to trash' })
        } finally {
          set({ isMutating: false })
        }
      },

      restoreItem: async (id) => {
        set({ isMutating: true, error: null, trashError: null })
        try {
          await client.post(`/trash/${id}/restore`)
          await Promise.all([
            get().refreshFolderTree(),
            get().fetchTrash(),
            get().searchQuery.trim()
              ? get().searchItems(get().searchQuery)
              : get().loadFolder(get().currentFolderId),
          ])
        } catch (error) {
          const message = error.response?.data?.detail || 'Unable to restore item'
          set({ error: message, trashError: message })
        } finally {
          set({ isMutating: false })
        }
      },

      deletePermanent: async (id) => {
        set({ isMutating: true, error: null, trashError: null })
        try {
          await client.delete(`/trash/${id}/permanent`)
          await Promise.all([
            get().refreshQuota(),
            get().fetchTrash(),
            get().refreshFolderTree(),
            get().searchQuery.trim()
              ? get().searchItems(get().searchQuery)
              : get().loadFolder(get().currentFolderId),
          ])
        } catch (error) {
          const message = error.response?.data?.detail || 'Unable to delete item permanently'
          set({ error: message, trashError: message })
        } finally {
          set({ isMutating: false })
        }
      },

      emptyTrash: async () => {
        set({ isMutating: true, error: null, trashError: null })
        try {
          await client.post('/trash/empty')
          await Promise.all([
            get().refreshQuota(),
            get().fetchTrash(),
            get().refreshFolderTree(),
            get().searchQuery.trim()
              ? get().searchItems(get().searchQuery)
              : get().loadFolder(get().currentFolderId),
          ])
        } catch (error) {
          const message = error.response?.data?.detail || 'Unable to empty trash'
          set({ error: message, trashError: message })
        } finally {
          set({ isMutating: false })
        }
      },

      downloadItem: async (item) => {
        if (!item || item.kind !== 'file') {
          return
        }

        try {
          const blob = await downloadFileBlob(item.id)
          const url = window.URL.createObjectURL(blob)
          const link = document.createElement('a')
          link.href = url
          link.download = item.name
          document.body.appendChild(link)
          link.click()
          link.remove()
          window.URL.revokeObjectURL(url)
        } catch (error) {
          set({ fileError: error.response?.data?.detail || 'Unable to download file' })
        }
      },

      resetData: () => set({ ...initialState }),
    }),
    {
      name: 'cfs-file-store',
      version: 3,
      partialize: (state) => ({
        searchQuery: state.searchQuery,
        sortBy: state.sortBy,
        view: state.view,
      }),
    },
  ),
)

export function getUsedBytes() {
  return useFileStore.getState().quota.used
}

export function getDescendantIds(itemId) {
  const items = useFileStore.getState().allFolders
  return collectDescendantIds(items, itemId)
}

export function canMoveItemToParent(id, parentId) {
  const state = useFileStore.getState()
  const items = [...state.allFolders, ...state.items.filter((item) => item.kind === 'file')]
  return canMoveItem(items, id, parentId)
}
