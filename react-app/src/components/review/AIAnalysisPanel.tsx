import { useState } from "react";
import {
  Eye,
  Palette,
  Layers,
  BarChart3,
  ChevronDown,
  ChevronRight,
  Target,
  Settings,
  Mountain,
  Info,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { DepthMapViewer } from "./DepthMapViewer";
import { AIProcessingTrigger } from "./AIProcessingTrigger";
import type { Scene, SceneObject } from "@/types/dataset";

interface AIAnalysisPanelProps {
  scene: Scene;
  selectedObject?: SceneObject | null;
  onObjectSelect?: (object: SceneObject | null) => void;
  onProcessingComplete?: () => void;
  className?: string;
}

export function AIAnalysisPanel({
  scene,
  selectedObject,
  onObjectSelect,
  onProcessingComplete,
  className,
}: AIAnalysisPanelProps) {
  const [expandedSections, setExpandedSections] = useState({
    sceneAnalysis: true,
    objects: true,
    styles: false,
    colors: false,
    depth: false,
  });
  const [showDepthMap, setShowDepthMap] = useState(false);

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return "text-green-600";
    if (confidence >= 0.6) return "text-yellow-600";
    return "text-red-600";
  };

  const getConfidenceVariant = (confidence: number) => {
    if (confidence >= 0.8) return "default";
    if (confidence >= 0.6) return "secondary";
    return "destructive";
  };

  const formatConfidence = (confidence: number) => {
    return `${(confidence * 100).toFixed(0)}%`;
  };

  return (
    <TooltipProvider data-oid="jsmf5a_">
      <div className={`space-y-4 ${className}`} data-oid="avi4o2t">
        {/* AI Processing Trigger */}
        <AIProcessingTrigger
          scene={scene}
          onProcessingComplete={onProcessingComplete}
          data-oid="knw97:j"
        />

        {/* Scene Analysis */}
        <Card data-oid="7-56qa_">
          <Collapsible
            open={expandedSections.sceneAnalysis}
            onOpenChange={() => toggleSection("sceneAnalysis")}
            data-oid="3v8f3g2"
          >
            <CollapsibleTrigger
              className="cursor-pointer hover:bg-muted/50 transition-colors pb-3"
              data-oid="-8r:y.l"
            >
              <CardHeader data-oid="m1gz2jm">
                <CardTitle
                  className="flex items-center justify-between text-base"
                  data-oid="0a2lzch"
                >
                  <div
                    className="flex items-center space-x-2"
                    data-oid="9mixtju"
                  >
                    <Eye className="h-4 w-4" data-oid="0m8-5ad" />
                    <span data-oid="ppr_d-_">Scene Classification</span>
                  </div>
                  {expandedSections.sceneAnalysis ? (
                    <ChevronDown className="h-4 w-4" data-oid="0d2f.je" />
                  ) : (
                    <ChevronRight className="h-4 w-4" data-oid="5iwuqb1" />
                  )}
                </CardTitle>
              </CardHeader>
            </CollapsibleTrigger>
            <CollapsibleContent data-oid="5h00hvn">
              <CardContent className="pt-0" data-oid=".d-mrd0">
                {scene.scene_type ? (
                  <div className="space-y-3" data-oid="q4n36:o">
                    <div
                      className="flex items-center justify-between"
                      data-oid="1ii8dd5"
                    >
                      <Badge
                        variant="secondary"
                        className="text-sm"
                        data-oid="7gu:391"
                      >
                        {scene.scene_type
                          .replace("_", " ")
                          .replace(/\b\w/g, (l) => l.toUpperCase())}
                      </Badge>
                      <Badge
                        variant={getConfidenceVariant(scene.scene_conf || 0)}
                        className="text-xs"
                        data-oid="gluvl4j"
                      >
                        {formatConfidence(scene.scene_conf || 0)}
                      </Badge>
                    </div>

                    {scene.scene_conf && (
                      <div className="space-y-1" data-oid="5qlpjj-">
                        <div
                          className="flex justify-between text-xs text-muted-foreground"
                          data-oid="zjzx2:j"
                        >
                          <span data-oid="yj:ip13">Confidence</span>
                          <span
                            className={getConfidenceColor(scene.scene_conf)}
                            data-oid="vpuy-7z"
                          >
                            {formatConfidence(scene.scene_conf)}
                          </span>
                        </div>
                        <Progress
                          value={scene.scene_conf * 100}
                          className="h-2"
                          data-oid="8uvsn_d"
                        />
                      </div>
                    )}
                  </div>
                ) : (
                  <div
                    className="text-center py-4 text-muted-foreground"
                    data-oid="_dpa32x"
                  >
                    <Target
                      className="h-8 w-8 mx-auto mb-2 opacity-50"
                      data-oid="e_qk6p3"
                    />
                    <p className="text-sm" data-oid="gw9hib_">
                      No scene classification available
                    </p>
                  </div>
                )}
              </CardContent>
            </CollapsibleContent>
          </Collapsible>
        </Card>

        {/* Objects */}
        <Card data-oid="mdr_nrv">
          <Collapsible
            open={expandedSections.objects}
            onOpenChange={() => toggleSection("objects")}
            data-oid="-jzm5ir"
          >
            <CollapsibleTrigger
              className="cursor-pointer hover:bg-muted/50 transition-colors pb-3"
              data-oid="zi3ajnp"
            >
              <CardHeader data-oid="dk2vqxf">
                <CardTitle
                  className="flex items-center justify-between text-base"
                  data-oid="y0usprl"
                >
                  <div
                    className="flex items-center space-x-2"
                    data-oid="d:ei:oy"
                  >
                    <Layers className="h-4 w-4" data-oid="jimap5h" />
                    <span data-oid="6a262yi">Detected Objects</span>
                    <Badge
                      variant="outline"
                      className="text-xs"
                      data-oid="7_hgf0b"
                    >
                      {scene.objects?.length || 0}
                    </Badge>
                  </div>
                  {expandedSections.objects ? (
                    <ChevronDown className="h-4 w-4" data-oid="4h.ewk6" />
                  ) : (
                    <ChevronRight className="h-4 w-4" data-oid="_i1bzsp" />
                  )}
                </CardTitle>
              </CardHeader>
            </CollapsibleTrigger>
            <CollapsibleContent data-oid="fq2wba7">
              <CardContent className="pt-0" data-oid="zioizuh">
                {scene.objects && scene.objects.length > 0 ? (
                  <div
                    className="space-y-2 max-h-64 overflow-y-auto"
                    data-oid="np5f5nt"
                  >
                    {scene.objects
                      .sort((a, b) => b.confidence - a.confidence)
                      .map((object) => (
                        <div
                          key={object.id}
                          className={`p-3 rounded-lg border cursor-pointer transition-all ${
                            selectedObject?.id === object.id
                              ? "bg-primary/10 border-primary"
                              : "hover:bg-muted/50"
                          }`}
                          onClick={() =>
                            onObjectSelect?.(
                              selectedObject?.id === object.id ? null : object,
                            )
                          }
                          data-oid=":qdr97p"
                        >
                          <div
                            className="flex items-center justify-between mb-2"
                            data-oid=":ppy-sv"
                          >
                            <span
                              className="font-medium text-sm"
                              data-oid="gfeucpq"
                            >
                              {object.label}
                            </span>
                            <Badge
                              variant={getConfidenceVariant(object.confidence)}
                              className="text-xs"
                              data-oid="it0rvzl"
                            >
                              {formatConfidence(object.confidence)}
                            </Badge>
                          </div>

                          {object.material && (
                            <div
                              className="flex items-center space-x-2 text-xs text-muted-foreground"
                              data-oid="leqqopr"
                            >
                              <Settings
                                className="h-3 w-3"
                                data-oid="pqh2t1:"
                              />
                              <span data-oid="l3q-jr.">
                                {object.material}
                                {object.material_conf && (
                                  <span className="ml-1" data-oid="wjjy98f">
                                    ({formatConfidence(object.material_conf)})
                                  </span>
                                )}
                              </span>
                            </div>
                          )}

                          <div
                            className="text-xs text-muted-foreground mt-1"
                            data-oid="zfit033"
                          >
                            {Math.round(object.bbox.width)}×
                            {Math.round(object.bbox.height)} at (
                            {Math.round(object.bbox.x)},{" "}
                            {Math.round(object.bbox.y)})
                          </div>
                        </div>
                      ))}
                  </div>
                ) : (
                  <div
                    className="text-center py-4 text-muted-foreground"
                    data-oid="9khz6:c"
                  >
                    <Layers
                      className="h-8 w-8 mx-auto mb-2 opacity-50"
                      data-oid="387btja"
                    />
                    <p className="text-sm" data-oid="7sgnix-">
                      No objects detected
                    </p>
                  </div>
                )}
              </CardContent>
            </CollapsibleContent>
          </Collapsible>
        </Card>

        {/* Style Analysis */}
        <Card data-oid="injg1j0">
          <Collapsible
            open={expandedSections.styles}
            onOpenChange={() => toggleSection("styles")}
            data-oid="aws3ii9"
          >
            <CollapsibleTrigger
              className="cursor-pointer hover:bg-muted/50 transition-colors pb-3"
              data-oid="c_9iwd2"
            >
              <CardHeader data-oid="fk2sr-f">
                <CardTitle
                  className="flex items-center justify-between text-base"
                  data-oid="7j_etqk"
                >
                  <div
                    className="flex items-center space-x-2"
                    data-oid="s6ylg1c"
                  >
                    <BarChart3 className="h-4 w-4" data-oid="tbskq7w" />
                    <span data-oid="zyi7mbm">Style Analysis</span>
                    <Badge
                      variant="outline"
                      className="text-xs"
                      data-oid="gbkgltn"
                    >
                      {scene.styles?.length || 0}
                    </Badge>
                  </div>
                  {expandedSections.styles ? (
                    <ChevronDown className="h-4 w-4" data-oid="y7rqs-k" />
                  ) : (
                    <ChevronRight className="h-4 w-4" data-oid="ni:xjn7" />
                  )}
                </CardTitle>
              </CardHeader>
            </CollapsibleTrigger>
            <CollapsibleContent data-oid="xm2.4ar">
              <CardContent className="pt-0" data-oid="xwrb_ay">
                {scene.styles && scene.styles.length > 0 ? (
                  <div className="space-y-3" data-oid="09kea-9">
                    {scene.styles
                      .sort((a, b) => b.conf - a.conf)
                      .map((style) => (
                        <div
                          key={style.code}
                          className="space-y-1"
                          data-oid="ueatt-n"
                        >
                          <div
                            className="flex items-center justify-between"
                            data-oid="lnty1jl"
                          >
                            <span
                              className="text-sm font-medium capitalize"
                              data-oid="uf4vd6r"
                            >
                              {style.code.replace("_", " ")}
                            </span>
                            <span
                              className={`text-xs ${getConfidenceColor(style.conf)}`}
                              data-oid="8ivnui1"
                            >
                              {formatConfidence(style.conf)}
                            </span>
                          </div>
                          <Progress
                            value={style.conf * 100}
                            className="h-2"
                            data-oid="f8qywro"
                          />
                        </div>
                      ))}
                  </div>
                ) : (
                  <div
                    className="text-center py-4 text-muted-foreground"
                    data-oid="_9g06gj"
                  >
                    <BarChart3
                      className="h-8 w-8 mx-auto mb-2 opacity-50"
                      data-oid=".1itt5g"
                    />
                    <p className="text-sm" data-oid="3hwewn4">
                      No style analysis available
                    </p>
                  </div>
                )}
              </CardContent>
            </CollapsibleContent>
          </Collapsible>
        </Card>

        {/* Color Palette */}
        <Card data-oid="kv1f4yb">
          <Collapsible
            open={expandedSections.colors}
            onOpenChange={() => toggleSection("colors")}
            data-oid="zz:wdyn"
          >
            <CollapsibleTrigger
              className="cursor-pointer hover:bg-muted/50 transition-colors pb-3"
              data-oid="a8rc522"
            >
              <CardHeader data-oid="xhb--f9">
                <CardTitle
                  className="flex items-center justify-between text-base"
                  data-oid="65st_1p"
                >
                  <div
                    className="flex items-center space-x-2"
                    data-oid="u0-d.08"
                  >
                    <Palette className="h-4 w-4" data-oid="rv5uwsv" />
                    <span data-oid="zjxajv-">Color Palette</span>
                    <Badge
                      variant="outline"
                      className="text-xs"
                      data-oid="y9hbbpx"
                    >
                      {scene.palette?.length || 0}
                    </Badge>
                  </div>
                  {expandedSections.colors ? (
                    <ChevronDown className="h-4 w-4" data-oid="ftl67fe" />
                  ) : (
                    <ChevronRight className="h-4 w-4" data-oid="g28q95f" />
                  )}
                </CardTitle>
              </CardHeader>
            </CollapsibleTrigger>
            <CollapsibleContent data-oid="hh_xcnl">
              <CardContent className="pt-0" data-oid="_86mh4n">
                {scene.palette && scene.palette.length > 0 ? (
                  <div className="space-y-3" data-oid="fl90cjr">
                    <div className="grid grid-cols-5 gap-2" data-oid="yd22olx">
                      {scene.palette.slice(0, 5).map((color, index) => (
                        <Tooltip key={index} data-oid="k-0wimr">
                          <TooltipTrigger data-oid="_8q4eu6">
                            <div
                              className="h-10 rounded-md border-2 border-background shadow-sm cursor-pointer hover:scale-105 transition-transform"
                              style={{ backgroundColor: color.hex }}
                              data-oid="-e9c3q5"
                            />
                          </TooltipTrigger>
                          <TooltipContent data-oid=".s:zbzp">
                            <div className="text-center" data-oid="sckh_ap">
                              <div
                                className="font-mono text-sm"
                                data-oid="3galqv9"
                              >
                                {color.hex}
                              </div>
                              <div
                                className="text-xs text-muted-foreground"
                                data-oid="l_x1ci1"
                              >
                                {(color.p * 100).toFixed(1)}% coverage
                              </div>
                            </div>
                          </TooltipContent>
                        </Tooltip>
                      ))}
                    </div>

                    <div className="space-y-2" data-oid="8o5vfp7">
                      {scene.palette.slice(0, 3).map((color, index) => (
                        <div
                          key={index}
                          className="flex items-center space-x-3"
                          data-oid="r4_xg08"
                        >
                          <div
                            className="w-4 h-4 rounded border"
                            style={{ backgroundColor: color.hex }}
                            data-oid="6p_65c1"
                          />

                          <span
                            className="font-mono text-xs"
                            data-oid="dsq2om1"
                          >
                            {color.hex}
                          </span>
                          <span
                            className="text-xs text-muted-foreground ml-auto"
                            data-oid="6zoepf-"
                          >
                            {(color.p * 100).toFixed(1)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div
                    className="text-center py-4 text-muted-foreground"
                    data-oid="17ueoid"
                  >
                    <Palette
                      className="h-8 w-8 mx-auto mb-2 opacity-50"
                      data-oid="maad_y7"
                    />
                    <p className="text-sm" data-oid="o4x0ki2">
                      No color analysis available
                    </p>
                  </div>
                )}
              </CardContent>
            </CollapsibleContent>
          </Collapsible>
        </Card>

        {/* Depth Analysis */}
        <Card data-oid="bnhza0d">
          <Collapsible
            open={expandedSections.depth}
            onOpenChange={() => toggleSection("depth")}
            data-oid="7-_v8d."
          >
            <CollapsibleTrigger
              className="cursor-pointer hover:bg-muted/50 transition-colors pb-3"
              data-oid="nz1-l-_"
            >
              <CardHeader data-oid="5sj5zo.">
                <CardTitle
                  className="flex items-center justify-between text-base"
                  data-oid="i:ekah:"
                >
                  <div
                    className="flex items-center space-x-2"
                    data-oid="87h_gsj"
                  >
                    <Mountain className="h-4 w-4" data-oid="acylb7:" />
                    <span data-oid="n:7896g">Depth Analysis</span>
                    <Badge
                      variant={scene.has_depth ? "default" : "secondary"}
                      className="text-xs"
                      data-oid="12qjk5:"
                    >
                      {scene.has_depth ? "Available" : "N/A"}
                    </Badge>
                  </div>
                  {expandedSections.depth ? (
                    <ChevronDown className="h-4 w-4" data-oid="hglsrq4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" data-oid="lhc:4n-" />
                  )}
                </CardTitle>
              </CardHeader>
            </CollapsibleTrigger>
            <CollapsibleContent data-oid="42li6_q">
              <CardContent className="pt-0" data-oid="0kg5--9">
                {scene.has_depth ? (
                  <div className="space-y-3" data-oid="8itu61t">
                    <div
                      className="text-sm text-muted-foreground"
                      data-oid="2hdkr9m"
                    >
                      Depth mapping provides 3D spatial understanding of the
                      scene, enabling advanced analysis of object relationships
                      and room layout.
                    </div>

                    <Button
                      variant={showDepthMap ? "default" : "outline"}
                      size="sm"
                      className="w-full"
                      onClick={() => setShowDepthMap(!showDepthMap)}
                      data-oid="apc8_-m"
                    >
                      <Mountain className="h-4 w-4 mr-2" data-oid="-8x9j05" />
                      {showDepthMap ? "Hide" : "View"} Depth Map
                    </Button>
                  </div>
                ) : (
                  <div
                    className="text-center py-4 text-muted-foreground"
                    data-oid="wm2cyts"
                  >
                    <Mountain
                      className="h-8 w-8 mx-auto mb-2 opacity-50"
                      data-oid="n.n-maq"
                    />
                    <p className="text-sm" data-oid="1i0czq.">
                      No depth analysis available
                    </p>
                  </div>
                )}
              </CardContent>
            </CollapsibleContent>
          </Collapsible>
        </Card>

        {/* Depth Map Viewer */}
        {showDepthMap && scene.has_depth && (
          <DepthMapViewer
            scene={scene}
            isVisible={showDepthMap}
            onToggle={() => setShowDepthMap(!showDepthMap)}
            data-oid="u:hkvqm"
          />
        )}

        {/* AI Processing Info */}
        <Card data-oid="9dk4z6x">
          <CardContent className="pt-4" data-oid="11n-u1o">
            <div className="flex items-start space-x-3" data-oid="un_lbmo">
              <Info
                className="h-4 w-4 text-muted-foreground mt-0.5"
                data-oid="xoc8fv0"
              />
              <div className="text-xs text-muted-foreground" data-oid="nxcrqcz">
                <p className="mb-1" data-oid="h6d4u8.">
                  AI analysis powered by YOLO, CLIP, SAM2, and Depth Anything V2
                  models running on RunPod GPU infrastructure.
                </p>
                <p data-oid="pg7g3-e">
                  Processing time: ~1.3s per image • Real-time inference
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </TooltipProvider>
  );
}
