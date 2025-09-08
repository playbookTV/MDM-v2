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
      data-oid="if8qah5"
    >
      {/* Header */}
      <div
        className="flex items-center justify-between p-4 border-b"
        data-oid="vjiz3:o"
      >
        <div className="flex items-center space-x-2" data-oid=".eaw.8y">
          <Edit3 className="h-5 w-5" data-oid="592ut52" />
          <h3 className="font-semibold" data-oid="bbn.cd.">
            Annotation Tools
          </h3>
          {isEditing && (
            <Badge variant="default" className="text-xs" data-oid="kvvor1-">
              Editing
            </Badge>
          )}
        </div>

        <div className="flex items-center space-x-2" data-oid="m:ydosx">
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
                data-oid="r8:jzmu"
              >
                <X className="h-4 w-4 mr-1" data-oid="xe_ikpz" />
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={handleSaveCorrections}
                disabled={reviewWorkflow.isSubmitting || !hasChanges}
                data-oid="nmeqzwv"
              >
                <Save className="h-4 w-4 mr-1" data-oid="9xx6e64" />
                Save
              </Button>
            </>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsEditing(true)}
              data-oid="eav.bp0"
            >
              <Edit3 className="h-4 w-4 mr-1" data-oid="k.pxi3-" />
              Edit
            </Button>
          )}
        </div>
      </div>

      <div className="p-4 space-y-4" data-oid="3wyhe9e">
        {/* Scene Classification Section */}
        <Collapsible
          open={expandedSections.has("scene")}
          onOpenChange={() => toggleSection("scene")}
          data-oid="5765lop"
        >
          <CollapsibleTrigger
            className="flex items-center justify-between w-full p-2 hover:bg-muted rounded"
            data-oid="uo9c01:"
          >
            <div className="flex items-center space-x-2" data-oid="d:sj2tv">
              <Home className="h-4 w-4" data-oid="e_xlesw" />
              <span className="font-medium" data-oid="t4j.jb8">
                Scene Classification
              </span>
            </div>
            <div className="flex items-center space-x-2" data-oid="iu6zfmy">
              {scene.scene_conf && (
                <Badge variant="outline" className="text-xs" data-oid="hb:06s2">
                  {(scene.scene_conf * 100).toFixed(0)}% conf
                </Badge>
              )}
            </div>
          </CollapsibleTrigger>

          <CollapsibleContent className="pt-2" data-oid="z8s92b_">
            <div className="space-y-3" data-oid="16xlg7y">
              {/* Scene Type */}
              <div className="space-y-2" data-oid="kn-e8rt">
                <Label data-oid="yaokred">Scene Type</Label>
                {isEditing ? (
                  <Select
                    value={editedSceneType}
                    onValueChange={setEditedSceneType}
                    data-oid="xlyjxhi"
                  >
                    <SelectTrigger data-oid="u9sxel_">
                      <SelectValue
                        placeholder="Select scene type"
                        data-oid="0eo3297"
                      />
                    </SelectTrigger>
                    <SelectContent data-oid="5xmalf.">
                      {SCENE_TYPES.map((type) => (
                        <SelectItem key={type} value={type} data-oid="2gq3pnf">
                          {type.replace("_", " ")}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <div
                    className="flex items-center space-x-2"
                    data-oid="85d87cw"
                  >
                    <Badge variant="secondary" data-oid="aq:b0df">
                      {scene.scene_type?.replace("_", " ") || "Not classified"}
                    </Badge>
                    {scene.scene_type !== editedSceneType && (
                      <Badge
                        variant="outline"
                        className="text-yellow-600"
                        data-oid="cd7tfh:"
                      >
                        Changed
                      </Badge>
                    )}
                  </div>
                )}
              </div>

              {/* Styles */}
              <div className="space-y-2" data-oid="o5fuhum">
                <Label data-oid="73uy92i">Styles</Label>
                {isEditing ? (
                  <div className="space-y-2" data-oid="kbjkjme">
                    <Select onValueChange={addStyle} data-oid="-j7_q2o">
                      <SelectTrigger data-oid="mvrc5xk">
                        <SelectValue
                          placeholder="Add style"
                          data-oid="_tbawn5"
                        />
                      </SelectTrigger>
                      <SelectContent data-oid="2mja0p0">
                        {STYLE_CODES.map((style) => (
                          <SelectItem
                            key={style.code}
                            value={style.code}
                            data-oid="bpz9ocf"
                          >
                            {style.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>

                    <div className="space-y-1" data-oid="5ll_lmm">
                      {editedStyles.map((style) => (
                        <div
                          key={style.code}
                          className="flex items-center space-x-2"
                          data-oid="p--ddpw"
                        >
                          <Badge variant="outline" data-oid="g6t6vzm">
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
                            data-oid="d9yboi0"
                          />

                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeStyle(style.code)}
                            data-oid="-ohno98"
                          >
                            <Minus className="h-3 w-3" data-oid=":gjffc6" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-wrap gap-1" data-oid="zv8m.oo">
                    {(scene.styles || []).map((style) => (
                      <Badge
                        key={style.code}
                        variant="outline"
                        className="text-xs"
                        data-oid="vvc.k9w"
                      >
                        {style.code} ({(style.conf * 100).toFixed(0)}%)
                      </Badge>
                    ))}
                    {(scene.styles || []).length === 0 && (
                      <span
                        className="text-sm text-muted-foreground"
                        data-oid="47q0enp"
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
          data-oid="8ya0ryc"
        >
          <CollapsibleTrigger
            className="flex items-center justify-between w-full p-2 hover:bg-muted rounded"
            data-oid="766z5-t"
          >
            <div className="flex items-center space-x-2" data-oid="x_1s6lj">
              <Tag className="h-4 w-4" data-oid="1w0g:wj" />
              <span className="font-medium" data-oid="5iq5mni">
                Objects
              </span>
            </div>
            <Badge variant="outline" className="text-xs" data-oid="60ue5s9">
              {scene.objects?.length || 0} detected
            </Badge>
          </CollapsibleTrigger>

          <CollapsibleContent className="pt-2" data-oid="euudsz2">
            <div
              className="space-y-2 max-h-48 overflow-y-auto"
              data-oid="em16tj5"
            >
              {scene.objects && scene.objects.length > 0 ? (
                scene.objects.map((obj) => (
                  <ObjectAnnotationItem
                    key={obj.id}
                    object={obj}
                    isSelected={selectedObject?.id === obj.id}
                    onSelect={() => onObjectSelect?.(obj)}
                    onDeselect={() => onObjectSelect?.(null)}
                    data-oid="14pgpwy"
                  />
                ))
              ) : (
                <div
                  className="text-sm text-muted-foreground text-center py-4"
                  data-oid="bb-h-qu"
                >
                  No objects detected in this scene
                </div>
              )}
            </div>
          </CollapsibleContent>
        </Collapsible>

        {/* Notes Section */}
        {isEditing && (
          <div className="space-y-2" data-oid="7u1y_w_">
            <Label htmlFor="annotation-notes" data-oid="7rhtcc-">
              Review Notes
            </Label>
            <Input
              id="annotation-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add notes about corrections made..."
              data-oid="f.xu2eu"
            />
          </div>
        )}

        {/* Quick Actions */}
        <div
          className="flex items-center space-x-2 pt-2 border-t"
          data-oid="ur5.:74"
        >
          <Button
            variant="default"
            size="sm"
            onClick={() => reviewWorkflow.approveScene()}
            disabled={reviewWorkflow.isSubmitting}
            data-oid="6bj6l4m"
          >
            <Check className="h-4 w-4 mr-1" data-oid="2gzcxyn" />
            Approve
          </Button>

          <Button
            variant="destructive"
            size="sm"
            onClick={() => reviewWorkflow.rejectScene()}
            disabled={reviewWorkflow.isSubmitting}
            data-oid="4zevv_q"
          >
            <X className="h-4 w-4 mr-1" data-oid="7ddeil." />
            Reject
          </Button>

          {hasChanges && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleResetEdits}
              disabled={reviewWorkflow.isSubmitting}
              data-oid="uyx3pun"
            >
              <RotateCcw className="h-4 w-4 mr-1" data-oid="080z-ws" />
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
      data-oid="i-4pi9l"
    >
      <div
        className="flex items-center justify-between mb-2"
        data-oid="h--r6ua"
      >
        <div className="flex items-center space-x-2" data-oid="-.drx_a">
          <Badge variant="secondary" className="text-xs" data-oid="08ctfmv">
            {object.label}
          </Badge>
          <span
            className={`text-xs font-mono ${getConfidenceColor(object.confidence)}`}
            data-oid="l06be5x"
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
            data-oid="0em0.us"
          >
            <Edit3 className="h-3 w-3" data-oid="wp3foyk" />
          </Button>
        )}
      </div>

      {object.material && (
        <div className="text-xs text-muted-foreground" data-oid="i2dtu5i">
          Material: {object.material} ({(object.material_conf || 0) * 100}%)
        </div>
      )}

      {(object.bbox &&
        typeof object.bbox.x === "number" &&
        typeof object.bbox.y === "number" &&
        typeof object.bbox.width === "number" &&
        typeof object.bbox.height === "number") ? (
        <div className="text-xs text-muted-foreground mt-1" data-oid="..76z6e">
          {Math.round(object.bbox.width)}×{Math.round(object.bbox.height)} at (
          {Math.round(object.bbox.x)}, {Math.round(object.bbox.y)})
        </div>
      ) : (
        <div className="text-xs text-muted-foreground mt-1" data-oid="..76z6e">
          Bounding box: N/A
        </div>
      )}

      {isSelected && isEditing && (
        <div className="mt-3 pt-3 border-t space-y-2" data-oid="8xwaeom">
          <div className="grid grid-cols-2 gap-2" data-oid="crfappj">
            <Input
              value={editedLabel}
              onChange={(e) => setEditedLabel(e.target.value)}
              placeholder="Object label"
              className="text-xs"
              data-oid="vnp9ik4"
            />

            <Select
              value={editedMaterial}
              onValueChange={setEditedMaterial}
              data-oid="lxm7.7x"
            >
              <SelectTrigger className="text-xs" data-oid="u.-3lyd">
                <SelectValue placeholder="Material" data-oid="fp_wjy2" />
              </SelectTrigger>
              <SelectContent data-oid="3jr614w">
                {MATERIAL_OPTIONS.map((material) => (
                  <SelectItem
                    key={material}
                    value={material}
                    data-oid="21:a-:r"
                  >
                    {material}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex justify-end space-x-1" data-oid="_jjtkiy">
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                setIsEditing(false);
                setEditedLabel(object.label);
                setEditedMaterial(object.material || "");
              }}
              data-oid="jo0bs23"
            >
              <X className="h-3 w-3" data-oid="08g2pfl" />
            </Button>
            <Button
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                handleSave();
              }}
              disabled={reviewWorkflow.isSubmitting}
              data-oid="01n:7a4"
            >
              <Check className="h-3 w-3" data-oid="qek_8_m" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
