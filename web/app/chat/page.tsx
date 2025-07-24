'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';

interface Message {
  id: number;
  text: string;
  isBot: boolean;
  timestamp: Date;
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
  const messagesEndRef = useRef<HTMLDivElement>(null);

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
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-green-400 pixel-text">
              ЧАТ - ДЛЯ ПРОДЛЕНИЯ ЖИЗНИ
            </h1>
            <div className="text-sm text-green-300 mt-2">
              Обсуждаем идеи биомедицинских исследований
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <Link 
              href="/"
              className="px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white font-bold rounded border-2 border-gray-400 transition-all duration-200"
            >
              ГЛАВНАЯ
            </Link>
            <Link 
              href="/graph"
              className="px-4 py-2 bg-green-600 hover:bg-green-500 text-black font-bold rounded border-2 border-green-400 transition-all duration-200"
            >
              ГРАФ ЗНАНИЙ
            </Link>
            <Link 
              href="/report"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-black font-bold rounded border-2 border-blue-400 transition-all duration-200"
            >
              ОТЧЕТ
            </Link>
            <div className="w-8 h-8 border-2 border-green-400 rounded-full flex items-center justify-center">
              <div className="w-4 h-4 bg-green-400 rounded-full pulse-glow"></div>
            </div>
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
        </div>
      </div>
    </div>
  );
} 