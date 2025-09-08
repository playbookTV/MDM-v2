import { useState } from "react";
import {
  Edit3,
  Check,
  X,
  Minus,
  Save,
  RotateCcw,
  Tag,
  Home,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { SCENE_TYPES } from "@/hooks/useScenes";
import { useReviewWorkflow } from "@/hooks/useReviews";
import type { Scene, StyleClassification, SceneObject } from "@/types/dataset";

interface AnnotationToolsProps {
  scene: Scene;
  selectedObject?: SceneObject;
  onObjectSelect?: (object: SceneObject | null) => void;
  className?: string;
}

const STYLE_CODES = [
  { code: "contemporary", name: "Contemporary" },
  { code: "traditional", name: "Traditional" },
  { code: "modern", name: "Modern" },
  { code: "rustic", name: "Rustic" },
  { code: "industrial", name: "Industrial" },
  { code: "minimalist", name: "Minimalist" },
  { code: "bohemian", name: "Bohemian" },
  { code: "scandinavian", name: "Scandinavian" },
] as const;

const MATERIAL_OPTIONS = [
  "wood",
  "metal",
  "fabric",
  "leather",
  "glass",
  "plastic",
  "ceramic",
  "stone",
  "other",
] as const;

export function AnnotationTools({
  scene,
  selectedObject,
  onObjectSelect,
  className,
}: AnnotationToolsProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedSceneType, setEditedSceneType] = useState(
    scene.scene_type || "",
  );
  const [editedStyles, setEditedStyles] = useState<StyleClassification[]>(
    scene.styles || [],
  );
  const [notes, setNotes] = useState("");
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(["scene"]),
  );

  const reviewWorkflow = useReviewWorkflow(scene.id);

  const handleSaveCorrections = async () => {
    try {
      await reviewWorkflow.correctScene({
        scene_type:
          editedSceneType !== scene.scene_type ? editedSceneType : undefined,
        styles:
          JSON.stringify(editedStyles) !== JSON.stringify(scene.styles || [])
            ? editedStyles
            : undefined,
        notes: notes || undefined,
      });
      setIsEditing(false);
      setNotes("");
    } catch (error) {
      // Error handled by mutation
    }
  };

  const handleResetEdits = () => {
    setEditedSceneType(scene.scene_type || "");
    setEditedStyles(scene.styles || []);
    setNotes("");
  };

  const addStyle = (styleCode: string) => {
    if (!editedStyles.find((s) => s.code === styleCode)) {
      setEditedStyles([...editedStyles, { code: styleCode, conf: 0.5 }]);
    }
  };

  const removeStyle = (styleCode: string) => {
    setEditedStyles(editedStyles.filter((s) => s.code !== styleCode));
  };

  const updateStyleConfidence = (styleCode: string, conf: number) => {
    setEditedStyles(
      editedStyles.map((s) => (s.code === styleCode ? { ...s, conf } : s)),
    );
  };

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(section)) {
        newSet.delete(section);
      } else {
        newSet.add(section);
      }
      return newSet;
    });
  };

  const hasChanges =
    editedSceneType !== scene.scene_type ||
    JSON.stringify(editedStyles) !== JSON.stringify(scene.styles || []);

  return (
    <div
      className={`bg-card border rounded-lg ${className}`}
      data-oid="5usv15b"
    >
      {/* Header */}
      <div
        className="flex items-center justify-between p-4 border-b"
        data-oid="35a:h83"
      >
        <div className="flex items-center space-x-2" data-oid="z2r8iuv">
          <Edit3 className="h-5 w-5" data-oid="t.h68:e" />
          <h3 className="font-semibold" data-oid="1en9h4w">
            Annotation Tools
          </h3>
          {isEditing && (
            <Badge variant="default" className="text-xs" data-oid="y7hvli.">
              Editing
            </Badge>
          )}
        </div>

        <div className="flex items-center space-x-2" data-oid="nl3gkdv">
          {isEditing ? (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setIsEditing(false);
                  handleResetEdits();
                }}
                disabled={reviewWorkflow.isSubmitting}
                data-oid="9ivxdhv"
              >
                <X className="h-4 w-4 mr-1" data-oid=".5rwkjv" />
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={handleSaveCorrections}
                disabled={reviewWorkflow.isSubmitting || !hasChanges}
                data-oid="5-5hoqt"
              >
                <Save className="h-4 w-4 mr-1" data-oid="p30.97v" />
                Save
              </Button>
            </>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsEditing(true)}
              data-oid="my:94n9"
            >
              <Edit3 className="h-4 w-4 mr-1" data-oid="df9k7j5" />
              Edit
            </Button>
          )}
        </div>
      </div>

      <div className="p-4 space-y-4" data-oid="-.nngiw">
        {/* Scene Classification Section */}
        <Collapsible
          open={expandedSections.has("scene")}
          onOpenChange={() => toggleSection("scene")}
          data-oid="4rfq.pq"
        >
          <CollapsibleTrigger
            className="flex items-center justify-between w-full p-2 hover:bg-muted rounded"
            data-oid="__6llo-"
          >
            <div className="flex items-center space-x-2" data-oid="y9jvoes">
              <Home className="h-4 w-4" data-oid="flw_wj." />
              <span className="font-medium" data-oid="q7lztu8">
                Scene Classification
              </span>
            </div>
            <div className="flex items-center space-x-2" data-oid="ospegiy">
              {scene.scene_conf && (
                <Badge variant="outline" className="text-xs" data-oid="35mzrhx">
                  {(scene.scene_conf * 100).toFixed(0)}% conf
                </Badge>
              )}
            </div>
          </CollapsibleTrigger>

          <CollapsibleContent className="pt-2" data-oid="ev4nwm5">
            <div className="space-y-3" data-oid="bu5hoaz">
              {/* Scene Type */}
              <div className="space-y-2" data-oid="uzc_j9v">
                <Label data-oid="-zhl-s6">Scene Type</Label>
                {isEditing ? (
                  <Select
                    value={editedSceneType}
                    onValueChange={setEditedSceneType}
                    data-oid="j89z6j8"
                  >
                    <SelectTrigger data-oid="urg94ke">
                      <SelectValue
                        placeholder="Select scene type"
                        data-oid="7oor1gv"
                      />
                    </SelectTrigger>
                    <SelectContent data-oid="m..qq70">
                      {SCENE_TYPES.map((type) => (
                        <SelectItem key={type} value={type} data-oid="ix-55nk">
                          {type.replace("_", " ")}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <div
                    className="flex items-center space-x-2"
                    data-oid="thhzdwk"
                  >
                    <Badge variant="secondary" data-oid="os.n48k">
                      {scene.scene_type?.replace("_", " ") || "Not classified"}
                    </Badge>
                    {scene.scene_type !== editedSceneType && (
                      <Badge
                        variant="outline"
                        className="text-yellow-600"
                        data-oid="woathlh"
                      >
                        Changed
                      </Badge>
                    )}
                  </div>
                )}
              </div>

              {/* Styles */}
              <div className="space-y-2" data-oid="n9k8mod">
                <Label data-oid="5i:wq9n">Styles</Label>
                {isEditing ? (
                  <div className="space-y-2" data-oid="eugox4a">
                    <Select onValueChange={addStyle} data-oid="1-eywot">
                      <SelectTrigger data-oid="ox7iv5h">
                        <SelectValue
                          placeholder="Add style"
                          data-oid="hqa53kt"
                        />
                      </SelectTrigger>
                      <SelectContent data-oid="wlp_5gs">
                        {STYLE_CODES.map((style) => (
                          <SelectItem
                            key={style.code}
                            value={style.code}
                            data-oid="9bpfuh-"
                          >
                            {style.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>

                    <div className="space-y-1" data-oid="4.e4ogh">
                      {editedStyles.map((style) => (
                        <div
                          key={style.code}
                          className="flex items-center space-x-2"
                          data-oid="-6xkxkf"
                        >
                          <Badge variant="outline" data-oid="2r4gz9g">
                            {style.code}
                          </Badge>
                          <Input
                            type="number"
                            min="0"
                            max="1"
                            step="0.1"
                            value={style.conf}
                            onChange={(e) =>
                              updateStyleConfidence(
                                style.code,
                                parseFloat(e.target.value),
                              )
                            }
                            className="w-20 h-8"
                            data-oid="-d1.m8j"
                          />

                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeStyle(style.code)}
                            data-oid="ilkv_b1"
                          >
                            <Minus className="h-3 w-3" data-oid="lr11e8j" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-wrap gap-1" data-oid="2cjd2t6">
                    {(scene.styles || []).map((style) => (
                      <Badge
                        key={style.code}
                        variant="outline"
                        className="text-xs"
                        data-oid="o8sq-xm"
                      >
                        {style.code} ({(style.conf * 100).toFixed(0)}%)
                      </Badge>
                    ))}
                    {(scene.styles || []).length === 0 && (
                      <span
                        className="text-sm text-muted-foreground"
                        data-oid="ro_33f7"
                      >
                        No styles detected
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          </CollapsibleContent>
        </Collapsible>

        {/* Objects Section */}
        <Collapsible
          open={expandedSections.has("objects")}
          onOpenChange={() => toggleSection("objects")}
          data-oid="acj.mk."
        >
          <CollapsibleTrigger
            className="flex items-center justify-between w-full p-2 hover:bg-muted rounded"
            data-oid="0u4-idh"
          >
            <div className="flex items-center space-x-2" data-oid="sm.zoky">
              <Tag className="h-4 w-4" data-oid="q-qpr0m" />
              <span className="font-medium" data-oid="g:dc3kb">
                Objects
              </span>
            </div>
            <Badge variant="outline" className="text-xs" data-oid="qitz-gj">
              {scene.objects?.length || 0} detected
            </Badge>
          </CollapsibleTrigger>

          <CollapsibleContent className="pt-2" data-oid="cyf53e3">
            <div
              className="space-y-2 max-h-48 overflow-y-auto"
              data-oid="vumig91"
            >
              {scene.objects && scene.objects.length > 0 ? (
                scene.objects.map((obj) => (
                  <ObjectAnnotationItem
                    key={obj.id}
                    object={obj}
                    isSelected={selectedObject?.id === obj.id}
                    onSelect={() => onObjectSelect?.(obj)}
                    onDeselect={() => onObjectSelect?.(null)}
                    data-oid="-tznzay"
                  />
                ))
              ) : (
                <div
                  className="text-sm text-muted-foreground text-center py-4"
                  data-oid="uz1zv44"
                >
                  No objects detected in this scene
                </div>
              )}
            </div>
          </CollapsibleContent>
        </Collapsible>

        {/* Notes Section */}
        {isEditing && (
          <div className="space-y-2" data-oid="iiqj.-k">
            <Label htmlFor="annotation-notes" data-oid="a85tktb">
              Review Notes
            </Label>
            <Input
              id="annotation-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add notes about corrections made..."
              data-oid="l95d3wa"
            />
          </div>
        )}

        {/* Quick Actions */}
        <div
          className="flex items-center space-x-2 pt-2 border-t"
          data-oid="p:9.tno"
        >
          <Button
            variant="default"
            size="sm"
            onClick={() => reviewWorkflow.approveScene()}
            disabled={reviewWorkflow.isSubmitting}
            data-oid="hgo3.ne"
          >
            <Check className="h-4 w-4 mr-1" data-oid="s5i:0tg" />
            Approve
          </Button>

          <Button
            variant="destructive"
            size="sm"
            onClick={() => reviewWorkflow.rejectScene()}
            disabled={reviewWorkflow.isSubmitting}
            data-oid="bbpizgy"
          >
            <X className="h-4 w-4 mr-1" data-oid="0goiig0" />
            Reject
          </Button>

          {hasChanges && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleResetEdits}
              disabled={reviewWorkflow.isSubmitting}
              data-oid="c5sjiyu"
            >
              <RotateCcw className="h-4 w-4 mr-1" data-oid=".b6hglv" />
              Reset
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

// Object annotation item component
function ObjectAnnotationItem({
  object,
  isSelected,
  onSelect,
  onDeselect,
}: {
  object: SceneObject;
  isSelected: boolean;
  onSelect: () => void;
  onDeselect: () => void;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedLabel, setEditedLabel] = useState(object.label);
  const [editedMaterial, setEditedMaterial] = useState(object.material || "");

  const reviewWorkflow = useReviewWorkflow();

  const handleSave = async () => {
    try {
      await reviewWorkflow.correctObject(object.id, {
        label: editedLabel !== object.label ? editedLabel : undefined,
        material:
          editedMaterial !== object.material ? editedMaterial : undefined,
      });
      setIsEditing(false);
    } catch (error) {
      // Error handled by mutation
    }
  };

  const getConfidenceColor = (conf: number) => {
    if (conf >= 0.8) return "text-green-500";
    if (conf >= 0.6) return "text-yellow-500";
    return "text-red-500";
  };

  return (
    <div
      className={`p-3 rounded border transition-colors cursor-pointer ${
        isSelected
          ? "border-primary bg-primary/5"
          : "border-border hover:bg-muted/50"
      }`}
      onClick={isSelected ? onDeselect : onSelect}
      data-oid="zf90a9q"
    >
      <div
        className="flex items-center justify-between mb-2"
        data-oid="a:w8sgq"
      >
        <div className="flex items-center space-x-2" data-oid=".toqiad">
          <Badge variant="secondary" className="text-xs" data-oid="fpcj_ij">
            {object.label}
          </Badge>
          <span
            className={`text-xs font-mono ${getConfidenceColor(object.confidence)}`}
            data-oid="ny7au.n"
          >
            {(object.confidence * 100).toFixed(0)}%
          </span>
        </div>

        {isSelected && (
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              setIsEditing(!isEditing);
            }}
            data-oid="poyc0hu"
          >
            <Edit3 className="h-3 w-3" data-oid="p:k:f.q" />
          </Button>
        )}
      </div>

      {object.material && (
        <div className="text-xs text-muted-foreground" data-oid="nr-vo6b">
          Material: {object.material} ({(object.material_conf || 0) * 100}%)
        </div>
      )}

      <div className="text-xs text-muted-foreground mt-1" data-oid="7.jrv.6">
        {Math.round(object.bbox.width)}×{Math.round(object.bbox.height)} at (
        {Math.round(object.bbox.x)}, {Math.round(object.bbox.y)})
      </div>

      {isSelected && isEditing && (
        <div className="mt-3 pt-3 border-t space-y-2" data-oid="zyvut-j">
          <div className="grid grid-cols-2 gap-2" data-oid="04o64q-">
            <Input
              value={editedLabel}
              onChange={(e) => setEditedLabel(e.target.value)}
              placeholder="Object label"
              className="text-xs"
              data-oid="e.toasi"
            />

            <Select
              value={editedMaterial}
              onValueChange={setEditedMaterial}
              data-oid="j_ir2h5"
            >
              <SelectTrigger className="text-xs" data-oid="9_1nfzs">
                <SelectValue placeholder="Material" data-oid="8st_pgx" />
              </SelectTrigger>
              <SelectContent data-oid="42pzr_-">
                {MATERIAL_OPTIONS.map((material) => (
                  <SelectItem
                    key={material}
                    value={material}
                    data-oid=":1ta_uh"
                  >
                    {material}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex justify-end space-x-1" data-oid="fyc7deb">
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                setIsEditing(false);
                setEditedLabel(object.label);
                setEditedMaterial(object.material || "");
              }}
              data-oid="nbfxked"
            >
              <X className="h-3 w-3" data-oid="490dxzc" />
            </Button>
            <Button
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                handleSave();
              }}
              disabled={reviewWorkflow.isSubmitting}
              data-oid="1krx78v"
            >
              <Check className="h-3 w-3" data-oid="g_l1d:h" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
