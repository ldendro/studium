import cytoscape, { type Core } from 'cytoscape'
import { Maximize2, Network, RotateCcw } from 'lucide-react'
import { useEffect, useRef } from 'react'
import type { GraphProjection } from '../lib/types'
import { IconButton } from './ui'

export function KnowledgeGraph({
  graph,
  onSelect,
  mode = 'knowledge',
}: {
  graph: GraphProjection
  onSelect: (conceptId: string) => void
  mode?: 'knowledge' | 'mastery'
}) {
  const container = useRef<HTMLDivElement>(null)
  const core = useRef<Core | null>(null)

  useEffect(() => {
    if (!container.current) return
    core.current?.destroy()
    const instance = cytoscape({
      container: container.current,
      elements: [
        ...graph.nodes.map((node) => ({
          data: {
            id: node.id,
            label: node.title,
            conceptType: node.concept_type,
            domain: node.domains[0] ?? 'general',
            selected: node.selected,
            masteryState: node.mastery_state ?? 'unassessed',
            masteryScore: node.mastery_score ?? 0,
            retentionDue: node.retention_due_count ?? 0,
          },
          classes: [
            node.selected ? 'center' : '',
            mode === 'mastery' ? `mastery-${node.mastery_state ?? 'unassessed'}` : '',
          ].filter(Boolean).join(' '),
        })),
        ...graph.edges.map((edge) => ({
          data: {
            id: edge.id,
            source: edge.source,
            target: edge.target,
            label: edge.relationship_type.replaceAll('_', ' '),
            relationshipType: edge.relationship_type,
          },
        })),
      ],
      style: [
        {
          selector: 'node',
          style: {
            width: 26,
            height: 26,
            label: 'data(label)',
            color: '#aeb8c6',
            'font-family': 'DM Sans, sans-serif',
            'font-size': 9,
            'font-weight': 500,
            'text-wrap': 'wrap',
            'text-max-width': '100px',
            'text-valign': 'bottom',
            'text-margin-y': 8,
            'background-color': '#78a8d4',
            'border-width': 4,
            'border-color': 'rgba(120,168,212,.12)',
          },
        },
        {
          selector: 'node.center',
          style: {
            width: 38,
            height: 38,
            color: '#edf0f4',
            'font-size': 11,
            'font-weight': 700,
            'background-color': '#deb66a',
            'border-width': 6,
            'border-color': 'rgba(222,182,106,.15)',
          },
        },
        {
          selector: 'node.mastery-strong',
          style: {
            'background-color': '#72bb9a',
            'border-color': 'rgba(114,187,154,.18)',
          },
        },
        {
          selector: 'node.mastery-developing',
          style: {
            'background-color': '#78a8d4',
            'border-color': 'rgba(120,168,212,.18)',
          },
        },
        {
          selector: 'node.mastery-fragile',
          style: {
            'background-color': '#df9d67',
            'border-color': 'rgba(223,157,103,.18)',
          },
        },
        {
          selector: 'node.mastery-unassessed',
          style: {
            'background-color': '#566477',
            'border-color': 'rgba(86,100,119,.18)',
          },
        },
        {
          selector: 'node:active',
          style: {
            'overlay-color': '#deb66a',
            'overlay-opacity': 0.12,
            'overlay-padding': 8,
          },
        },
        {
          selector: 'edge',
          style: {
            width: 1.2,
            'line-color': '#384454',
            'target-arrow-color': '#566477',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'arrow-scale': 0.65,
            label: 'data(label)',
            color: '#6f7b8b',
            'font-size': 7,
            'text-background-color': '#111722',
            'text-background-opacity': 0.85,
            'text-background-padding': '2px',
            'text-rotation': 'autorotate',
          },
        },
        {
          selector: 'edge[relationshipType = "depends_on"]',
          style: { 'line-color': '#72bb9a', 'target-arrow-color': '#72bb9a' },
        },
        {
          selector: 'edge[relationshipType = "variant_of"]',
          style: { 'line-color': '#ad96d5', 'target-arrow-color': '#ad96d5' },
        },
        {
          selector: 'edge[relationshipType = "contrasts_with"]',
          style: { 'line-style': 'dashed', 'line-color': '#df9d67' },
        },
      ],
      layout: mode === 'mastery'
        ? {
            name: 'breadthfirst',
            animate: false,
            directed: true,
            spacingFactor: 1.25,
            padding: 34,
          }
        : {
            name: 'cose',
            animate: false,
            idealEdgeLength: graph.center ? 110 : 80,
            nodeOverlap: 14,
            gravity: 0.8,
            padding: 34,
            randomize: true,
          },
      minZoom: 0.25,
      maxZoom: 2.2,
      wheelSensitivity: 0.25,
    })
    instance.on('tap', 'node', (event) => onSelect(event.target.id()))
    core.current = instance
    const observer = new ResizeObserver(() => {
      instance.resize()
      instance.fit(undefined, 28)
    })
    observer.observe(container.current)
    return () => {
      observer.disconnect()
      instance.destroy()
      core.current = null
    }
  }, [graph, mode, onSelect])

  return (
    <div className="knowledge-graph">
      <div className="knowledge-graph__toolbar">
        <span>
          <Network size={15} /> {graph.nodes.length} concepts
        </span>
        <div>
          <IconButton label="Recenter graph" onClick={() => core.current?.center()}>
            <RotateCcw size={15} />
          </IconButton>
          <IconButton label="Fit graph" onClick={() => core.current?.fit(undefined, 30)}>
            <Maximize2 size={15} />
          </IconButton>
        </div>
      </div>
      <div className="knowledge-graph__canvas" ref={container} />
      <div className="graph-legend" aria-label="Graph relationship legend">
        {Object.entries(graph.legend).map(([type, label]) => (
          <span key={type} data-type={type}>
            <i /> {label}
          </span>
        ))}
      </div>
    </div>
  )
}
