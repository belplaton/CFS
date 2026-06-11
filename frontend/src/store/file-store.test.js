import { beforeEach, describe, expect, it } from 'vitest'

import { ROOT_FOLDER_ID } from '@/lib/files-constants'
import { canMoveItemToParent, getDescendantIds, useFileStore } from '@/store/file-store'

describe('file store helpers', () => {
  beforeEach(() => {
    window.localStorage.clear()
    useFileStore.getState().resetData()
    useFileStore.setState({
      allFolders: [
        { id: 'folder-root-a', kind: 'folder', parentId: null, name: 'A' },
        { id: 'folder-child-a', kind: 'folder', parentId: 'folder-root-a', name: 'B' },
      ],
      items: [
        { id: 'file-1', kind: 'file', parentId: null, name: 'Doc.pdf', size: 10 },
      ],
    })
  })

  it('returns descendants for a folder', () => {
    expect(getDescendantIds('folder-root-a')).toEqual(['folder-child-a'])
  })

  it('prevents moving a folder into its descendant', () => {
    expect(canMoveItemToParent('folder-root-a', 'folder-child-a')).toBe(false)
  })

  it('allows moving a file back to root', () => {
    expect(canMoveItemToParent('file-1', ROOT_FOLDER_ID)).toBe(true)
  })
})
