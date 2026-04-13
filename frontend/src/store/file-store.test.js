import { beforeEach, describe, expect, it } from 'vitest'

import { ROOT_FOLDER_ID } from '@/data/mock-data'
import { useFileStore } from '@/store/file-store'

describe('file store', () => {
  beforeEach(() => {
    window.localStorage.clear()
    useFileStore.getState().resetData()
  })

  it('moves a file into a different folder', () => {
    useFileStore.getState().moveItem({
      id: 'file-home-brief',
      parentId: 'folder-project-alpha',
    })

    const movedFile = useFileStore.getState().items.find((item) => item.id === 'file-home-brief')
    expect(movedFile?.parentId).toBe('folder-project-alpha')
  })

  it('prevents moving a folder into one of its descendants', () => {
    useFileStore.getState().moveItem({
      id: 'folder-project-alpha',
      parentId: 'folder-legal',
    })

    const folder = useFileStore.getState().items.find((item) => item.id === 'folder-project-alpha')
    expect(folder?.parentId).toBeNull()
  })

  it('allows moving an item back to root through the root folder id', () => {
    useFileStore.getState().moveItem({
      id: 'file-contract',
      parentId: ROOT_FOLDER_ID,
    })

    const movedFile = useFileStore.getState().items.find((item) => item.id === 'file-contract')
    expect(movedFile?.parentId).toBeNull()
  })
})
