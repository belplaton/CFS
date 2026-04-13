import { create } from 'zustand'
import { persist } from 'zustand/middleware'

import { createMockItems, ROOT_FOLDER_ID } from '@/data/mock-data'

function createId(prefix) {
  const uuid = globalThis.crypto?.randomUUID?.()
  return uuid ? `${prefix}-${uuid}` : `${prefix}-${Date.now()}`
}

function collectDescendantIds(items, itemId) {
  const children = items.filter((item) => item.parentId === itemId)
  return children.reduce(
    (accumulator, child) => [...accumulator, child.id, ...collectDescendantIds(items, child.id)],
    [],
  )
}

function calculateUsedBytes(items) {
  return items.reduce((total, item) => {
    if (item.kind !== 'file' || item.deletedAt) {
      return total
    }

    return total + (item.size ?? 0)
  }, 0)
}

export const useFileStore = create(
  persist(
    (set, get) => ({
      items: [],
      currentFolderId: ROOT_FOLDER_ID,
      searchQuery: '',
      sortBy: 'updatedAt',
      view: 'grid',
      previewItemId: null,
      ensureSeedData: () => {
        if (get().items.length > 0) {
          return
        }

        set({
          items: createMockItems(),
        })
      },
      setSearchQuery: (searchQuery) => set({ searchQuery }),
      setSortBy: (sortBy) => set({ sortBy }),
      setView: (view) => set({ view }),
      openFolder: (folderId) => set({ currentFolderId: folderId }),
      goToRoot: () => set({ currentFolderId: ROOT_FOLDER_ID }),
      createFolder: ({ name, parentId }) =>
        set((state) => ({
          items: [
            {
              id: createId('folder'),
              kind: 'folder',
              parentId: parentId === ROOT_FOLDER_ID ? null : parentId,
              name,
              updatedAt: new Date().toISOString(),
              accent: 'from-indigo-500 to-sky-500',
            },
            ...state.items,
          ],
        })),
      uploadFiles: (files, parentId) =>
        set((state) => ({
          items: [
            ...files.map((file) => ({
              id: createId('file'),
              kind: 'file',
              parentId: parentId === ROOT_FOLDER_ID ? null : parentId,
              name: file.name,
              size: file.size,
              mimeType: file.type || 'application/octet-stream',
              updatedAt: new Date().toISOString(),
              preview: file.type.startsWith('image/')
                ? 'image'
                : file.type === 'application/pdf'
                  ? 'pdf'
                  : file.type.startsWith('text/')
                    ? 'text'
                    : 'generic',
              accent: 'from-cyan-500 to-blue-500',
            })),
            ...state.items,
          ],
        })),
      renameItem: ({ id, name }) =>
        set((state) => ({
          items: state.items.map((item) =>
            item.id === id
              ? {
                  ...item,
                  name,
                  updatedAt: new Date().toISOString(),
                }
              : item,
          ),
        })),
      moveItem: ({ id, parentId }) =>
        set((state) => ({
          items: state.items.map((item) =>
            item.id === id
              ? {
                  ...item,
                  parentId: parentId === ROOT_FOLDER_ID ? null : parentId,
                  updatedAt: new Date().toISOString(),
                }
              : item,
          ),
        })),
      moveToTrash: (id) =>
        set((state) => {
          const ids = [id, ...collectDescendantIds(state.items, id)]
          const deletedAt = new Date().toISOString()

          return {
            items: state.items.map((item) =>
              ids.includes(item.id)
                ? {
                    ...item,
                    deletedAt,
                  }
                : item,
            ),
            currentFolderId: ids.includes(state.currentFolderId) ? ROOT_FOLDER_ID : state.currentFolderId,
            previewItemId: ids.includes(state.previewItemId) ? null : state.previewItemId,
          }
        }),
      restoreItem: (id) =>
        set((state) => {
          const ids = [id, ...collectDescendantIds(state.items, id)]

          return {
            items: state.items.map((item) =>
              ids.includes(item.id)
                ? {
                    ...item,
                    deletedAt: null,
                  }
                : item,
            ),
          }
        }),
      deletePermanent: (id) =>
        set((state) => {
          const ids = [id, ...collectDescendantIds(state.items, id)]
          return {
            items: state.items.filter((item) => !ids.includes(item.id)),
            previewItemId: ids.includes(state.previewItemId) ? null : state.previewItemId,
          }
        }),
      emptyTrash: () =>
        set((state) => ({
          items: state.items.filter((item) => !item.deletedAt),
        })),
      openPreview: (id) => set({ previewItemId: id }),
      closePreview: () => set({ previewItemId: null }),
      resetData: () =>
        set({
          items: createMockItems(),
          currentFolderId: ROOT_FOLDER_ID,
          searchQuery: '',
          sortBy: 'updatedAt',
          view: 'grid',
          previewItemId: null,
        }),
    }),
    {
      name: 'cfs-file-store',
      partialize: (state) => ({
        items: state.items,
        currentFolderId: state.currentFolderId,
        searchQuery: state.searchQuery,
        sortBy: state.sortBy,
        view: state.view,
      }),
    },
  ),
)

export function getUsedBytes() {
  return calculateUsedBytes(useFileStore.getState().items)
}

export function getDescendantIds(itemId) {
  const items = useFileStore.getState().items
  return collectDescendantIds(items, itemId)
}
