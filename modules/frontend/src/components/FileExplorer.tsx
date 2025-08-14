import React, { useState } from 'react'
import { 
  ChevronRight, 
  ChevronDown, 
  File, 
  Folder, 
  FolderOpen,
  Plus,
  MoreVertical,
  FileText,
  FileCode,
  Image,
  Archive
} from 'lucide-react'

interface FileNode {
  id: string
  name: string
  type: 'file' | 'folder'
  children?: FileNode[]
  expanded?: boolean
  extension?: string
}

interface FileExplorerProps {
  files: FileNode[]
  onFileSelect: (file: FileNode) => void
  selectedFileId?: string
}

const getFileIcon = (fileName: string) => {
  const ext = fileName.split('.').pop()?.toLowerCase()
  
  switch (ext) {
    case 'py':
    case 'js':
    case 'ts':
    case 'jsx':
    case 'tsx':
      return <FileCode className="h-4 w-4 text-blue-400" />
    case 'md':
    case 'txt':
      return <FileText className="h-4 w-4 text-gray-400" />
    case 'png':
    case 'jpg':
    case 'jpeg':
    case 'gif':
    case 'svg':
      return <Image className="h-4 w-4 text-green-400" />
    case 'zip':
    case 'tar':
    case 'gz':
      return <Archive className="h-4 w-4 text-yellow-400" />
    default:
      return <File className="h-4 w-4 text-gray-400" />
  }
}

export const FileExplorer: React.FC<FileExplorerProps> = ({
  files,
  onFileSelect,
  selectedFileId
}) => {
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; fileId: string } | null>(null)

  const toggleFolder = (folderId: string) => {
    const newExpanded = new Set(expandedFolders)
    if (newExpanded.has(folderId)) {
      newExpanded.delete(folderId)
    } else {
      newExpanded.add(folderId)
    }
    setExpandedFolders(newExpanded)
  }

  const handleContextMenu = (e: React.MouseEvent, fileId: string) => {
    e.preventDefault()
    setContextMenu({ x: e.clientX, y: e.clientY, fileId })
  }

  const renderFileTree = (nodes: FileNode[], level = 0) => {
    return nodes.map((node) => {
      const isExpanded = expandedFolders.has(node.id)
      const isSelected = selectedFileId === node.id
      
      return (
        <div key={node.id}>
          <div
            className={`flex items-center px-2 py-1 hover:bg-gray-700 cursor-pointer group ${
              isSelected ? 'bg-gray-700' : ''
            }`}
            style={{ paddingLeft: `${level * 16 + 8}px` }}
            onClick={() => {
              if (node.type === 'folder') {
                toggleFolder(node.id)
              } else {
                onFileSelect(node)
              }
            }}
            onContextMenu={(e) => handleContextMenu(e, node.id)}
          >
            {node.type === 'folder' ? (
              <>
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4 text-gray-400 mr-1" />
                ) : (
                  <ChevronRight className="h-4 w-4 text-gray-400 mr-1" />
                )}
                {isExpanded ? (
                  <FolderOpen className="h-4 w-4 text-yellow-500 mr-2" />
                ) : (
                  <Folder className="h-4 w-4 text-yellow-500 mr-2" />
                )}
              </>
            ) : (
              <span className="w-5" />
            )}
            
            {node.type === 'file' && getFileIcon(node.name)}
            
            <span className={`ml-2 text-sm flex-1 ${
              isSelected ? 'text-white' : 'text-gray-300'
            }`}>
              {node.name}
            </span>
            
            <button
              className="opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={(e) => {
                e.stopPropagation()
                handleContextMenu(e, node.id)
              }}
            >
              <MoreVertical className="h-4 w-4 text-gray-400" />
            </button>
          </div>
          
          {node.type === 'folder' && isExpanded && node.children && (
            <div>
              {renderFileTree(node.children, level + 1)}
            </div>
          )}
        </div>
      )
    })
  }

  return (
    <div className="h-full bg-gray-850 text-gray-300 select-none">
      {/* Header */}
      <div className="flex items-center justify-between p-2 border-b border-gray-700">
        <span className="text-xs font-semibold uppercase text-gray-400">Explorer</span>
        <button className="text-gray-400 hover:text-white">
          <Plus className="h-4 w-4" />
        </button>
      </div>
      
      {/* File Tree */}
      <div className="overflow-y-auto">
        {renderFileTree(files)}
      </div>
      
      {/* Context Menu */}
      {contextMenu && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setContextMenu(null)}
          />
          <div
            className="fixed z-50 bg-gray-800 border border-gray-700 rounded-md shadow-lg py-1 min-w-[150px]"
            style={{ left: contextMenu.x, top: contextMenu.y }}
          >
            <button className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-700">
              New File
            </button>
            <button className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-700">
              New Folder
            </button>
            <hr className="my-1 border-gray-700" />
            <button className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-700">
              Rename
            </button>
            <button className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-700">
              Delete
            </button>
          </div>
        </>
      )}
    </div>
  )
} 