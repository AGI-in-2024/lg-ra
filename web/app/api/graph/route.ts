import { NextResponse } from 'next/server';
import * as fs from 'fs';
import * as xml2js from 'xml2js';

interface GraphNode {
  id: string;
  type: string;
  content?: string;
  entity_type?: string;
  name?: string;
  canonical_name?: string;
  paper_id?: string;
  statement?: string;
  year?: number;
}

interface GraphEdge {
  source: string;
  target: string;
  type?: string;
  context?: string;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export async function GET() {
  try {
    const graphmlPath = 'public/data/dataset1/longevity_knowledge_graph.graphml';
    
    if (!fs.existsSync(graphmlPath)) {
      return NextResponse.json({ error: 'GraphML file not found' }, { status: 404 });
    }

    const xmlData = fs.readFileSync(graphmlPath, 'utf8');
    const parser = new xml2js.Parser();
    
    const result = await parser.parseStringPromise(xmlData);
    
    const graphData: GraphData = {
      nodes: [],
      edges: []
    };

    // Parse nodes
    if (result.graphml?.graph?.[0]?.node) {
      for (const xmlNode of result.graphml.graph[0].node) {
        const node: GraphNode = {
          id: xmlNode.$.id,
          type: 'unknown'
        };

        // Parse node data attributes
        if (xmlNode.data) {
          for (const data of xmlNode.data) {
            const key = data.$.key;
            const value = data._ || data;

            switch (key) {
              case 'd0':
                node.type = value;
                break;
              case 'd1':
                node.content = value;
                break;
              case 'd2':
                node.year = parseInt(value);
                break;
              case 'd3':
                node.statement = value;
                break;
              case 'd4':
                node.paper_id = value;
                break;
              case 'd5':
                node.entity_type = value;
                break;
              case 'd6':
                node.name = value;
                break;
              case 'd7':
                node.canonical_name = value;
                break;
            }
          }
        }

        graphData.nodes.push(node);
      }
    }

    // Parse edges
    if (result.graphml?.graph?.[0]?.edge) {
      for (const xmlEdge of result.graphml.graph[0].edge) {
        const edge: GraphEdge = {
          source: xmlEdge.$.source,
          target: xmlEdge.$.target
        };

        // Parse edge data attributes
        if (xmlEdge.data) {
          for (const data of xmlEdge.data) {
            const key = data.$.key;
            const value = data._ || data;

            switch (key) {
              case 'd8':
                edge.type = value;
                break;
              case 'd9':
                edge.context = value;
                break;
            }
          }
        }

        graphData.edges.push(edge);
      }
    }

    return NextResponse.json(graphData);

  } catch (error) {
    console.error('Error loading graph:', error);
    return NextResponse.json({ error: 'Failed to load graph data' }, { status: 500 });
  }
} 