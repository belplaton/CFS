export const ROOT_FOLDER_ID = 'root'

const hour = 60 * 60 * 1000
const day = 24 * hour
const now = new Date('2026-04-13T10:00:00.000Z').getTime()

function iso(offset) {
  return new Date(now - offset).toISOString()
}

export function createMockItems() {
  return [
    {
      id: 'folder-project-alpha',
      kind: 'folder',
      parentId: null,
      name: 'Project Alpha',
      updatedAt: iso(2 * hour),
      accent: 'from-cyan-500 to-sky-500',
    },
    {
      id: 'folder-brand',
      kind: 'folder',
      parentId: null,
      name: 'Brand Kit',
      updatedAt: iso(18 * hour),
      accent: 'from-amber-500 to-orange-500',
    },
    {
      id: 'folder-reports',
      kind: 'folder',
      parentId: null,
      name: 'Quarterly Reports',
      updatedAt: iso(3 * day),
      accent: 'from-emerald-500 to-teal-500',
    },
    {
      id: 'folder-legal',
      kind: 'folder',
      parentId: 'folder-project-alpha',
      name: 'Contracts',
      updatedAt: iso(8 * hour),
      accent: 'from-fuchsia-500 to-rose-500',
    },
    {
      id: 'file-home-brief',
      kind: 'file',
      parentId: null,
      name: 'Product-strategy.pdf',
      size: 4_280_000,
      mimeType: 'application/pdf',
      updatedAt: iso(4 * hour),
      preview: 'pdf',
      accent: 'from-red-500 to-orange-400',
    },
    {
      id: 'file-home-cover',
      kind: 'file',
      parentId: null,
      name: 'Launch-cover.png',
      size: 2_640_000,
      mimeType: 'image/png',
      updatedAt: iso(7 * hour),
      preview: 'image',
      accent: 'from-sky-500 to-cyan-400',
    },
    {
      id: 'file-alpha-plan',
      kind: 'file',
      parentId: 'folder-project-alpha',
      name: 'Sprint-plan.docx',
      size: 890_000,
      mimeType:
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      updatedAt: iso(90 * 60 * 1000),
      preview: 'document',
      accent: 'from-violet-500 to-fuchsia-400',
    },
    {
      id: 'file-alpha-wireframes',
      kind: 'file',
      parentId: 'folder-project-alpha',
      name: 'Wireframes.fig',
      size: 11_900_000,
      mimeType: 'application/octet-stream',
      updatedAt: iso(5 * hour),
      preview: 'generic',
      accent: 'from-slate-700 to-slate-500',
    },
    {
      id: 'file-contract',
      kind: 'file',
      parentId: 'folder-legal',
      name: 'Service-agreement.pdf',
      size: 1_320_000,
      mimeType: 'application/pdf',
      updatedAt: iso(11 * hour),
      preview: 'pdf',
      accent: 'from-rose-500 to-red-400',
    },
    {
      id: 'file-brand-logo',
      kind: 'file',
      parentId: 'folder-brand',
      name: 'Logo-pack.zip',
      size: 28_400_000,
      mimeType: 'application/zip',
      updatedAt: iso(28 * hour),
      preview: 'generic',
      accent: 'from-amber-400 to-orange-500',
    },
    {
      id: 'file-report-q1',
      kind: 'file',
      parentId: 'folder-reports',
      name: 'Q1-forecast.xlsx',
      size: 3_780_000,
      mimeType:
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      updatedAt: iso(2 * day),
      preview: 'document',
      accent: 'from-emerald-500 to-lime-400',
    },
    {
      id: 'file-trash-notes',
      kind: 'file',
      parentId: null,
      name: 'Old-notes.txt',
      size: 54_000,
      mimeType: 'text/plain',
      updatedAt: iso(10 * day),
      deletedAt: iso(2 * day),
      preview: 'text',
      accent: 'from-stone-500 to-zinc-400',
    },
    {
      id: 'folder-trash-archive',
      kind: 'folder',
      parentId: null,
      name: 'Archive 2025',
      updatedAt: iso(12 * day),
      deletedAt: iso(4 * day),
      accent: 'from-zinc-600 to-slate-500',
    },
  ]
}

