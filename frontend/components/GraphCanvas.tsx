"use client";

import { useRef, useState } from "react";
import { MinusIcon, PlusIcon, RotateCcwIcon } from "lucide-react";

import { Button } from "@/components/ui/button";

export interface CanvasNode {
  id: string;
  caption: string;
  color: string;
  size: number;
}

export interface CanvasRelationship {
  id: string;
  from: string;
  to: string;
  caption: string;
  color: string;
}

type Point = { x: number; y: number };

const WIDTH = 1000;
const HEIGHT = 620;

function initialPositions(nodes: CanvasNode[]): Record<string, Point> {
  const center = { x: WIDTH / 2, y: HEIGHT / 2 };
  const radius = Math.min(WIDTH, HEIGHT) * 0.34;
  return Object.fromEntries(
    nodes.map((node, index) => {
      if (nodes.length === 1) return [node.id, center];
      const angle = -Math.PI / 2 + (index / nodes.length) * Math.PI * 2;
      return [
        node.id,
        {
          x: center.x + Math.cos(angle) * radius,
          y: center.y + Math.sin(angle) * radius,
        },
      ];
    }),
  );
}

export default function GraphCanvas({
  nodes,
  rels,
}: {
  nodes: CanvasNode[];
  rels: CanvasRelationship[];
}) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [positions, setPositions] = useState<Record<string, Point>>(() => initialPositions(nodes));
  const [zoom, setZoom] = useState(1);
  const [dragging, setDragging] = useState<string | null>(null);

  function eventPoint(event: React.PointerEvent<SVGSVGElement>): Point | null {
    const svg = svgRef.current;
    if (!svg) return null;
    const matrix = svg.getScreenCTM();
    if (!matrix) return null;
    const point = new DOMPoint(event.clientX, event.clientY).matrixTransform(matrix.inverse());
    return { x: point.x, y: point.y };
  }

  function moveNode(event: React.PointerEvent<SVGSVGElement>) {
    if (!dragging) return;
    const point = eventPoint(event);
    if (!point) return;
    setPositions((current) => ({ ...current, [dragging]: point }));
  }

  const viewWidth = WIDTH / zoom;
  const viewHeight = HEIGHT / zoom;
  const viewBox = `${(WIDTH - viewWidth) / 2} ${(HEIGHT - viewHeight) / 2} ${viewWidth} ${viewHeight}`;

  return (
    <div className="relative h-full min-h-[280px] overflow-hidden">
      <div className="absolute top-3 right-3 z-10 flex gap-1 rounded-lg border bg-background/90 p-1 shadow-sm">
        <Button
          size="icon-sm"
          variant="ghost"
          aria-label="Zoom out"
          onClick={() => setZoom((value) => Math.max(0.55, value - 0.2))}
        >
          <MinusIcon />
        </Button>
        <Button
          size="icon-sm"
          variant="ghost"
          aria-label="Reset graph layout"
          onClick={() => {
            setPositions(initialPositions(nodes));
            setZoom(1);
          }}
        >
          <RotateCcwIcon />
        </Button>
        <Button
          size="icon-sm"
          variant="ghost"
          aria-label="Zoom in"
          onClick={() => setZoom((value) => Math.min(2.4, value + 0.2))}
        >
          <PlusIcon />
        </Button>
      </div>

      <svg
        ref={svgRef}
        viewBox={viewBox}
        className="h-full w-full touch-none select-none"
        role="img"
        aria-label={`Evidence graph with ${nodes.length} nodes and ${rels.length} relationships`}
        onPointerMove={moveNode}
        onPointerUp={(event) => {
          if (dragging) event.currentTarget.releasePointerCapture(event.pointerId);
          setDragging(null);
        }}
        onPointerCancel={() => setDragging(null)}
        onWheel={(event) => {
          event.preventDefault();
          setZoom((value) => Math.min(2.4, Math.max(0.55, value + (event.deltaY < 0 ? 0.1 : -0.1))));
        }}
      >
        <defs>
          <marker
            id="graph-arrow"
            markerWidth="8"
            markerHeight="8"
            refX="7"
            refY="4"
            orient="auto"
            markerUnits="strokeWidth"
          >
            <path d="M0,0 L8,4 L0,8 z" fill="currentColor" />
          </marker>
        </defs>

        {rels.map((relationship) => {
          const from = positions[relationship.from];
          const to = positions[relationship.to];
          if (!from || !to) return null;
          return (
            <g key={relationship.id} className="text-muted-foreground">
              <line
                x1={from.x}
                y1={from.y}
                x2={to.x}
                y2={to.y}
                stroke={relationship.color}
                strokeWidth={2}
                strokeOpacity={0.72}
                markerEnd="url(#graph-arrow)"
              />
              <text
                x={(from.x + to.x) / 2}
                y={(from.y + to.y) / 2 - 7}
                textAnchor="middle"
                className="fill-muted-foreground text-[11px] font-medium"
              >
                {relationship.caption}
              </text>
            </g>
          );
        })}

        {nodes.map((node) => {
          const point = positions[node.id];
          if (!point) return null;
          const caption = node.caption.length > 30 ? `${node.caption.slice(0, 29)}…` : node.caption;
          return (
            <g
              key={node.id}
              transform={`translate(${point.x} ${point.y})`}
              className="cursor-grab active:cursor-grabbing"
              onPointerDown={(event) => {
                event.currentTarget.ownerSVGElement?.setPointerCapture(event.pointerId);
                setDragging(node.id);
              }}
            >
              <circle
                r={node.size}
                fill={node.color}
                stroke="var(--background)"
                strokeWidth={5}
                className="drop-shadow-sm"
              />
              <circle r={node.size - 4} fill="none" stroke="white" strokeOpacity={0.35} strokeWidth={1} />
              <text
                y={node.size + 20}
                textAnchor="middle"
                className="fill-foreground text-[12px] font-semibold"
              >
                {caption}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
