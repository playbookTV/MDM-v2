import { useState } from "react";
import {
  Mountain,
  Eye,
  EyeOff,
  RotateCw,
  Layers,
  Settings,
  Info,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { useSceneImages } from "@/hooks/useScenes";
import type { Scene } from "@/types/dataset";

interface DepthMapViewerProps {
  scene: Scene;
  isVisible: boolean;
  onToggle: () => void;
  className?: string;
}

export function DepthMapViewer({
  scene,
  isVisible,
  onToggle,
  className,
}: DepthMapViewerProps) {
  const [opacity, setOpacity] = useState([0.7]);
  const [colorMode, setColorMode] = useState<"grayscale" | "heatmap">(
    "heatmap",
  );
  const [showOriginal, setShowOriginal] = useState(true);

  const { originalUrl, depthUrl } = useSceneImages(scene);

  if (!scene.has_depth) {
    return (
      <Card className={className} data-oid="los6rpz">
        <CardContent className="pt-6" data-oid="le_cwcx">
          <div
            className="text-center py-8 text-muted-foreground"
            data-oid="y3tk1i4"
          >
            <Mountain
              className="h-12 w-12 mx-auto mb-4 opacity-50"
              data-oid="w160l2x"
            />

            <h3 className="text-lg font-semibold mb-2" data-oid="4p5hx0n">
              No Depth Data
            </h3>
            <p className="text-sm" data-oid="d7n6e92">
              This scene doesn't have depth map data available.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const toggleColorMode = () => {
    setColorMode((current) =>
      current === "grayscale" ? "heatmap" : "grayscale",
    );
  };

  return (
    <Card className={className} data-oid="09575-0">
      <CardHeader data-oid="_-tn7kn">
        <CardTitle
          className="flex items-center justify-between"
          data-oid="9bqb:t-"
        >
          <div className="flex items-center space-x-2" data-oid="exng.vy">
            <Mountain className="h-5 w-5" data-oid="u5871ji" />
            <span data-oid="__f-pyd">Depth Map Analysis</span>
          </div>
          <div className="flex items-center space-x-2" data-oid="z7in5fq">
            <Badge variant="secondary" className="text-xs" data-oid="uheu0wo">
              3D Spatial
            </Badge>
            <Button
              variant="ghost"
              size="sm"
              onClick={onToggle}
              data-oid="w.q6jpx"
            >
              {isVisible ? (
                <EyeOff className="h-4 w-4" data-oid="pv2pm0u" />
              ) : (
                <Eye className="h-4 w-4" data-oid="7cbes:s" />
              )}
            </Button>
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4" data-oid="zf1m_r8">
        {isVisible && (
          <>
            {/* Depth Map Display */}
            <div
              className="relative rounded-lg overflow-hidden border"
              data-oid="nppor07"
            >
              <div className="relative" data-oid="ljr5p5t">
                {/* Original Image (Background) */}
                {showOriginal && (
                  <img
                    src={originalUrl}
                    alt="Original scene"
                    className="w-full h-auto"
                    data-oid="em02sky"
                  />
                )}

                {/* Depth Map Overlay */}
                {depthUrl && (
                  <img
                    src={depthUrl}
                    alt="Depth map"
                    className={`absolute top-0 left-0 w-full h-full object-cover transition-opacity ${
                      colorMode === "heatmap"
                        ? "depth-heatmap"
                        : "depth-grayscale"
                    }`}
                    style={{
                      opacity: opacity[0],
                      mixBlendMode: showOriginal ? "multiply" : "normal",
                    }}
                    data-oid="0qsatov"
                  />
                )}

                {/* Depth Legend */}
                <div
                  className="absolute top-2 right-2 bg-background/90 backdrop-blur-sm rounded-lg p-2"
                  data-oid="::-lm6p"
                >
                  <div className="text-xs font-medium mb-1" data-oid="s3-hueu">
                    Depth
                  </div>
                  <div
                    className="flex items-center space-x-2 text-xs"
                    data-oid="-tg9izc"
                  >
                    <div
                      className="flex items-center space-x-1"
                      data-oid="6mcmf_2"
                    >
                      <div
                        className="w-3 h-3 bg-blue-600 rounded-sm"
                        data-oid="rhqanny"
                      />

                      <span data-oid="ug5a_kj">Near</span>
                    </div>
                    <div
                      className="flex items-center space-x-1"
                      data-oid="-c2o8lu"
                    >
                      <div
                        className="w-3 h-3 bg-red-600 rounded-sm"
                        data-oid="bu6oulo"
                      />

                      <span data-oid="hr3ohok">Far</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Controls */}
            <div className="space-y-4" data-oid="9leoi1a">
              {/* Opacity Control */}
              <div className="space-y-2" data-oid="no9r-qu">
                <Label
                  className="text-xs font-medium flex items-center"
                  data-oid="-xntoi."
                >
                  <Layers className="h-3 w-3 mr-1" data-oid="o8ltbfm" />
                  Depth Map Opacity
                </Label>
                <Slider
                  value={opacity}
                  onValueChange={setOpacity}
                  max={1}
                  min={0}
                  step={0.1}
                  className="w-full"
                  data-oid="sv553:j"
                />

                <div
                  className="flex justify-between text-xs text-muted-foreground"
                  data-oid="znu3.1d"
                >
                  <span data-oid="-b5i8ss">Transparent</span>
                  <span data-oid="34j.25c">
                    {Math.round(opacity[0] * 100)}%
                  </span>
                  <span data-oid="xwe2fz7">Opaque</span>
                </div>
              </div>

              {/* Display Options */}
              <div className="grid grid-cols-2 gap-3" data-oid="f6d:2e8">
                <div className="flex items-center space-x-2" data-oid="on:duat">
                  <Switch
                    id="show-original"
                    checked={showOriginal}
                    onCheckedChange={setShowOriginal}
                    data-oid="i1l00l4"
                  />

                  <Label
                    htmlFor="show-original"
                    className="text-xs"
                    data-oid="s0x093x"
                  >
                    Show Original
                  </Label>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={toggleColorMode}
                  className="text-xs"
                  data-oid="4:d22li"
                >
                  <RotateCw className="h-3 w-3 mr-1" data-oid="f5i4hxn" />
                  {colorMode === "heatmap" ? "Heatmap" : "Grayscale"}
                </Button>
              </div>
            </div>

            {/* Depth Statistics */}
            <div
              className="bg-muted/50 rounded-lg p-3 space-y-2"
              data-oid="pim2shp"
            >
              <div
                className="flex items-center space-x-2 mb-2"
                data-oid="nmi-ypd"
              >
                <Info
                  className="h-4 w-4 text-muted-foreground"
                  data-oid="d19aegs"
                />

                <span className="text-xs font-medium" data-oid=".mvfov0">
                  Depth Analysis
                </span>
              </div>

              <div
                className="grid grid-cols-2 gap-2 text-xs"
                data-oid="4y9psi1"
              >
                <div className="flex justify-between" data-oid="g5tgs2f">
                  <span className="text-muted-foreground" data-oid="pj_o._x">
                    Resolution:
                  </span>
                  <span className="font-mono" data-oid="rwzj_yc">
                    {scene.width}×{scene.height}
                  </span>
                </div>
                <div className="flex justify-between" data-oid="ef_wgm9">
                  <span className="text-muted-foreground" data-oid="lzeuntt">
                    Model:
                  </span>
                  <span className="font-mono" data-oid="6m2kigr">
                    Depth Anything V2
                  </span>
                </div>
              </div>

              <div
                className="text-xs text-muted-foreground mt-2"
                data-oid="gukgp71"
              >
                Depth maps provide spatial understanding for object
                relationships, occlusion analysis, and 3D scene reconstruction.
              </div>
            </div>
          </>
        )}

        {!isVisible && (
          <div
            className="text-center py-6 text-muted-foreground"
            data-oid="o_-c9mc"
          >
            <Mountain
              className="h-8 w-8 mx-auto mb-2 opacity-50"
              data-oid="o:p7jar"
            />

            <p className="text-sm" data-oid="lfvm4nr">
              Click the eye icon to view depth analysis
            </p>
          </div>
        )}
      </CardContent>

      {/* CSS for depth map styling */}
      <style jsx={true} data-oid="-jjqnr5">{`
        .depth-heatmap {
          filter: hue-rotate(240deg) saturate(1.5) contrast(1.2);
        }

        .depth-grayscale {
          filter: grayscale(1) contrast(1.3);
        }
      `}</style>
    </Card>
  );
}
