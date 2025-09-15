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
    <TooltipProvider data-oid="gvr835h">
      <div className={`space-y-4 ${className}`} data-oid="22cwafg">
        {/* AI Processing Trigger */}
        <AIProcessingTrigger
          scene={scene}
          onProcessingComplete={onProcessingComplete}
          data-oid="o2x0o_h"
        />

        {/* Scene Analysis */}
        <Card data-oid="uwu7kyv">
          <Collapsible
            open={expandedSections.sceneAnalysis}
            onOpenChange={() => toggleSection("sceneAnalysis")}
            data-oid="7mb:0q7"
          >
            <CollapsibleTrigger
              className="cursor-pointer hover:bg-muted/50 transition-colors pb-3"
              data-oid="tddqx62"
            >
              <CardHeader data-oid="eyqmdon">
                <CardTitle
                  className="flex items-center justify-between text-base"
                  data-oid="8yo_njj"
                >
                  <div
                    className="flex items-center space-x-2"
                    data-oid="w-i-yc4"
                  >
                    <Eye className="h-4 w-4" data-oid="k888t96" />
                    <span data-oid="ci0c4sj">Scene Classification</span>
                  </div>
                  {expandedSections.sceneAnalysis ? (
                    <ChevronDown className="h-4 w-4" data-oid="8x6gs-z" />
                  ) : (
                    <ChevronRight className="h-4 w-4" data-oid="k11nmev" />
                  )}
                </CardTitle>
              </CardHeader>
            </CollapsibleTrigger>
            <CollapsibleContent data-oid="0nvexd6">
              <CardContent className="pt-0" data-oid="syulwnp">
                {scene.scene_type ? (
                  <div className="space-y-3" data-oid="5arfaic">
                    <div
                      className="flex items-center justify-between"
                      data-oid="kaqf1:t"
                    >
                      <Badge
                        variant="secondary"
                        className="text-sm"
                        data-oid="-3xctva"
                      >
                        {scene.scene_type
                          .replace("_", " ")
                          .replace(/\b\w/g, (l) => l.toUpperCase())}
                      </Badge>
                      <Badge
                        variant={getConfidenceVariant(scene.scene_conf || 0)}
                        className="text-xs"
                        data-oid="n92w.gu"
                      >
                        {formatConfidence(scene.scene_conf || 0)}
                      </Badge>
                    </div>

                    {scene.scene_conf && (
                      <div className="space-y-1" data-oid="7na1x09">
                        <div
                          className="flex justify-between text-xs text-muted-foreground"
                          data-oid="j6qwbnm"
                        >
                          <span data-oid="lzlbc_r">Confidence</span>
                          <span
                            className={getConfidenceColor(scene.scene_conf)}
                            data-oid="iwyt5d7"
                          >
                            {formatConfidence(scene.scene_conf)}
                          </span>
                        </div>
                        <Progress
                          value={scene.scene_conf * 100}
                          className="h-2"
                          data-oid="94xpci9"
                        />
                      </div>
                    )}
                  </div>
                ) : (
                  <div
                    className="text-center py-4 text-muted-foreground"
                    data-oid="dulgix:"
                  >
                    <Target
                      className="h-8 w-8 mx-auto mb-2 opacity-50"
                      data-oid="p9n_5p0"
                    />

                    <p className="text-sm" data-oid="qbdi_16">
                      No scene classification available
                    </p>
                  </div>
                )}
              </CardContent>
            </CollapsibleContent>
          </Collapsible>
        </Card>

        {/* Objects */}
        <Card data-oid="p19j08n">
          <Collapsible
            open={expandedSections.objects}
            onOpenChange={() => toggleSection("objects")}
            data-oid="zghbc3q"
          >
            <CollapsibleTrigger
              className="cursor-pointer hover:bg-muted/50 transition-colors pb-3"
              data-oid="-72898."
            >
              <CardHeader data-oid="2nlk0x:">
                <CardTitle
                  className="flex items-center justify-between text-base"
                  data-oid=":7sb8b."
                >
                  <div
                    className="flex items-center space-x-2"
                    data-oid="2_s4y.0"
                  >
                    <Layers className="h-4 w-4" data-oid="wu8dwf." />
                    <span data-oid=".lpj-rg">Detected Objects</span>
                    <Badge
                      variant="outline"
                      className="text-xs"
                      data-oid="znxp9jp"
                    >
                      {scene.objects?.length || 0}
                    </Badge>
                  </div>
                  {expandedSections.objects ? (
                    <ChevronDown className="h-4 w-4" data-oid="_kaw3sv" />
                  ) : (
                    <ChevronRight className="h-4 w-4" data-oid="gdnyp5j" />
                  )}
                </CardTitle>
              </CardHeader>
            </CollapsibleTrigger>
            <CollapsibleContent data-oid="hyzdzoy">
              <CardContent className="pt-0" data-oid="v8bayyk">
                {scene.objects && scene.objects.length > 0 ? (
                  <div
                    className="space-y-2 max-h-64 overflow-y-auto"
                    data-oid="4795a58"
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
                          data-oid="to1kvub"
                        >
                          <div
                            className="flex items-center justify-between mb-2"
                            data-oid="eracnt8"
                          >
                            <span
                              className="font-medium text-sm"
                              data-oid="108ns2v"
                            >
                              {object.label}
                            </span>
                            <Badge
                              variant={getConfidenceVariant(object.confidence)}
                              className="text-xs"
                              data-oid=".pd8ucp"
                            >
                              {formatConfidence(object.confidence)}
                            </Badge>
                          </div>

                          {/* Enhanced material display with multiple materials */}
                          {object.materials && object.materials.length > 0 ? (
                            <div className="space-y-1 mt-2">
                              {object.materials.slice(0, 3).map((mat, idx) => (
                                <div
                                  key={idx}
                                  className="flex items-center space-x-2 text-xs"
                                  data-oid="tulizv-"
                                >
                                  <Settings
                                    className="h-3 w-3 text-muted-foreground"
                                    data-oid="wq5dwpb"
                                  />
                                  <span className="text-muted-foreground" data-oid="o-bko7.">
                                    {mat.material}
                                  </span>
                                  <Badge 
                                    variant="outline" 
                                    className="text-xs h-4 px-1"
                                  >
                                    {formatConfidence(mat.confidence)}
                                  </Badge>
                                </div>
                              ))}
                            </div>
                          ) : object.material ? (
                            // Fallback to legacy single material
                            <div
                              className="flex items-center space-x-2 text-xs text-muted-foreground"
                              data-oid="tulizv-"
                            >
                              <Settings
                                className="h-3 w-3"
                                data-oid="wq5dwpb"
                              />

                              <span data-oid="o-bko7.">
                                {object.material}
                                {object.material_conf && (
                                  <span className="ml-1" data-oid="l2-z:uv">
                                    ({formatConfidence(object.material_conf)})
                                  </span>
                                )}
                              </span>
                            </div>
                          ) : null}

                          {(object.bbox &&
                            typeof object.bbox.x === "number" &&
                            typeof object.bbox.y === "number" &&
                            typeof object.bbox.width === "number" &&
                            typeof object.bbox.height === "number") ? (
                            <div
                              className="text-xs text-muted-foreground mt-1"
                              data-oid="yb.woiz"
                            >
                              {Math.round(object.bbox.width)}×
                              {Math.round(object.bbox.height)} at (
                              {Math.round(object.bbox.x)},{" "}
                              {Math.round(object.bbox.y)})
                            </div>
                          ) : (
                            <div
                              className="text-xs text-muted-foreground mt-1"
                              data-oid="yb.woiz"
                            >
                              Bounding box: N/A
                            </div>
                          )}
                        </div>
                      ))}
                  </div>
                ) : (
                  <div
                    className="text-center py-4 text-muted-foreground"
                    data-oid="6jwglgt"
                  >
                    <Layers
                      className="h-8 w-8 mx-auto mb-2 opacity-50"
                      data-oid="vtbq.c6"
                    />

                    <p className="text-sm" data-oid="m5nxx:i">
                      No objects detected
                    </p>
                  </div>
                )}
              </CardContent>
            </CollapsibleContent>
          </Collapsible>
        </Card>

        {/* Style Analysis */}
        <Card data-oid="y-etabu">
          <Collapsible
            open={expandedSections.styles}
            onOpenChange={() => toggleSection("styles")}
            data-oid="-r7tauc"
          >
            <CollapsibleTrigger
              className="cursor-pointer hover:bg-muted/50 transition-colors pb-3"
              data-oid="0f-5zqv"
            >
              <CardHeader data-oid="0q_sx.g">
                <CardTitle
                  className="flex items-center justify-between text-base"
                  data-oid="7icru:3"
                >
                  <div
                    className="flex items-center space-x-2"
                    data-oid="5ph26li"
                  >
                    <BarChart3 className="h-4 w-4" data-oid="qo2r7ne" />
                    <span data-oid="9xpl6r5">Style Analysis</span>
                    <Badge
                      variant="outline"
                      className="text-xs"
                      data-oid="-zah3fw"
                    >
                      {scene.styles?.length || 0}
                    </Badge>
                  </div>
                  {expandedSections.styles ? (
                    <ChevronDown className="h-4 w-4" data-oid="ay_tfcq" />
                  ) : (
                    <ChevronRight className="h-4 w-4" data-oid="36c2f37" />
                  )}
                </CardTitle>
              </CardHeader>
            </CollapsibleTrigger>
            <CollapsibleContent data-oid="z68_tj-">
              <CardContent className="pt-0" data-oid="sicanx8">
                {scene.styles && scene.styles.length > 0 ? (
                  <div className="space-y-3" data-oid="x_s46lx">
                    {scene.styles
                      .sort((a, b) => b.conf - a.conf)
                      .map((style) => (
                        <div
                          key={style.code}
                          className="space-y-1"
                          data-oid="5kkjgac"
                        >
                          <div
                            className="flex items-center justify-between"
                            data-oid="droy97e"
                          >
                            <span
                              className="text-sm font-medium capitalize"
                              data-oid="vpzgd3l"
                            >
                              {style.code.replace("_", " ")}
                            </span>
                            <span
                              className={`text-xs ${getConfidenceColor(style.conf)}`}
                              data-oid="dfw6-0z"
                            >
                              {formatConfidence(style.conf)}
                            </span>
                          </div>
                          <Progress
                            value={style.conf * 100}
                            className="h-2"
                            data-oid="l1l9x4e"
                          />
                        </div>
                      ))}
                  </div>
                ) : (
                  <div
                    className="text-center py-4 text-muted-foreground"
                    data-oid="iaqbgot"
                  >
                    <BarChart3
                      className="h-8 w-8 mx-auto mb-2 opacity-50"
                      data-oid="8az0x39"
                    />

                    <p className="text-sm" data-oid="r-ia7xd">
                      No style analysis available
                    </p>
                  </div>
                )}
              </CardContent>
            </CollapsibleContent>
          </Collapsible>
        </Card>

        {/* Color Palette */}
        <Card data-oid="iaam7m:">
          <Collapsible
            open={expandedSections.colors}
            onOpenChange={() => toggleSection("colors")}
            data-oid="su:q3xg"
          >
            <CollapsibleTrigger
              className="cursor-pointer hover:bg-muted/50 transition-colors pb-3"
              data-oid="15uvn1h"
            >
              <CardHeader data-oid="o15e5s:">
                <CardTitle
                  className="flex items-center justify-between text-base"
                  data-oid="l7qj3.a"
                >
                  <div
                    className="flex items-center space-x-2"
                    data-oid="13y1y-b"
                  >
                    <Palette className="h-4 w-4" data-oid="tk0jna8" />
                    <span data-oid="ywxm_.b">Color Palette</span>
                    <Badge
                      variant="outline"
                      className="text-xs"
                      data-oid="udb0zi:"
                    >
                      {scene.palette?.length || 0}
                    </Badge>
                  </div>
                  {expandedSections.colors ? (
                    <ChevronDown className="h-4 w-4" data-oid="rr19m0t" />
                  ) : (
                    <ChevronRight className="h-4 w-4" data-oid=".9c.9b_" />
                  )}
                </CardTitle>
              </CardHeader>
            </CollapsibleTrigger>
            <CollapsibleContent data-oid="eu.s5-g">
              <CardContent className="pt-0" data-oid="tz.vl0i">
                {scene.palette && scene.palette.length > 0 ? (
                  <div className="space-y-3" data-oid="89385q_">
                    <div className="grid grid-cols-5 gap-2" data-oid="sdpc2xw">
                      {scene.palette.slice(0, 5).map((color, index) => (
                        <Tooltip key={index} data-oid="b1-sxil">
                          <TooltipTrigger data-oid="6:i7a-u">
                            <div
                              className="h-10 rounded-md border-2 border-background shadow-sm cursor-pointer hover:scale-105 transition-transform"
                              style={{ backgroundColor: color.hex }}
                              data-oid="6gv6eo5"
                            />
                          </TooltipTrigger>
                          <TooltipContent data-oid="y3e6o25">
                            <div className="text-center" data-oid="uf45yfs">
                              <div
                                className="font-mono text-sm"
                                data-oid="jwir5o6"
                              >
                                {color.hex}
                              </div>
                              <div
                                className="text-xs text-muted-foreground"
                                data-oid=".hbcq.w"
                              >
                                {(color.p * 100).toFixed(1)}% coverage
                              </div>
                            </div>
                          </TooltipContent>
                        </Tooltip>
                      ))}
                    </div>

                    <div className="space-y-2" data-oid="7uff5gz">
                      {scene.palette.slice(0, 3).map((color, index) => (
                        <div
                          key={index}
                          className="flex items-center space-x-3"
                          data-oid="p.bg13z"
                        >
                          <div
                            className="w-4 h-4 rounded border"
                            style={{ backgroundColor: color.hex }}
                            data-oid="572:pqt"
                          />

                          <span
                            className="font-mono text-xs"
                            data-oid="x2o3q23"
                          >
                            {color.hex}
                          </span>
                          <span
                            className="text-xs text-muted-foreground ml-auto"
                            data-oid="cmp:057"
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
                    data-oid="yst6odd"
                  >
                    <Palette
                      className="h-8 w-8 mx-auto mb-2 opacity-50"
                      data-oid="eym5dcy"
                    />

                    <p className="text-sm" data-oid="e4f60ip">
                      No color analysis available
                    </p>
                  </div>
                )}
              </CardContent>
            </CollapsibleContent>
          </Collapsible>
        </Card>

        {/* Depth Analysis */}
        <Card data-oid="rn7da40">
          <Collapsible
            open={expandedSections.depth}
            onOpenChange={() => toggleSection("depth")}
            data-oid="tnf-pz."
          >
            <CollapsibleTrigger
              className="cursor-pointer hover:bg-muted/50 transition-colors pb-3"
              data-oid=".d8xtw3"
            >
              <CardHeader data-oid="943s4k3">
                <CardTitle
                  className="flex items-center justify-between text-base"
                  data-oid="zzzfgjo"
                >
                  <div
                    className="flex items-center space-x-2"
                    data-oid="z5evmug"
                  >
                    <Mountain className="h-4 w-4" data-oid="77q.akz" />
                    <span data-oid="ar2:o--">Depth Analysis</span>
                    <Badge
                      variant={scene.has_depth ? "default" : "secondary"}
                      className="text-xs"
                      data-oid="fyfxvby"
                    >
                      {scene.has_depth ? "Available" : "N/A"}
                    </Badge>
                  </div>
                  {expandedSections.depth ? (
                    <ChevronDown className="h-4 w-4" data-oid="qezjdtt" />
                  ) : (
                    <ChevronRight className="h-4 w-4" data-oid="jv6k_4z" />
                  )}
                </CardTitle>
              </CardHeader>
            </CollapsibleTrigger>
            <CollapsibleContent data-oid="qcjhydu">
              <CardContent className="pt-0" data-oid="9wdgids">
                {scene.has_depth ? (
                  <div className="space-y-3" data-oid="jknscmr">
                    <div
                      className="text-sm text-muted-foreground"
                      data-oid="mx:72:k"
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
                      data-oid="c9_0hv:"
                    >
                      <Mountain className="h-4 w-4 mr-2" data-oid="wzc2:1o" />
                      {showDepthMap ? "Hide" : "View"} Depth Map
                    </Button>
                  </div>
                ) : (
                  <div
                    className="text-center py-4 text-muted-foreground"
                    data-oid="n34_hz7"
                  >
                    <Mountain
                      className="h-8 w-8 mx-auto mb-2 opacity-50"
                      data-oid="u-x1zmk"
                    />

                    <p className="text-sm" data-oid="ylw1a1:">
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
            data-oid="1fm244q"
          />
        )}

        {/* AI Processing Info */}
        <Card data-oid="2drd.k-">
          <CardContent className="pt-4" data-oid="03smkl2">
            <div className="flex items-start space-x-3" data-oid="9w588il">
              <Info
                className="h-4 w-4 text-muted-foreground mt-0.5"
                data-oid="e0_ll8b"
              />

              <div className="text-xs text-muted-foreground" data-oid="843.81y">
                <p className="mb-1" data-oid="02:zcnx">
                  AI analysis powered by YOLO, CLIP, SAM2, and Depth Anything V2
                  models running on RunPod GPU infrastructure.
                </p>
                <p data-oid="w2a3sgy">
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
