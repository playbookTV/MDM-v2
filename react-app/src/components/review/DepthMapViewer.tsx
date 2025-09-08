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
      <Card className={className} data-oid="dv8okvq">
        <CardContent className="pt-6" data-oid="bc4-8hp">
          <div
            className="text-center py-8 text-muted-foreground"
            data-oid="u:bl_nv"
          >
            <Mountain
              className="h-12 w-12 mx-auto mb-4 opacity-50"
              data-oid="3jye.47"
            />
            <h3 className="text-lg font-semibold mb-2" data-oid="_-..r2w">
              No Depth Data
            </h3>
            <p className="text-sm" data-oid="nw5-q-v">
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
    <Card className={className} data-oid="1scj0xd">
      <CardHeader data-oid="k4bn:qz">
        <CardTitle
          className="flex items-center justify-between"
          data-oid="dw1yp5i"
        >
          <div className="flex items-center space-x-2" data-oid="63kpyk8">
            <Mountain className="h-5 w-5" data-oid="gnk4adm" />
            <span data-oid="-cmnfzh">Depth Map Analysis</span>
          </div>
          <div className="flex items-center space-x-2" data-oid="h37rmzy">
            <Badge variant="secondary" className="text-xs" data-oid="zbz9-zq">
              3D Spatial
            </Badge>
            <Button
              variant="ghost"
              size="sm"
              onClick={onToggle}
              data-oid="b.jlij5"
            >
              {isVisible ? (
                <EyeOff className="h-4 w-4" data-oid="zq:1372" />
              ) : (
                <Eye className="h-4 w-4" data-oid="q7tlw6r" />
              )}
            </Button>
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4" data-oid="zfi-3xn">
        {isVisible && (
          <>
            {/* Depth Map Display */}
            <div
              className="relative rounded-lg overflow-hidden border"
              data-oid="egkxni1"
            >
              <div className="relative" data-oid="8i9anq6">
                {/* Original Image (Background) */}
                {showOriginal && (
                  <img
                    src={originalUrl}
                    alt="Original scene"
                    className="w-full h-auto"
                    data-oid="vvj4jjh"
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
                    data-oid="thyqye7"
                  />
                )}

                {/* Depth Legend */}
                <div
                  className="absolute top-2 right-2 bg-background/90 backdrop-blur-sm rounded-lg p-2"
                  data-oid="_h6p40i"
                >
                  <div className="text-xs font-medium mb-1" data-oid="f3f41nn">
                    Depth
                  </div>
                  <div
                    className="flex items-center space-x-2 text-xs"
                    data-oid="h8t1f43"
                  >
                    <div
                      className="flex items-center space-x-1"
                      data-oid="awtcxlh"
                    >
                      <div
                        className="w-3 h-3 bg-blue-600 rounded-sm"
                        data-oid="69fyb_h"
                      />
                      <span data-oid="z6rj1j2">Near</span>
                    </div>
                    <div
                      className="flex items-center space-x-1"
                      data-oid="08qtc5w"
                    >
                      <div
                        className="w-3 h-3 bg-red-600 rounded-sm"
                        data-oid="rqsrhlm"
                      />
                      <span data-oid="gwr08w6">Far</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Controls */}
            <div className="space-y-4" data-oid="bw5fp-p">
              {/* Opacity Control */}
              <div className="space-y-2" data-oid="fbapdsw">
                <Label
                  className="text-xs font-medium flex items-center"
                  data-oid="e0wpkn1"
                >
                  <Layers className="h-3 w-3 mr-1" data-oid="cxd9knh" />
                  Depth Map Opacity
                </Label>
                <Slider
                  value={opacity}
                  onValueChange={setOpacity}
                  max={1}
                  min={0}
                  step={0.1}
                  className="w-full"
                  data-oid="gmb_i7y"
                />

                <div
                  className="flex justify-between text-xs text-muted-foreground"
                  data-oid="4pf5ig4"
                >
                  <span data-oid="v_5h70j">Transparent</span>
                  <span data-oid="1ty512y">
                    {Math.round(opacity[0] * 100)}%
                  </span>
                  <span data-oid="q4sbl86">Opaque</span>
                </div>
              </div>

              {/* Display Options */}
              <div className="grid grid-cols-2 gap-3" data-oid="o327_3.">
                <div className="flex items-center space-x-2" data-oid="8ljfqmc">
                  <Switch
                    id="show-original"
                    checked={showOriginal}
                    onCheckedChange={setShowOriginal}
                    data-oid="kp_75as"
                  />

                  <Label
                    htmlFor="show-original"
                    className="text-xs"
                    data-oid="ns._a5y"
                  >
                    Show Original
                  </Label>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={toggleColorMode}
                  className="text-xs"
                  data-oid="a49ag:a"
                >
                  <RotateCw className="h-3 w-3 mr-1" data-oid="t-i8x14" />
                  {colorMode === "heatmap" ? "Heatmap" : "Grayscale"}
                </Button>
              </div>
            </div>

            {/* Depth Statistics */}
            <div
              className="bg-muted/50 rounded-lg p-3 space-y-2"
              data-oid="xo1k6xk"
            >
              <div
                className="flex items-center space-x-2 mb-2"
                data-oid="wqnhhv."
              >
                <Info
                  className="h-4 w-4 text-muted-foreground"
                  data-oid="4vvqrzb"
                />
                <span className="text-xs font-medium" data-oid="b1tun.z">
                  Depth Analysis
                </span>
              </div>

              <div
                className="grid grid-cols-2 gap-2 text-xs"
                data-oid="aek8qw3"
              >
                <div className="flex justify-between" data-oid="hzw7.h.">
                  <span className="text-muted-foreground" data-oid="jc7ixex">
                    Resolution:
                  </span>
                  <span className="font-mono" data-oid="j3_3k54">
                    {scene.width}×{scene.height}
                  </span>
                </div>
                <div className="flex justify-between" data-oid="c7l4ot2">
                  <span className="text-muted-foreground" data-oid="1jbi-88">
                    Model:
                  </span>
                  <span className="font-mono" data-oid="-z6px8x">
                    Depth Anything V2
                  </span>
                </div>
              </div>

              <div
                className="text-xs text-muted-foreground mt-2"
                data-oid="wefykff"
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
            data-oid="viwo9k3"
          >
            <Mountain
              className="h-8 w-8 mx-auto mb-2 opacity-50"
              data-oid="tn7cqri"
            />
            <p className="text-sm" data-oid="ltxhfas">
              Click the eye icon to view depth analysis
            </p>
          </div>
        )}
      </CardContent>

      {/* CSS for depth map styling */}
      <style jsx data-oid="z.vjvg8">{`
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
