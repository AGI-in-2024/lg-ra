/* eslint-disable @typescript-eslint/no-require-imports */
/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import { useState, useEffect, useRef, useCallback } from 'react';

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
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

interface GraphEdge {
  source: string | GraphNode;
  target: string | GraphNode;
  type?: string;
  context?: string;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

interface GraphVisualizationProps {
  focusNodeId?: string;
  highlightPapers?: string[];
  openSearch?: boolean;
}

export default function GraphVisualization({ focusNodeId, highlightPapers = [], openSearch = false }: GraphVisualizationProps = {}) {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [showFullContent, setShowFullContent] = useState(false);
  const [connectedNodes, setConnectedNodes] = useState<{
    incoming: Array<{node: GraphNode, edge: GraphEdge}>,
    outgoing: Array<{node: GraphNode, edge: GraphEdge}>
  }>({ incoming: [], outgoing: [] });
  const [showLocalGraph, setShowLocalGraph] = useState(false);
  const [panelWidth, setPanelWidth] = useState(384); // 96 * 4 = 384px (w-96)
  const [isResizing, setIsResizing] = useState(false);
  const [showSearchPanel, setShowSearchPanel] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredNodes, setFilteredNodes] = useState<GraphNode[]>([]);
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const localGraphRef = useRef<SVGSVGElement>(null);
  const resizeHandleRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const zoomBehaviorRef = useRef<any>(null);
  const simulationRef = useRef<any>(null);

  // Load graph data from API
  const loadGraphData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/graph');
      if (!response.ok) {
        throw new Error('Ошибка загрузки данных графа');
      }
      const data: GraphData = await response.json();
      setGraphData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Неизвестная ошибка');
    } finally {
      setLoading(false);
    }
  };

  // Node styling functions
  const getNodeColor = useCallback((node: GraphNode) => {
    // Подсветка выбранного узла
    if (selectedNode && selectedNode.id === node.id) {
      return '#ffff00'; // Желтый для выбранного узла
    }
    
    // Подсветка статей из отчета
    if (highlightPapers.includes(node.id) || highlightPapers.includes(node.paper_id || '')) {
      return '#ffd700'; // Золотой для подсвеченных статей
    }
    
    switch (node.type) {
      case 'Paper': return '#00ff00';
      case 'Entity': return '#00ccff';
      case 'Result': return '#ffaa00';
      case 'Conclusion': return '#ff00aa';
      default: return '#888888';
    }
  }, [selectedNode, highlightPapers]);

  const getNodeSize = useCallback((node: GraphNode) => {
    // Увеличенный размер для выбранного узла
    if (selectedNode && selectedNode.id === node.id) {
      switch (node.type) {
        case 'Paper': return 18;
        case 'Entity': return 14;
        case 'Result': return 12;
        case 'Conclusion': return 12;
        default: return 10;
      }
    }
    
    switch (node.type) {
      case 'Paper': return 12;
      case 'Entity': return 8;
      case 'Result': return 6;
      case 'Conclusion': return 6;
      default: return 5;
    }
  }, [selectedNode]);

  // Initialize D3 force simulation
  useEffect(() => {
    if (!graphData || !svgRef.current) {
      return;
    }

    const d3 = require('d3');
    const svg = d3.select(svgRef.current);
    const parentContainer = svg.node()?.parentElement;
    const width = parentContainer?.clientWidth || 1200;
    const height = parentContainer?.clientHeight || 800;
    
    // Clear previous content
    svg.selectAll("*").remove();
    
    // Set dynamic viewBox
    svg.attr("viewBox", `0 0 ${width} ${height}`);
    
    // Create container for zoom/pan
    const container = svg.append("g");
    
    // Setup zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([0.1, 4])
      .on("zoom", (event: any) => {
        container.attr("transform", event.transform);
      });
    
    svg.call(zoom);
    zoomBehaviorRef.current = zoom;
    
    // Clone data to avoid mutations
    const nodes = graphData.nodes.map(d => ({...d}));
    const links = graphData.edges.map(d => ({...d}));
    
    // Create force simulation
    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id((d: any) => d.id).distance(Math.min(60, width/20)))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(15))
      .force("x", d3.forceX(width / 2).strength(0.1))
      .force("y", d3.forceY(height / 2).strength(0.1));

    simulationRef.current = simulation;

    // Create links
    const link = container.append("g")
      .attr("stroke", "#00ff00")
      .attr("stroke-opacity", 0.4)
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke-width", 1.5);

    // Create nodes
    const node = container.append("g")
      .selectAll("g")
      .data(nodes)
      .join("g")
      .attr("cursor", "pointer")
      .call(d3.drag()
        .on("start", (event: any, d: any) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on("drag", (event: any, d: any) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on("end", (event: any, d: any) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        }));

    // Add circles to nodes
    node.append("circle")
      .attr("r", (d: GraphNode) => getNodeSize(d))
      .attr("fill", (d: GraphNode) => getNodeColor(d))
      .attr("stroke", (d: GraphNode) => selectedNode && selectedNode.id === d.id ? "#ffffff" : "#fff")
      .attr("stroke-width", (d: GraphNode) => selectedNode && selectedNode.id === d.id ? 3 : 1.5)
      .on("click", (event: any, d: GraphNode) => {
        setSelectedNode(d);
        setShowFullContent(false); // Reset content view when selecting new node
        setShowLocalGraph(false); // Reset local graph when selecting new node
        
        // Zoom to node
        const scale = 2.5;
        const [x, y] = [d.x || 0, d.y || 0];
        
        svg.transition()
          .duration(750)
          .call(
            zoom.transform,
            d3.zoomIdentity
              .translate(width / 2, height / 2)
              .scale(scale)
              .translate(-x, -y)
          );
        
        event.stopPropagation();
      })
      .on("mouseover", (event: any, d: GraphNode) => {
        d3.select(event.currentTarget)
          .transition()
          .duration(200)
          .attr("r", getNodeSize(d) * 1.2);
      })
      .on("mouseout", (event: any, d: GraphNode) => {
        d3.select(event.currentTarget)
          .transition()
          .duration(200)
          .attr("r", getNodeSize(d));
      });

    // Add labels to nodes
    node.append("text")
      .text((d: GraphNode) => getNodeLabel(d).substring(0, 12))
      .attr("font-size", 10)
      .attr("fill", "#00ff00")
      .attr("text-anchor", "middle")
      .attr("dy", 25)
      .style("pointer-events", "none")
      .style("user-select", "none");

    // Update positions on simulation tick
    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      node
        .attr("transform", (d: any) => `translate(${d.x},${d.y})`);
    });

    // Фокус на определенном узле, если указан
    if (focusNodeId) {
      const targetNode = nodes.find(n => n.id === focusNodeId || n.paper_id === focusNodeId);
      if (targetNode) {
        // Устанавливаем выбранный узел сразу
        setSelectedNode(targetNode);
        
        // Функция для фокуса на узле
        const focusOnTargetNode = () => {
          if (targetNode.x !== undefined && targetNode.y !== undefined) {
            const transform = d3.zoomIdentity
              .translate(width / 2 - targetNode.x, height / 2 - targetNode.y)
              .scale(2.5);
            svg.transition().duration(1500).call(zoom.transform, transform);
          }
        };

        // Пробуем фокусироваться несколько раз пока симуляция стабилизируется
        let attempts = 0;
        const maxAttempts = 10;
        const tryFocus = () => {
          attempts++;
          if (targetNode.x !== undefined && targetNode.y !== undefined) {
            focusOnTargetNode();
          } else if (attempts < maxAttempts) {
            setTimeout(tryFocus, 200);
          }
        };
        
        setTimeout(tryFocus, 300);
      }
    }

    // Cleanup function
    return () => {
      simulation.stop();
    };

  }, [graphData, focusNodeId, getNodeColor, getNodeSize, selectedNode]);

  // Обновление подсветки выбранного узла
  useEffect(() => {
    if (!svgRef.current) return;
    
    const d3 = require('d3');
    const svg = d3.select(svgRef.current);
    
    // Обновляем цвет, размер и обводку всех узлов
    svg.selectAll("circle")
      .attr("r", (d: any) => getNodeSize(d))
      .attr("fill", (d: any) => getNodeColor(d))
      .attr("stroke", (d: any) => selectedNode && selectedNode.id === d.id ? "#ffffff" : "#fff")
      .attr("stroke-width", (d: any) => selectedNode && selectedNode.id === d.id ? 3 : 1.5);
      
  }, [selectedNode, getNodeColor, getNodeSize]);

  // Обработка изменения размера окна
  useEffect(() => {
    const handleResize = () => {
      if (graphData && svgRef.current) {
        // Перезапускаем симуляцию с новыми размерами
        setTimeout(() => {
          const d3 = require('d3');
          const svg = d3.select(svgRef.current);
          const parentContainer = svg.node()?.parentElement;
          const newWidth = parentContainer?.clientWidth || 1200;
          const newHeight = parentContainer?.clientHeight || 800;
          
          svg.attr("viewBox", `0 0 ${newWidth} ${newHeight}`);
          
          if (simulationRef.current) {
            simulationRef.current
              .force("center", d3.forceCenter(newWidth / 2, newHeight / 2))
              .alpha(0.3)
              .restart();
          }
        }, 100);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [graphData]);

  // Load data on component mount
  useEffect(() => {
    loadGraphData();
    // Автоматически показываем панель поиска если есть фокус, подсветка или openSearch
    if (focusNodeId || highlightPapers.length > 0 || openSearch) {
      setShowSearchPanel(true);
    }
  }, [focusNodeId, highlightPapers, openSearch]);

  // Фильтрация узлов по поисковому запросу и типам
  useEffect(() => {
    if (!graphData) return;
    
    let filtered = graphData.nodes;
    
    // Фильтр по типам
    if (selectedTypes.length > 0) {
      filtered = filtered.filter(node => selectedTypes.includes(node.type));
    }
    
    // Фильтр по поисковому запросу
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(node => {
        const searchText = [
          node.id,
          node.name,
          node.canonical_name,
          node.paper_id,
          node.type,
          node.entity_type,
          node.content
        ].filter(Boolean).join(' ').toLowerCase();
        
        return searchText.includes(query);
      });
    }
    
    setFilteredNodes(filtered);
  }, [graphData, searchQuery, selectedTypes]);

  // Горячие клавиши
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === 'f') {
        e.preventDefault();
        setShowSearchPanel(true);
        // Фокус на поле поиска через небольшую задержку
        setTimeout(() => {
          const searchInput = document.querySelector('input[placeholder="Поиск по узлам..."]') as HTMLInputElement;
          if (searchInput) {
            searchInput.focus();
          }
        }, 100);
      }
      if (e.key === 'Escape' && showSearchPanel) {
        setShowSearchPanel(false);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => {
      window.removeEventListener('keydown', handleKeyPress);
    };
  }, [showSearchPanel]);

  // Получение всех уникальных типов узлов
  const nodeTypes = graphData ? [...new Set(graphData.nodes.map(node => node.type))] : [];

  // Функция для переключения фильтра типов
  const toggleTypeFilter = (type: string) => {
    setSelectedTypes(prev => 
      prev.includes(type) 
        ? prev.filter(t => t !== type)
        : [...prev, type]
    );
  };

  // Функция для очистки всех фильтров
  const clearAllFilters = () => {
    setSearchQuery('');
    setSelectedTypes([]);
  };

  // Функция для фокуса на узле из панели поиска
  const focusOnNodeFromSearch = (nodeId: string) => {
    if (!graphData || !svgRef.current) return;
    
    const d3 = require('d3');
    const svg = d3.select(svgRef.current);
    const targetNode = graphData.nodes.find(n => n.id === nodeId);
    
    if (targetNode && zoomBehaviorRef.current) {
      // Устанавливаем выбранный узел
      setSelectedNode(targetNode);
      setShowFullContent(false);
      setShowLocalGraph(false);
      
      // Ищем узел в симуляции для получения актуальных координат
      const simulationNode = simulationRef.current?.nodes()?.find((n: any) => n.id === nodeId);
      
      const performFocus = () => {
        const nodeToFocus = simulationNode || targetNode;
        if (nodeToFocus && nodeToFocus.x !== undefined && nodeToFocus.y !== undefined) {
          const parentContainer = svg.node()?.parentElement;
          const currentWidth = parentContainer?.clientWidth || 1200;
          const currentHeight = parentContainer?.clientHeight || 800;
          const scale = 2.5;
          const [x, y] = [nodeToFocus.x, nodeToFocus.y];
          
          svg.transition()
            .duration(750)
            .call(
              zoomBehaviorRef.current.transform,
              d3.zoomIdentity
                .translate(currentWidth / 2, currentHeight / 2)
                .scale(scale)
                .translate(-x, -y)
            );
        }
      };

      // Пробуем фокусироваться несколько раз до стабилизации симуляции
      let attempts = 0;
      const tryFocus = () => {
        attempts++;
        const nodeToCheck = simulationNode || targetNode;
        if (nodeToCheck && nodeToCheck.x !== undefined && nodeToCheck.y !== undefined) {
          performFocus();
        } else if (attempts < 8) {
          setTimeout(tryFocus, 250);
        }
      };
      
      // Первая попытка сразу, затем с задержкой
      if (simulationNode && simulationNode.x !== undefined) {
        performFocus();
      } else {
        setTimeout(tryFocus, 100);
      }
    }
  };

  const getNodeLabel = (node: GraphNode) => {
    if (node.canonical_name) return node.canonical_name;
    if (node.name) return node.name;
    if (node.statement) return node.statement;
    if (node.content) return node.content;
    if (node.type === 'Paper') return `Paper ${node.year || ''}`;
    return node.type;
  };

  const resetZoom = () => {
    if (svgRef.current && zoomBehaviorRef.current) {
      const d3 = require('d3');
      const svg = d3.select(svgRef.current);
      
      svg.transition()
        .duration(750)
        .call(
          zoomBehaviorRef.current.transform,
          d3.zoomIdentity
        );
    }
  };

  // Find connected nodes for selected node
  const findConnectedNodes = useCallback((nodeId: string) => {
    if (!graphData) return { incoming: [], outgoing: [] };

    const incoming: Array<{node: GraphNode, edge: GraphEdge}> = [];
    const outgoing: Array<{node: GraphNode, edge: GraphEdge}> = [];

    graphData.edges.forEach(edge => {
      if (edge.target === nodeId) {
        const sourceNode = graphData.nodes.find(n => n.id === edge.source);
        if (sourceNode) {
          incoming.push({ node: sourceNode, edge });
        }
      } else if (edge.source === nodeId) {
        const targetNode = graphData.nodes.find(n => n.id === edge.target);
        if (targetNode) {
          outgoing.push({ node: targetNode, edge });
        }
      }
    });

    return { incoming, outgoing };
  }, [graphData]);

  // Update connected nodes when selected node changes
  useEffect(() => {
    if (selectedNode) {
      const connections = findConnectedNodes(selectedNode.id);
      setConnectedNodes(connections);
    } else {
      setConnectedNodes({ incoming: [], outgoing: [] });
    }
  }, [selectedNode, graphData, findConnectedNodes]);

  // Create local mini-graph
  const createLocalGraph = useCallback(() => {
    if (!selectedNode || !localGraphRef.current || !showLocalGraph) {
      return;
    }

    const d3 = require('d3');
    const svg = d3.select(localGraphRef.current);
    const width = Math.max(280, panelWidth - 40); // Адаптивная ширина
    const height = Math.max(250, Math.min(400, panelWidth * 0.6)); // Адаптивная высота

    // Clear previous content
    svg.selectAll("*").remove();
    
    // Set viewBox for proper scaling
    svg.attr("viewBox", `0 0 ${width} ${height}`);

    // Get local nodes and edges
    const localNodes = [
      selectedNode,
      ...connectedNodes.incoming.map(c => c.node),
      ...connectedNodes.outgoing.map(c => c.node)
    ];

    const localEdges = [
      ...connectedNodes.incoming.map(c => c.edge),
      ...connectedNodes.outgoing.map(c => c.edge)
    ];

    if (localNodes.length <= 1) {
      // Show single node in center if no connections
      const centerNode = svg.append("g")
        .datum(selectedNode)
        .attr("transform", `translate(${width/2}, ${height/2})`);
      
      centerNode.append("circle")
        .attr("r", 15)
        .attr("fill", "#ffff00")
        .attr("stroke", "#fff")
        .attr("stroke-width", 2);
        
      // Background for text
      const labelText = getNodeLabel(selectedNode).substring(0, 12) || 'Узел';
      centerNode.append("rect")
        .attr("x", -(labelText.length * 3.5))
        .attr("y", -30)
        .attr("width", labelText.length * 7)
        .attr("height", 14)
        .attr("fill", "rgba(0,0,0,0.9)")
        .attr("rx", 3);
        
      centerNode.append("text")
        .text(labelText)
        .attr("font-size", 11)
        .attr("fill", "#00ff00")
        .attr("text-anchor", "middle")
        .attr("dy", -20)
        .attr("font-weight", "bold");
        
      // Show "no connections" message
      svg.append("text")
        .text("Нет связей")
        .attr("x", width/2)
        .attr("y", height - 20)
        .attr("text-anchor", "middle")
        .attr("font-size", 12)
        .attr("fill", "#666")
        .attr("font-style", "italic");
        
      return;
    }

    // Clone nodes with initial positions
    const nodesCopy = localNodes.map((d, i) => {
      // Position selected node in center, others around it
      if (d.id === selectedNode.id) {
        return {
          ...d,
          x: width / 2,
          y: height / 2,
          vx: 0,
          vy: 0,
          fx: width / 2, // Fix selected node position initially
          fy: height / 2
        };
      } else {
        const angle = (i * 2 * Math.PI) / (localNodes.length - 1);
        const radius = 80;
        return {
          ...d,
          x: width / 2 + Math.cos(angle) * radius,
          y: height / 2 + Math.sin(angle) * radius,
          vx: 0,
          vy: 0
        };
      }
    });

    // Create local simulation with stronger forces
    const localSimulation = d3.forceSimulation(nodesCopy)
      .force("link", d3.forceLink(localEdges.map(d => ({...d}))).id((d: any) => d.id).distance(80).strength(1))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2).strength(0.1))
      .force("collision", d3.forceCollide().radius(20))
      .force("x", d3.forceX(width / 2).strength(0.1))
      .force("y", d3.forceY(height / 2).strength(0.1))
      .alpha(1)
      .alphaDecay(0.02);

    // Create links
    const link = svg.append("g")
      .selectAll("line")
      .data(localEdges)
      .join("line")
      .attr("stroke", "#00ff00")
      .attr("stroke-opacity", 0.8)
      .attr("stroke-width", 2);

    // Create nodes
    const node = svg.append("g")
      .selectAll("g")
      .data(nodesCopy)
      .join("g")
      .attr("cursor", "pointer");

    // Add circles
    node.append("circle")
      .attr("r", (d: any) => d.id === selectedNode.id ? 15 : 10)
      .attr("fill", (d: any) => d.id === selectedNode.id ? "#ffff00" : getNodeColor(d))
      .attr("stroke", "#fff")
      .attr("stroke-width", 2)
      .style("filter", "drop-shadow(2px 2px 4px rgba(0,0,0,0.8))")
      .on("click", (event: any, d: any) => {
        if (d.id !== selectedNode.id) {
          focusOnNode(d.id);
        }
      })
      .on("mouseover", (event: any, d: any) => {
        d3.select(event.currentTarget).transition().duration(200).attr("r", d.id === selectedNode.id ? 18 : 12);
      })
      .on("mouseout", (event: any, d: any) => {
        d3.select(event.currentTarget).transition().duration(200).attr("r", d.id === selectedNode.id ? 15 : 10);
      });

    // Add background for text
    node.append("rect")
      .attr("x", (d: any) => -(getNodeLabel(d).substring(0, 8).length * 3.5))
      .attr("y", -20)
      .attr("width", (d: any) => getNodeLabel(d).substring(0, 8).length * 7)
      .attr("height", 14)
      .attr("fill", "rgba(0,0,0,0.9)")
      .attr("rx", 3)
      .style("pointer-events", "none");

    // Add labels
    node.append("text")
      .text((d: any) => getNodeLabel(d).substring(0, 8))
      .attr("font-size", 11)
      .attr("fill", "#00ff00")
      .attr("text-anchor", "middle")
      .attr("dy", -10)
      .attr("font-weight", "bold")
      .style("pointer-events", "none");

    // Release fixed position after a short time
    setTimeout(() => {
      const centerNode = nodesCopy.find(n => n.id === selectedNode.id);
      if (centerNode) {
        centerNode.fx = null;
        centerNode.fy = null;
      }
    }, 1000);

    // Update positions with bounds checking
    localSimulation.on("tick", () => {
      // Keep nodes within bounds
      nodesCopy.forEach(d => {
        d.x = Math.max(25, Math.min(width - 25, d.x || width/2));
        d.y = Math.max(25, Math.min(height - 25, d.y || height/2));
      });

      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      node
        .attr("transform", (d: any) => `translate(${d.x},${d.y})`);
    });

    // Stop simulation after it stabilizes
    setTimeout(() => {
      localSimulation.stop();
    }, 8000);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedNode, showLocalGraph, connectedNodes, panelWidth, getNodeColor]);

  // Update local graph when connections change
  useEffect(() => {
    if (showLocalGraph) {
      createLocalGraph();
    }
  }, [connectedNodes, showLocalGraph, selectedNode, panelWidth, createLocalGraph]);

  // Handle panel resizing
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      
      const newWidth = window.innerWidth - e.clientX;
      const minWidth = 300;
      const maxWidth = window.innerWidth * 0.8;
      
      setPanelWidth(Math.max(minWidth, Math.min(maxWidth, newWidth)));
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'ew-resize';
      document.body.style.userSelect = 'none';
    } else {
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing]);

  // Focus on a specific node from connections
  const focusOnNode = useCallback((nodeId: string) => {
    const node = graphData?.nodes.find(n => n.id === nodeId);
    if (node && svgRef.current && zoomBehaviorRef.current) {
      const d3 = require('d3');
      const svg = d3.select(svgRef.current);
      
      // Find node position in simulation
      const simulationNode = simulationRef.current?.nodes()?.find((n: any) => n.id === nodeId);
      if (simulationNode) {
        const scale = 2.5;
        const [x, y] = [simulationNode.x || 0, simulationNode.y || 0];
        
        svg.transition()
          .duration(750)
          .call(
            zoomBehaviorRef.current.transform,
            d3.zoomIdentity
              .translate(960, 540) // width/2, height/2
              .scale(scale)
              .translate(-x, -y)
          );
      }
      
      setSelectedNode(node);
      setShowFullContent(false);
      setShowLocalGraph(false);
    }
  }, [graphData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="text-green-400 text-xl mb-4">Загрузка данных графа...</div>
          <div className="flex justify-center">
            <div className="w-3 h-3 bg-green-400 rounded-full animate-bounce mx-1"></div>
            <div className="w-3 h-3 bg-green-400 rounded-full animate-bounce mx-1" style={{ animationDelay: '0.1s' }}></div>
            <div className="w-3 h-3 bg-green-400 rounded-full animate-bounce mx-1" style={{ animationDelay: '0.2s' }}></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="text-red-400 mb-4 text-xl">Ошибка: {error}</div>
          <button 
            onClick={loadGraphData}
            className="px-6 py-3 bg-green-600 hover:bg-green-500 text-black font-bold rounded border-2 border-green-400"
          >
            ПОВТОРИТЬ
          </button>
        </div>
      </div>
    );
  }

  if (!graphData) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-green-400 text-xl">Нет данных для отображения</div>
      </div>
    );
  }

  return (
    <div className="flex h-full">
      {/* Search panel */}
      {showSearchPanel && (
        <div className="w-80 bg-black border-r border-green-500 flex flex-col h-full overflow-hidden">
          <div className="p-4 pb-2 flex-shrink-0">
            <h3 className="text-green-400 font-bold mb-3">ПОИСК И ФИЛЬТРЫ</h3>
            
            {/* Поиск */}
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Поиск по узлам..."
                className="flex-1 min-w-0 bg-gray-900 border border-green-500 rounded px-3 py-2 text-green-400 placeholder-green-600 focus:outline-none focus:border-green-300 text-sm"
              />
              {(searchQuery || selectedTypes.length > 0) && (
                <button
                  onClick={clearAllFilters}
                  className="px-2 py-1 bg-red-600 hover:bg-red-500 text-white text-xs rounded border border-red-400 transition-all duration-200 flex-shrink-0"
                  title="Очистить все фильтры"
                >
                  ✕
                </button>
              )}
            </div>

            {/* Фильтры по типам */}
            <div className="overflow-hidden">
              <div className="flex justify-between items-center mb-2">
                <h4 className="text-green-300 text-sm font-bold flex-shrink-0">Типы узлов:</h4>
                <div className="flex gap-1 flex-shrink-0">
                  <button
                    onClick={() => setSelectedTypes(nodeTypes)}
                    className="px-2 py-1 text-xs bg-green-700 hover:bg-green-600 text-white rounded border border-green-500 transition-all duration-200"
                    title="Выбрать все типы"
                  >
                    Все
                  </button>
                  <button
                    onClick={() => setSelectedTypes([])}
                    className="px-2 py-1 text-xs bg-red-700 hover:bg-red-600 text-white rounded border border-red-500 transition-all duration-200"
                    title="Снять все фильтры"
                  >
                    Нет
                  </button>
                </div>
              </div>
              <div className="flex flex-wrap gap-1 overflow-hidden">
                {nodeTypes.map(type => {
                  const isSelected = selectedTypes.includes(type);
                  const count = graphData ? graphData.nodes.filter(n => n.type === type).length : 0;
                  
                  return (
                    <button
                      key={type}
                      onClick={() => toggleTypeFilter(type)}
                      className={`px-2 py-1 text-xs rounded border transition-all duration-200 flex-shrink-0 break-words max-w-full ${
                        isSelected 
                          ? type === 'Paper' ? 'bg-green-600 border-green-400 text-white' :
                            type === 'Entity' ? 'bg-blue-600 border-blue-400 text-white' :
                            type === 'Result' ? 'bg-yellow-600 border-yellow-400 text-black' :
                            type === 'Conclusion' ? 'bg-pink-600 border-pink-400 text-white' :
                            'bg-gray-600 border-gray-400 text-white'
                          : type === 'Paper' ? 'bg-gray-800 border-green-600 text-green-400 hover:bg-green-900' :
                            type === 'Entity' ? 'bg-gray-800 border-blue-600 text-blue-400 hover:bg-blue-900' :
                            type === 'Result' ? 'bg-gray-800 border-yellow-600 text-yellow-400 hover:bg-yellow-900' :
                            type === 'Conclusion' ? 'bg-gray-800 border-pink-600 text-pink-400 hover:bg-pink-900' :
                            'bg-gray-800 border-gray-600 text-gray-400 hover:bg-gray-700'
                      }`}
                      style={{ wordBreak: 'break-word' }}
                    >
                      {type} ({count})
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
          
          <div className="flex-1 overflow-hidden p-4 pt-2">
            <div className="text-green-300 text-sm font-bold mb-2">
              Найдено: {filteredNodes.length} из {graphData?.nodes.length || 0} узлов
              {selectedTypes.length > 0 && (
                <div className="text-xs text-gray-400 mt-1 break-words overflow-hidden">
                  Фильтр активен: {selectedTypes.join(', ')}
                </div>
              )}
            </div>
            
            <div className="h-full overflow-y-auto overflow-x-hidden space-y-1 pr-1">
              {filteredNodes.slice(0, 50).map((node) => (
                <div
                  key={node.id}
                  onClick={() => focusOnNodeFromSearch(node.id)}
                  className={`p-2 rounded border cursor-pointer transition-all duration-200 hover:bg-gray-800 overflow-hidden ${
                    selectedNode?.id === node.id 
                      ? 'border-yellow-400 bg-gray-800' 
                      : 'border-green-600 hover:border-green-400'
                  }`}
                >
                  <div className="text-xs overflow-hidden">
                    <div className={`font-bold break-words overflow-hidden ${
                      node.type === 'Paper' ? 'text-green-400' :
                      node.type === 'Entity' ? 'text-blue-400' :
                      node.type === 'Result' ? 'text-yellow-400' :
                      'text-pink-400'
                    }`} style={{ wordBreak: 'break-word', overflowWrap: 'break-word' }}>
                      {getNodeLabel(node)}
                    </div>
                    <div className="text-gray-400 break-words overflow-hidden" style={{ wordBreak: 'break-word', overflowWrap: 'break-word' }}>
                      {node.type} • {node.id.substring(0, 20)}...
                    </div>
                  </div>
                </div>
              ))}
              
              {filteredNodes.length > 50 && (
                <div className="text-gray-400 text-xs text-center py-2">
                  Показано первые 50 из {filteredNodes.length} результатов
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Main graph area */}
      <div 
        className="relative" 
        style={{ 
          width: selectedNode && !showSearchPanel ? `calc(100% - ${panelWidth}px)` : 
                 !selectedNode && showSearchPanel ? 'calc(100% - 320px)' :
                 selectedNode && showSearchPanel ? `calc(100% - ${panelWidth + 320}px)` : 
                 '100%',
          transition: 'width 0.2s ease-in-out'
        }}
      >
        <div className="absolute inset-0 w-full h-full overflow-hidden">
          <svg 
            ref={svgRef} 
            width="100%" 
            height="100%" 
            className="cursor-move"
            style={{ display: 'block' }}
          >
            {/* D3 will render content here */}
          </svg>
          
          {/* Controls overlay */}
          <div className="absolute top-2 left-2 text-green-400 text-xs font-mono bg-black bg-opacity-90 p-2 rounded border border-green-400 max-w-xs">
            <div className="mb-1 font-bold text-sm">Управление:</div>
            <div>• Перетаскивание узлов</div>
            <div>• Масштаб: колесо мыши</div>
            <div>• Панорама: перетаскивание</div>
            <div>• Клик по узлу: приближение</div>
            <div className="text-xs text-green-300 mt-1">
              • Ctrl+F: поиск • Esc: закрыть
            </div>
            <button 
              onClick={() => setShowSearchPanel(!showSearchPanel)}
              className="mt-1 px-2 py-1 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded border border-blue-400 transition-all duration-200 w-full"
            >
              {showSearchPanel ? 'Скрыть панель' : 'Поиск и фильтры'}
            </button>
          </div>

          {/* Legend */}
          <div className="absolute top-2 right-2 text-green-400 text-xs font-mono bg-black bg-opacity-90 p-2 rounded border border-green-400">
            <div className="mb-1 font-bold text-sm">Типы узлов:</div>
            <div className="flex items-center mb-0.5">
              <div className="w-3 h-3 bg-green-400 rounded-full mr-1.5"></div>
              <span>Статьи</span>
            </div>
            <div className="flex items-center mb-0.5">
              <div className="w-3 h-3 bg-blue-400 rounded-full mr-1.5"></div>
              <span>Сущности</span>
            </div>
            <div className="flex items-center mb-0.5">
              <div className="w-3 h-3 bg-yellow-400 rounded-full mr-1.5"></div>
              <span>Результаты</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-pink-400 rounded-full mr-1.5"></div>
              <span>Выводы</span>
            </div>
          </div>

          {/* Stats */}
          <div className="absolute bottom-2 right-2 text-green-400 text-xs font-mono bg-black bg-opacity-90 p-2 rounded border border-green-400 max-w-xs">
            <div>Узлы: {graphData.nodes.length}</div>
            <div>Связи: {graphData.edges.length}</div>
            {highlightPapers.length > 0 && (
              <div className="text-yellow-400 mt-1">
                Подсвечено: {highlightPapers.length}
              </div>
            )}
            {selectedNode && (
              <div className="text-yellow-400 mt-1 break-words">
                Выбран: {getNodeLabel(selectedNode).substring(0, 15)}...
              </div>
            )}
            {showSearchPanel && (
              <div className="text-blue-400 mt-1 break-words">
                Найдено: {filteredNodes.length}
                {selectedTypes.length > 0 && ` (фильтр: ${selectedTypes.length} типов)`}
              </div>
            )}
          </div>

          {/* Control buttons */}
          <div className="absolute bottom-2 left-2 flex flex-col space-y-2">
            <button 
              onClick={resetZoom}
              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-bold rounded border border-blue-400 transition-all duration-200"
            >
              СБРОСИТЬ ВИД
            </button>
            <button 
              onClick={loadGraphData}
              className="px-3 py-1.5 bg-green-600 hover:bg-green-500 text-white text-sm font-bold rounded border border-green-400 transition-all duration-200"
            >
              ОБНОВИТЬ
            </button>
          </div>
        </div>
      </div>

      {/* Node details panel */}
      {selectedNode && (
        <div 
          className="bg-black border-l border-green-500 overflow-y-auto relative"
          style={{ width: `${panelWidth}px` }}
        >
          {/* Resize handle */}
          <div
            ref={resizeHandleRef}
            className="absolute left-0 top-0 w-1 h-full bg-green-500 hover:bg-green-400 cursor-ew-resize z-10 opacity-50 hover:opacity-100 transition-opacity"
            onMouseDown={() => setIsResizing(true)}
          />
                    {/* Header */}
          <div className="sticky top-0 bg-black border-b border-green-500 p-4">
            <div className="flex justify-between items-center">
              <div>
                <h4 className="text-green-400 font-bold">ДЕТАЛИ УЗЛА</h4>
                <div className="text-xs text-gray-400 mt-1">
                  ← Потяните край для изменения размера
                </div>
              </div>
              <button 
                onClick={() => {
                  setSelectedNode(null);
                  setShowFullContent(false);
                  setShowLocalGraph(false);
                }}
                className="text-green-400 hover:text-green-300 text-xl"
              >
                ×
              </button>
            </div>
          </div>

          <div className="p-4 space-y-4">
            {/* Graph Overview */}
            <div className="bg-gray-900 p-3 rounded border border-green-600">
              <h5 className="text-green-400 font-bold mb-2 text-sm">ОБЗОР ГРАФА</h5>
              <div className="text-xs text-green-300 space-y-1">
                <div>Всего узлов: {graphData?.nodes.length || 0}</div>
                <div>Всего связей: {graphData?.edges.length || 0}</div>
                <div>Типы узлов: {[...new Set(graphData?.nodes.map(n => n.type) || [])].join(', ')}</div>
                {graphData?.edges.some(e => e.type) && (
                  <div>Типы связей: {[...new Set(graphData?.edges.map(e => e.type).filter(Boolean) || [])].join(', ')}</div>
                )}
              </div>
            </div>

            {/* Basic Info */}
            <div className="space-y-3 text-sm text-green-300">
              <div>
                <span className="text-green-500 font-mono">ID:</span>
                <div className="text-xs break-words">{selectedNode.id}</div>
              </div>
              
              <div>
                <span className="text-green-500 font-mono">Тип:</span>
                <div>{selectedNode.type}</div>
              </div>
              
              {selectedNode.canonical_name && (
                <div>
                  <span className="text-green-500 font-mono">Название:</span>
                  <div>{selectedNode.canonical_name}</div>
                </div>
              )}
              
              {selectedNode.entity_type && (
                <div>
                  <span className="text-green-500 font-mono">Тип сущности:</span>
                  <div>{selectedNode.entity_type}</div>
                </div>
              )}
              
              {selectedNode.year && (
                <div>
                  <span className="text-green-500 font-mono">Год:</span>
                  <div>{selectedNode.year}</div>
                </div>
              )}
              
              {selectedNode.statement && (
                <div>
                  <span className="text-green-500 font-mono">Утверждение:</span>
                  <div className="text-xs">{selectedNode.statement}</div>
                </div>
              )}
              
              {selectedNode.content && (
                <div>
                  <span className="text-green-500 font-mono">Содержание:</span>
                  <div className="text-xs">
                    {showFullContent 
                      ? selectedNode.content 
                      : selectedNode.content.length > 300 
                        ? `${selectedNode.content.substring(0, 300)}...` 
                        : selectedNode.content
                    }
                  </div>
                  {selectedNode.content.length > 300 && (
                    <button 
                      onClick={() => setShowFullContent(!showFullContent)}
                      className="text-green-400 hover:text-green-300 text-xs mt-1 underline"
                    >
                      {showFullContent ? 'Свернуть' : 'Показать полностью'}
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Connection Stats */}
            <div className="border-t border-green-500 pt-4">
              <h5 className="text-green-400 font-bold mb-2">СВЯЗИ</h5>
              <div className="text-xs text-green-300 space-y-1">
                <div>Входящие: {connectedNodes.incoming.length}</div>
                <div>Исходящие: {connectedNodes.outgoing.length}</div>
                <div>Всего: {connectedNodes.incoming.length + connectedNodes.outgoing.length}</div>
              </div>
              
              {/* Local graph toggle */}
              {(connectedNodes.incoming.length + connectedNodes.outgoing.length) > 0 && (
                <button
                  onClick={() => setShowLocalGraph(!showLocalGraph)}
                  className="mt-2 px-3 py-1 text-xs bg-green-600 hover:bg-green-500 text-black font-bold rounded border border-green-400 transition-all duration-200"
                >
                  {showLocalGraph ? 'Скрыть граф' : 'Показать локальный граф'}
                </button>
              )}
            </div>

            {/* Local Graph */}
            {showLocalGraph && (connectedNodes.incoming.length + connectedNodes.outgoing.length) > 0 && (
              <div className="border-t border-green-500 pt-4">
                <h5 className="text-green-400 font-bold mb-2">ЛОКАЛЬНЫЙ ГРАФ</h5>
                <div className="bg-gray-900 p-3 rounded border border-green-600">
                  <svg
                    ref={localGraphRef}
                    width="100%"
                    height={Math.max(250, Math.min(400, panelWidth * 0.6))}
                    className="w-full"
                    style={{ 
                      background: '#0a0a0a', 
                      border: '1px solid #333',
                      minHeight: '250px',
                      display: 'block'
                    }}
                    preserveAspectRatio="xMidYMid meet"
                  />
                  <div className="text-xs text-gray-400 mt-2 text-center">
                    🟡 Текущий узел | Клик для перехода к соседям
                    <div className="mt-1">
                      Узлов: {connectedNodes.incoming.length + connectedNodes.outgoing.length + 1}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Incoming connections */}
            {connectedNodes.incoming.length > 0 && (
              <div className="border-t border-green-500 pt-4">
                <h5 className="text-green-400 font-bold mb-2">ВХОДЯЩИЕ СВЯЗИ ←</h5>
                <div className="space-y-2">
                  {connectedNodes.incoming.map((connection, index) => (
                    <div key={index} className="bg-gray-900 p-2 rounded border border-green-600">
                      <button
                        onClick={() => focusOnNode(connection.node.id)}
                        className="text-green-300 hover:text-green-100 text-xs font-mono cursor-pointer block w-full text-left"
                      >
                        {getNodeLabel(connection.node)}
                      </button>
                      <div className="text-xs text-green-500 mt-1">
                        Тип: {connection.node.type}
                        {connection.edge.type && (
                          <span className="ml-2 text-blue-400">Связь: {connection.edge.type}</span>
                        )}
                      </div>
                      {connection.edge.context && (
                        <div className="text-xs text-gray-400 mt-1">
                          Контекст: {connection.edge.context}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Outgoing connections */}
            {connectedNodes.outgoing.length > 0 && (
              <div className="border-t border-green-500 pt-4">
                <h5 className="text-green-400 font-bold mb-2">ИСХОДЯЩИЕ СВЯЗИ →</h5>
                <div className="space-y-2">
                  {connectedNodes.outgoing.map((connection, index) => (
                    <div key={index} className="bg-gray-900 p-2 rounded border border-green-600">
                      <button
                        onClick={() => focusOnNode(connection.node.id)}
                        className="text-green-300 hover:text-green-100 text-xs font-mono cursor-pointer block w-full text-left"
                      >
                        {getNodeLabel(connection.node)}
                      </button>
                      <div className="text-xs text-green-500 mt-1">
                        Тип: {connection.node.type}
                        {connection.edge.type && (
                          <span className="ml-2 text-blue-400">Связь: {connection.edge.type}</span>
                        )}
                      </div>
                      {connection.edge.context && (
                        <div className="text-xs text-gray-400 mt-1">
                          Контекст: {connection.edge.context}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* No connections message */}
            {connectedNodes.incoming.length === 0 && connectedNodes.outgoing.length === 0 && (
              <div className="border-t border-green-500 pt-4">
                <div className="text-gray-400 text-xs text-center">
                  Нет связей с другими узлами
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
} 