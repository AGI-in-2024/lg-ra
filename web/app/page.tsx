'use client';

import { useState, useEffect, useRef } from 'react';

interface Message {
  id: number;
  text: string;
  isBot: boolean;
  timestamp: Date;
}

interface Node {
  id: string;
  x: number;
  y: number;
  connections: string[];
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
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Generate random graph nodes
  const generateGraphNodes = (): Node[] => {
    const nodes: Node[] = [];
    const nodeCount = 12;
    
    for (let i = 0; i < nodeCount; i++) {
      const angle = (i / nodeCount) * 2 * Math.PI;
      const radius = 80 + Math.random() * 60;
      const centerX = 150;
      const centerY = 150;
      
      nodes.push({
        id: `node-${i}`,
        x: centerX + Math.cos(angle) * radius + (Math.random() - 0.5) * 40,
        y: centerY + Math.sin(angle) * radius + (Math.random() - 0.5) * 40,
        connections: []
      });
    }

    // Add random connections
    nodes.forEach((node, index) => {
      const connectionCount = Math.floor(Math.random() * 3) + 1;
      for (let i = 0; i < connectionCount; i++) {
        const targetIndex = Math.floor(Math.random() * nodeCount);
        if (targetIndex !== index && !node.connections.includes(`node-${targetIndex}`)) {
          node.connections.push(`node-${targetIndex}`);
        }
      }
    });

    return nodes;
  };

  const [graphNodes] = useState<Node[]>(generateGraphNodes());

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
    setShowGraph(!showGraph);
  };

  const GraphVisualization = () => (
    <div className="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50" onClick={() => setShowGraph(false)}>
      <div className="bg-black border-2 border-green-400 rounded-lg p-6 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-green-400 font-bold">ГРАФ СВЯЗЕЙ</h3>
          <button 
            onClick={() => setShowGraph(false)}
            className="text-green-400 hover:text-green-300 text-xl font-bold"
          >
            ×
          </button>
        </div>
        
        <div className="relative w-full h-80 bg-gray-900 border border-green-500 rounded">
          <svg className="w-full h-full">
            {/* Draw connections */}
            {graphNodes.map((node) =>
              node.connections.map((connectionId) => {
                const targetNode = graphNodes.find(n => n.id === connectionId);
                if (!targetNode) return null;
                
                return (
                  <line
                    key={`${node.id}-${connectionId}`}
                    x1={node.x}
                    y1={node.y}
                    x2={targetNode.x}
                    y2={targetNode.y}
                    stroke="#00ff00"
                    strokeWidth="1"
                    opacity="0.6"
                    className="animate-pulse"
                  />
                );
              })
            )}
            
            {/* Draw nodes */}
            {graphNodes.map((node, index) => (
              <g key={node.id}>
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={index === 0 ? "8" : index < 3 ? "6" : "4"}
                  fill="#00ff00"
                  className="animate-pulse"
                  style={{ animationDelay: `${index * 0.1}s` }}
                />
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={index === 0 ? "12" : index < 3 ? "10" : "8"}
                  fill="none"
                  stroke="#00ff00"
                  strokeWidth="1"
                  opacity="0.5"
                />
              </g>
            ))}
          </svg>
          
          {/* Overlay text */}
          <div className="absolute top-2 left-2 text-green-400 text-xs font-mono">
            Узлы: {graphNodes.length}
          </div>
          <div className="absolute bottom-2 right-2 text-green-400 text-xs font-mono">
            Связи: {graphNodes.reduce((acc, node) => acc + node.connections.length, 0)}
          </div>
        </div>
        
        <div className="mt-4 text-center">
          <button 
            onClick={() => setShowGraph(false)}
            className="px-4 py-2 bg-green-600 hover:bg-green-500 text-black font-bold rounded border-2 border-green-400 transition-all duration-200 pixel-button"
          >
            ЗАКРЫТЬ
          </button>
        </div>
      </div>
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
              ОТОБРАЗИТЬ ГРАФ
            </button>
          </div>
        </div>
      </div>

      {/* Graph Modal */}
      {showGraph && <GraphVisualization />}
    </div>
  );
}
