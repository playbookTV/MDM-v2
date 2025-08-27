import { useState } from 'react'
import { 
  Edit3, 
  Check, 
  X, 
  Minus, 
  Save,
  RotateCcw,
  Tag,
  Home
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { SCENE_TYPES } from '@/hooks/useScenes'
import { useReviewWorkflow } from '@/hooks/useReviews'
import type { Scene, StyleClassification, SceneObject } from '@/types/dataset'

interface AnnotationToolsProps {
  scene: Scene
  selectedObject?: SceneObject
  onObjectSelect?: (object: SceneObject | null) => void
  className?: string
}

const STYLE_CODES = [
  { code: 'contemporary', name: 'Contemporary' },
  { code: 'traditional', name: 'Traditional' },
  { code: 'modern', name: 'Modern' },
  { code: 'rustic', name: 'Rustic' },
  { code: 'industrial', name: 'Industrial' },
  { code: 'minimalist', name: 'Minimalist' },
  { code: 'bohemian', name: 'Bohemian' },
  { code: 'scandinavian', name: 'Scandinavian' },
] as const

const MATERIAL_OPTIONS = [
  'wood', 'metal', 'fabric', 'leather', 'glass', 'plastic', 'ceramic', 'stone', 'other'
] as const

export function AnnotationTools({ scene, selectedObject, onObjectSelect, className }: AnnotationToolsProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editedSceneType, setEditedSceneType] = useState(scene.scene_type || '')
  const [editedStyles, setEditedStyles] = useState<StyleClassification[]>(scene.styles || [])
  const [notes, setNotes] = useState('')
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['scene']))

  const reviewWorkflow = useReviewWorkflow(scene.id)

  const handleSaveCorrections = async () => {
    try {
      await reviewWorkflow.correctScene({
        scene_type: editedSceneType !== scene.scene_type ? editedSceneType : undefined,
        styles: JSON.stringify(editedStyles) !== JSON.stringify(scene.styles || []) ? editedStyles : undefined,
        notes: notes || undefined,
      })
      setIsEditing(false)
      setNotes('')
    } catch (error) {
      // Error handled by mutation
    }
  }

  const handleResetEdits = () => {
    setEditedSceneType(scene.scene_type || '')
    setEditedStyles(scene.styles || [])
    setNotes('')
  }

  const addStyle = (styleCode: string) => {
    if (!editedStyles.find(s => s.code === styleCode)) {
      setEditedStyles([...editedStyles, { code: styleCode, conf: 0.5 }])
    }
  }

  const removeStyle = (styleCode: string) => {
    setEditedStyles(editedStyles.filter(s => s.code !== styleCode))
  }

  const updateStyleConfidence = (styleCode: string, conf: number) => {
    setEditedStyles(editedStyles.map(s => 
      s.code === styleCode ? { ...s, conf } : s
    ))
  }

  const toggleSection = (section: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev)
      if (newSet.has(section)) {
        newSet.delete(section)
      } else {
        newSet.add(section)
      }
      return newSet
    })
  }

  const hasChanges = editedSceneType !== scene.scene_type || 
                    JSON.stringify(editedStyles) !== JSON.stringify(scene.styles || [])

  return (
    <div className={`bg-card border rounded-lg ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center space-x-2">
          <Edit3 className="h-5 w-5" />
          <h3 className="font-semibold">Annotation Tools</h3>
          {isEditing && (
            <Badge variant="default" className="text-xs">Editing</Badge>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          {isEditing ? (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setIsEditing(false)
                  handleResetEdits()
                }}
                disabled={reviewWorkflow.isSubmitting}
              >
                <X className="h-4 w-4 mr-1" />
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={handleSaveCorrections}
                disabled={reviewWorkflow.isSubmitting || !hasChanges}
              >
                <Save className="h-4 w-4 mr-1" />
                Save
              </Button>
            </>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsEditing(true)}
            >
              <Edit3 className="h-4 w-4 mr-1" />
              Edit
            </Button>
          )}
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Scene Classification Section */}
        <Collapsible 
          open={expandedSections.has('scene')} 
          onOpenChange={() => toggleSection('scene')}
        >
          <CollapsibleTrigger className="flex items-center justify-between w-full p-2 hover:bg-muted rounded">
            <div className="flex items-center space-x-2">
              <Home className="h-4 w-4" />
              <span className="font-medium">Scene Classification</span>
            </div>
            <div className="flex items-center space-x-2">
              {scene.scene_conf && (
                <Badge variant="outline" className="text-xs">
                  {(scene.scene_conf * 100).toFixed(0)}% conf
                </Badge>
              )}
            </div>
          </CollapsibleTrigger>
          
          <CollapsibleContent className="pt-2">
            <div className="space-y-3">
              {/* Scene Type */}
              <div className="space-y-2">
                <Label>Scene Type</Label>
                {isEditing ? (
                  <Select value={editedSceneType} onValueChange={setEditedSceneType}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select scene type" />
                    </SelectTrigger>
                    <SelectContent>
                      {SCENE_TYPES.map(type => (
                        <SelectItem key={type} value={type}>
                          {type.replace('_', ' ')}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <div className="flex items-center space-x-2">
                    <Badge variant="secondary">
                      {scene.scene_type?.replace('_', ' ') || 'Not classified'}
                    </Badge>
                    {scene.scene_type !== editedSceneType && (
                      <Badge variant="outline" className="text-yellow-600">
                        Changed
                      </Badge>
                    )}
                  </div>
                )}
              </div>

              {/* Styles */}
              <div className="space-y-2">
                <Label>Styles</Label>
                {isEditing ? (
                  <div className="space-y-2">
                    <Select onValueChange={addStyle}>
                      <SelectTrigger>
                        <SelectValue placeholder="Add style" />
                      </SelectTrigger>
                      <SelectContent>
                        {STYLE_CODES.map(style => (
                          <SelectItem key={style.code} value={style.code}>
                            {style.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    
                    <div className="space-y-1">
                      {editedStyles.map(style => (
                        <div key={style.code} className="flex items-center space-x-2">
                          <Badge variant="outline">{style.code}</Badge>
                          <Input
                            type="number"
                            min="0"
                            max="1"
                            step="0.1"
                            value={style.conf}
                            onChange={(e) => updateStyleConfidence(style.code, parseFloat(e.target.value))}
                            className="w-20 h-8"
                          />
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeStyle(style.code)}
                          >
                            <Minus className="h-3 w-3" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-wrap gap-1">
                    {(scene.styles || []).map(style => (
                      <Badge key={style.code} variant="outline" className="text-xs">
                        {style.code} ({(style.conf * 100).toFixed(0)}%)
                      </Badge>
                    ))}
                    {(scene.styles || []).length === 0 && (
                      <span className="text-sm text-muted-foreground">No styles detected</span>
                    )}
                  </div>
                )}
              </div>
            </div>
          </CollapsibleContent>
        </Collapsible>

        {/* Objects Section */}
        <Collapsible 
          open={expandedSections.has('objects')} 
          onOpenChange={() => toggleSection('objects')}
        >
          <CollapsibleTrigger className="flex items-center justify-between w-full p-2 hover:bg-muted rounded">
            <div className="flex items-center space-x-2">
              <Tag className="h-4 w-4" />
              <span className="font-medium">Objects</span>
            </div>
            <Badge variant="outline" className="text-xs">
              {scene.objects?.length || 0} detected
            </Badge>
          </CollapsibleTrigger>
          
          <CollapsibleContent className="pt-2">
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {scene.objects && scene.objects.length > 0 ? (
                scene.objects.map(obj => (
                  <ObjectAnnotationItem
                    key={obj.id}
                    object={obj}
                    isSelected={selectedObject?.id === obj.id}
                    onSelect={() => onObjectSelect?.(obj)}
                    onDeselect={() => onObjectSelect?.(null)}
                  />
                ))
              ) : (
                <div className="text-sm text-muted-foreground text-center py-4">
                  No objects detected in this scene
                </div>
              )}
            </div>
          </CollapsibleContent>
        </Collapsible>

        {/* Notes Section */}
        {isEditing && (
          <div className="space-y-2">
            <Label htmlFor="annotation-notes">Review Notes</Label>
            <Input
              id="annotation-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add notes about corrections made..."
            />
          </div>
        )}

        {/* Quick Actions */}
        <div className="flex items-center space-x-2 pt-2 border-t">
          <Button
            variant="default"
            size="sm"
            onClick={() => reviewWorkflow.approveScene()}
            disabled={reviewWorkflow.isSubmitting}
          >
            <Check className="h-4 w-4 mr-1" />
            Approve
          </Button>
          
          <Button
            variant="destructive"
            size="sm"
            onClick={() => reviewWorkflow.rejectScene()}
            disabled={reviewWorkflow.isSubmitting}
          >
            <X className="h-4 w-4 mr-1" />
            Reject
          </Button>

          {hasChanges && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleResetEdits}
              disabled={reviewWorkflow.isSubmitting}
            >
              <RotateCcw className="h-4 w-4 mr-1" />
              Reset
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}

// Object annotation item component
function ObjectAnnotationItem({ 
  object, 
  isSelected, 
  onSelect, 
  onDeselect 
}: {
  object: SceneObject
  isSelected: boolean
  onSelect: () => void
  onDeselect: () => void
}) {
  const [isEditing, setIsEditing] = useState(false)
  const [editedLabel, setEditedLabel] = useState(object.label)
  const [editedMaterial, setEditedMaterial] = useState(object.material || '')

  const reviewWorkflow = useReviewWorkflow()

  const handleSave = async () => {
    try {
      await reviewWorkflow.correctObject(object.id, {
        label: editedLabel !== object.label ? editedLabel : undefined,
        material: editedMaterial !== object.material ? editedMaterial : undefined,
      })
      setIsEditing(false)
    } catch (error) {
      // Error handled by mutation
    }
  }

  const getConfidenceColor = (conf: number) => {
    if (conf >= 0.8) return 'text-green-500'
    if (conf >= 0.6) return 'text-yellow-500'
    return 'text-red-500'
  }

  return (
    <div 
      className={`p-3 rounded border transition-colors cursor-pointer ${
        isSelected ? 'border-primary bg-primary/5' : 'border-border hover:bg-muted/50'
      }`}
      onClick={isSelected ? onDeselect : onSelect}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <Badge variant="secondary" className="text-xs">
            {object.label}
          </Badge>
          <span className={`text-xs font-mono ${getConfidenceColor(object.confidence)}`}>
            {(object.confidence * 100).toFixed(0)}%
          </span>
        </div>
        
        {isSelected && (
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation()
              setIsEditing(!isEditing)
            }}
          >
            <Edit3 className="h-3 w-3" />
          </Button>
        )}
      </div>

      {object.material && (
        <div className="text-xs text-muted-foreground">
          Material: {object.material} ({(object.material_conf || 0) * 100}%)
        </div>
      )}

      <div className="text-xs text-muted-foreground mt-1">
        {Math.round(object.bbox.width)}×{Math.round(object.bbox.height)} at ({Math.round(object.bbox.x)}, {Math.round(object.bbox.y)})
      </div>

      {isSelected && isEditing && (
        <div className="mt-3 pt-3 border-t space-y-2">
          <div className="grid grid-cols-2 gap-2">
            <Input
              value={editedLabel}
              onChange={(e) => setEditedLabel(e.target.value)}
              placeholder="Object label"
              className="text-xs"
            />
            
            <Select value={editedMaterial} onValueChange={setEditedMaterial}>
              <SelectTrigger className="text-xs">
                <SelectValue placeholder="Material" />
              </SelectTrigger>
              <SelectContent>
                {MATERIAL_OPTIONS.map(material => (
                  <SelectItem key={material} value={material}>
                    {material}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          <div className="flex justify-end space-x-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation()
                setIsEditing(false)
                setEditedLabel(object.label)
                setEditedMaterial(object.material || '')
              }}
            >
              <X className="h-3 w-3" />
            </Button>
            <Button
              size="sm"
              onClick={(e) => {
                e.stopPropagation()
                handleSave()
              }}
              disabled={reviewWorkflow.isSubmitting}
            >
              <Check className="h-3 w-3" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

