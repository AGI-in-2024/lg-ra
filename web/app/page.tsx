'use client';

import { useState, useEffect, useRef } from 'react';

interface Message {
  id: number;
  text: string;
  isBot: boolean;
  timestamp: Date;
}

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

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: "Мы верим, что мультиагентные системы и контекстная инженерия способны создать лекарство от старости. На хакатоне мы собираем исследователей, разработчиков и биологов, чтобы вместе двигаться к цели, которая кажется невозможной — но только до тех пор, пока не станет нормой.",
      isBot: true,
      timestamp: new Date()
    },
    {
      id: 2,
      text: "Интересная концепция! Как планируете интегрировать AI-агентов в биомедицинские исследования?",
      isBot: false,
      timestamp: new Date()
    },
    {
      id: 3,
      text: "После мероприятия мы продолжим формулировать задачи (будем рады вашим!) и искать лучшие решения: это не разовая история, но начало коллективной работы.",
      isBot: true,
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showGraph, setShowGraph] = useState(false);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);

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

  // Initialize D3 force simulation
  useEffect(() => {
    if (!graphData || !svgRef.current || !showGraph) {
      return;
    }

    const d3 = require('d3');
    const svg = d3.select(svgRef.current);
    const width = 1920;
    const height = 1080;
    
    // Clear previous content
    svg.selectAll("*").remove();
    
    // Create container for zoom/pan
    const container = svg.append("g");
    
    // Setup zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([0.1, 4])
      .on("zoom", (event: any) => {
        container.attr("transform", event.transform);
      });
    
    svg.call(zoom);
    
    // Clone data to avoid mutations
    const nodes = graphData.nodes.map(d => ({...d}));
    const links = graphData.edges.map(d => ({...d}));
    
    // Create force simulation
    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id((d: any) => d.id).distance(60))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(15));

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
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5)
      .on("click", (event: any, d: GraphNode) => {
        setSelectedNode(d);
        event.stopPropagation();
      })
      .on("mouseover", (event: any, d: GraphNode) => {
        d3.select(event.currentTarget)
          .transition()
          .duration(200)
          .attr("r", getNodeSize(d) * 1.5);
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

    // Cleanup function
    return () => {
      simulation.stop();
    };

  }, [graphData, showGraph]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = () => {
    if (inputMessage.trim()) {
      const newMessage: Message = {
        id: messages.length + 1,
        text: inputMessage,
        isBot: false,
        timestamp: new Date()
      };
      setMessages([...messages, newMessage]);
      setInputMessage('');
      
      // Simulate bot typing
      setIsTyping(true);
      setTimeout(() => {
        setIsTyping(false);
        const botResponse: Message = {
          id: messages.length + 2,
          text: "Спасибо за ваш вопрос! Это важное направление для развития биомедицинских технологий.",
          isBot: true,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, botResponse]);
      }, 2000);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const toggleGraph = () => {
    if (!graphData && !loading) {
      loadGraphData();
    }
    setShowGraph(!showGraph);
  };

  const getNodeColor = (node: GraphNode) => {
    switch (node.type) {
      case 'Paper': return '#00ff00';
      case 'Entity': return '#00ccff';
      case 'Result': return '#ffaa00';
      case 'Conclusion': return '#ff00aa';
      default: return '#888888';
    }
  };

  const getNodeSize = (node: GraphNode) => {
    switch (node.type) {
      case 'Paper': return 12;
      case 'Entity': return 8;
      case 'Result': return 6;
      case 'Conclusion': return 6;
      default: return 5;
    }
  };

  const getNodeLabel = (node: GraphNode) => {
    if (node.canonical_name) return node.canonical_name;
    if (node.name) return node.name;
    if (node.type === 'Paper') return `Paper ${node.year || ''}`;
    return node.type;
  };

  const GraphVisualization = () => (
    <div className="fixed inset-0 bg-black z-50 flex">
      {/* Main graph area */}
      <div className="flex-1 relative">
        {/* Header */}
        <div className="absolute top-4 left-4 z-10 flex justify-between items-center w-full pr-8">
          <h3 className="text-green-400 font-bold text-xl">ГРАФ ЗНАНИЙ ДОЛГОЛЕТИЯ</h3>
          <button 
            onClick={() => setShowGraph(false)}
            className="text-green-400 hover:text-green-300 text-2xl font-bold bg-black bg-opacity-75 px-3 py-1 rounded border border-green-400"
          >
            ×
          </button>
        </div>

        {loading && (
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
        )}

        {error && (
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
        )}

        {graphData && !loading && (
          <>
            <div className="absolute inset-0 w-full h-full">
              <svg 
                ref={svgRef} 
                width="100%" 
                height="100%" 
                viewBox="0 0 1920 1080"
                className="cursor-move"
              >
                {/* D3 will render content here */}
              </svg>
              
              {/* Controls overlay */}
              <div className="absolute top-20 left-4 text-green-400 text-sm font-mono bg-black bg-opacity-75 p-3 rounded border border-green-400">
                <div className="mb-2 font-bold">Управление:</div>
                <div>• Перетаскивание узлов</div>
                <div>• Масштаб: колесо мыши</div>
                <div>• Панорама: перетаскивание</div>
                <div>• Клик по узлу: информация</div>
              </div>

              {/* Legend */}
              <div className="absolute top-20 right-4 text-green-400 text-sm font-mono bg-black bg-opacity-75 p-3 rounded border border-green-400">
                <div className="mb-2 font-bold">Типы узлов:</div>
                <div className="flex items-center mb-1">
                  <div className="w-4 h-4 bg-green-400 rounded-full mr-2"></div>
                  <span>Статьи</span>
                </div>
                <div className="flex items-center mb-1">
                  <div className="w-4 h-4 bg-blue-400 rounded-full mr-2"></div>
                  <span>Сущности</span>
                </div>
                <div className="flex items-center mb-1">
                  <div className="w-4 h-4 bg-yellow-400 rounded-full mr-2"></div>
                  <span>Результаты</span>
                </div>
                <div className="flex items-center">
                  <div className="w-4 h-4 bg-pink-400 rounded-full mr-2"></div>
                  <span>Выводы</span>
                </div>
              </div>

              {/* Stats */}
              <div className="absolute bottom-4 right-4 text-green-400 text-sm font-mono bg-black bg-opacity-75 p-3 rounded border border-green-400">
                <div>Узлы: {graphData.nodes.length}</div>
                <div>Связи: {graphData.edges.length}</div>
              </div>

              {/* Control buttons */}
              <div className="absolute bottom-4 left-4 flex space-x-3">
                <button 
                  onClick={() => setShowGraph(false)}
                  className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white font-bold rounded border-2 border-red-400 transition-all duration-200"
                >
                  ЗАКРЫТЬ
                </button>
                <button 
                  onClick={loadGraphData}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded border-2 border-blue-400 transition-all duration-200"
                >
                  ОБНОВИТЬ
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Node details panel */}
      {selectedNode && (
        <div className="w-80 bg-black border-l border-green-500 p-4 overflow-y-auto">
          <div className="flex justify-between items-center mb-3">
            <h4 className="text-green-400 font-bold">ДЕТАЛИ УЗЛА</h4>
            <button 
              onClick={() => setSelectedNode(null)}
              className="text-green-400 hover:text-green-300 text-xl"
            >
              ×
            </button>
          </div>
          
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
                <div className="text-xs">{selectedNode.content.substring(0, 300)}...</div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-black text-green-400 font-mono relative">
      {/* Animated background particles */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-2 h-2 bg-green-400 rounded-full opacity-20 animate-ping"></div>
        <div className="absolute top-3/4 right-1/4 w-1 h-1 bg-green-300 rounded-full opacity-30 animate-pulse"></div>
        <div className="absolute top-1/2 left-3/4 w-3 h-3 bg-green-500 rounded-full opacity-10 animate-bounce"></div>
      </div>

      {/* Header */}
      <div className="border-b border-green-500 p-4 relative z-10">
        <h1 className="text-2xl font-bold text-green-400 pixel-text">
          ДЛЯ ПРОДЛЕНИЯ ЖИЗНИ
        </h1>
        <div className="text-sm text-green-300 mt-2">
          Ваша идея может изменить биомедицину. Присоединяйтесь.
        </div>
        <div className="absolute right-4 top-4">
          <div className="w-8 h-8 border-2 border-green-400 rounded-full flex items-center justify-center">
            <div className="w-4 h-4 bg-green-400 rounded-full pulse-glow"></div>
          </div>
        </div>
      </div>

      {/* Chat Container */}
      <div className="flex flex-col h-[calc(100vh-120px)] relative z-10">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message, index) => (
            <div 
              key={message.id} 
              className={`flex ${message.isBot ? 'justify-start' : 'justify-end'} message-bubble`}
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className={`flex items-start space-x-3 max-w-2xl ${message.isBot ? 'flex-row' : 'flex-row-reverse space-x-reverse'}`}>
                {/* Avatar */}
                <div className={`w-12 h-12 rounded-full border-2 border-green-400 flex items-center justify-center relative ${
                  message.isBot ? 'bg-green-900' : 'bg-green-800'
                }`}>
                  <div className="w-6 h-6 bg-green-400 rounded-full pixel-avatar"></div>
                  {/* Status indicator */}
                  <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-400 border-2 border-black rounded-full"></div>
                </div>
                
                {/* Message Bubble */}
                <div className={`relative px-4 py-3 rounded-lg border-2 transition-all duration-300 hover:scale-105 ${
                  message.isBot 
                    ? 'bg-gray-800 border-green-500 text-green-300 hover:border-green-400' 
                    : 'bg-green-900 border-green-400 text-green-100 hover:border-green-300'
                }`}>
                  <div className="text-sm leading-relaxed">{message.text}</div>
                  <div className="text-xs text-green-500 mt-2 opacity-70">
                    {message.timestamp.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
                  </div>
                  
                  {/* Message corner decoration */}
                  <div className={`absolute w-3 h-3 border-l-2 border-b-2 border-green-400 transform rotate-45 ${
                    message.isBot ? '-left-1 top-4' : '-right-1 top-4'
                  }`}></div>
                </div>
              </div>
            </div>
          ))}
          
          {/* Typing indicator */}
          {isTyping && (
            <div className="flex justify-start message-bubble">
              <div className="flex items-start space-x-3 max-w-2xl">
                <div className="w-12 h-12 rounded-full border-2 border-green-400 flex items-center justify-center bg-green-900">
                  <div className="w-6 h-6 bg-green-400 rounded-full pixel-avatar"></div>
                </div>
                <div className="relative px-4 py-3 rounded-lg border-2 bg-gray-800 border-green-500 text-green-300">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-green-500 p-4 bg-gray-900 bg-opacity-90">
          <div className="flex space-x-4">
            <div className="flex-1 relative">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Запрос..."
                className="w-full bg-black border-2 border-green-500 rounded-lg px-4 py-3 text-green-400 placeholder-green-600 resize-none focus:outline-none focus:border-green-300 font-mono transition-all duration-300"
                rows={2}
              />
              {inputMessage && (
                <div className="absolute right-2 bottom-2 text-green-500 text-xs terminal-cursor">
                  {inputMessage.length}
                </div>
              )}
            </div>
            <button
              onClick={sendMessage}
              disabled={!inputMessage.trim()}
              className="px-6 py-3 bg-green-600 hover:bg-green-500 text-black font-bold rounded-lg border-2 border-green-400 transition-all duration-200 hover:shadow-lg hover:shadow-green-500/50 pixel-button disabled:opacity-50 disabled:cursor-not-allowed"
            >
              ОТПРАВИТЬ
            </button>
          </div>
          
          {/* Graph Button */}
          <div className="mt-4 flex justify-center">
            <button 
              onClick={toggleGraph}
              className="px-8 py-3 bg-green-500 hover:bg-green-400 text-black font-bold rounded-lg border-2 border-green-300 transition-all duration-200 hover:shadow-lg hover:shadow-green-400/50 pixel-button"
            >
              ОТОБРАЗИТЬ ГРАФ ЗНАНИЙ
            </button>
          </div>
        </div>
      </div>

      {/* Graph Modal */}
      {showGraph && <GraphVisualization />}
    </div>
  );
}
