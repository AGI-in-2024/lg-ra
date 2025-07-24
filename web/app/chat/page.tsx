'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import ContextSelector from '../components/ContextSelector';

interface Message {
  id: number;
  text: string;
  isBot: boolean;
  timestamp: Date;
}

// Компонент для рендеринга Markdown с терминальными стилями
const MarkdownRenderer = ({ content }: { content: string }) => {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        // Заголовки
        h1: ({ children }) => (
          <h1 className="text-xl font-bold text-green-300 mb-2 border-b border-green-600 pb-1">
            {children}
          </h1>
        ),
        h2: ({ children }) => (
          <h2 className="text-lg font-bold text-green-300 mb-2 border-b border-green-700 pb-1">
            {children}
          </h2>
        ),
        h3: ({ children }) => (
          <h3 className="text-base font-bold text-green-300 mb-1">
            {children}
          </h3>
        ),
        h4: ({ children }) => (
          <h4 className="text-sm font-bold text-green-300 mb-1">
            {children}
          </h4>
        ),
        h5: ({ children }) => (
          <h5 className="text-sm font-bold text-green-400 mb-1">
            {children}
          </h5>
        ),
        h6: ({ children }) => (
          <h6 className="text-xs font-bold text-green-400 mb-1">
            {children}
          </h6>
        ),
        
        // Параграфы
        p: ({ children }) => (
          <p className="mb-2 leading-relaxed">
            {children}
          </p>
        ),
        
        // Списки
        ul: ({ children }) => (
          <ul className="list-none ml-4 mb-2 space-y-1">
            {children}
          </ul>
        ),
        ol: ({ children }) => (
          <ol className="list-none ml-4 mb-2 space-y-1 counter-reset-list">
            {children}
          </ol>
        ),
        li: ({ children }) => (
          <li className="flex items-start">
            <span className="text-green-400 mr-2 flex-shrink-0">
              ►
            </span>
            <span className="flex-1">{children}</span>
          </li>
        ),
        
        // Код
        code: ({ children, className }) => {
          const isInline = !className?.includes('language-');
          return isInline ? (
            <code className="bg-gray-900 text-green-300 px-1 py-0.5 rounded border border-green-600 font-mono text-xs">
              {children}
            </code>
          ) : (
            <code className="block bg-gray-900 text-green-300 p-2 rounded border border-green-600 font-mono text-xs overflow-x-auto">
              {children}
            </code>
          );
        },
        pre: ({ children }) => (
          <pre className="bg-gray-900 text-green-300 p-3 rounded border border-green-600 overflow-x-auto mb-2 font-mono text-xs">
            {children}
          </pre>
        ),
        
        // Блоки цитат
        blockquote: ({ children }) => (
          <blockquote className="border-l-4 border-green-500 pl-4 py-2 bg-gray-900 bg-opacity-50 italic text-green-200 mb-2">
            {children}
          </blockquote>
        ),
        
        // Ссылки
        a: ({ href, children }) => (
          <a 
            href={href} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-green-400 hover:text-green-300 underline hover:no-underline transition-colors"
          >
            {children}
          </a>
        ),
        
        // Выделение текста
        strong: ({ children }) => (
          <strong className="font-bold text-green-300">
            {children}
          </strong>
        ),
        em: ({ children }) => (
          <em className="italic text-green-200">
            {children}
          </em>
        ),
        
        // Таблицы
        table: ({ children }) => (
          <div className="overflow-x-auto mb-2">
            <table className="min-w-full border border-green-600 text-xs">
              {children}
            </table>
          </div>
        ),
        thead: ({ children }) => (
          <thead className="bg-green-900 bg-opacity-50">
            {children}
          </thead>
        ),
        tbody: ({ children }) => (
          <tbody>
            {children}
          </tbody>
        ),
        tr: ({ children }) => (
          <tr className="border-b border-green-700">
            {children}
          </tr>
        ),
        th: ({ children }) => (
          <th className="border border-green-600 px-2 py-1 text-left font-bold text-green-300">
            {children}
          </th>
        ),
        td: ({ children }) => (
          <td className="border border-green-600 px-2 py-1">
            {children}
          </td>
        ),
        
        // Горизонтальная линия
        hr: () => (
          <hr className="border-0 border-t border-green-600 my-4" />
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  );
};

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState('');
  const [selectedContextType, setSelectedContextType] = useState('report');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Загружаем данные из localStorage при первом рендере
  useEffect(() => {
    const savedMessages = localStorage.getItem('chat-messages');
    const savedDataset = localStorage.getItem('chat-dataset');
    const savedContextType = localStorage.getItem('chat-context-type');

    if (savedMessages) {
      try {
        const parsedMessages = JSON.parse(savedMessages).map((msg: Omit<Message, 'timestamp'> & { timestamp: string }) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }));
        setMessages(parsedMessages);
      } catch (error) {
        console.error('Error loading messages from localStorage:', error);
        // Если ошибка - добавляем приветственное сообщение
        setMessages([{
          id: 1,
          text: "Привет! Я ИИ-ассистент для анализа биомедицинских исследований. Выберите датасет и тип данных для контекста, затем задайте свой вопрос.",
          isBot: true,
          timestamp: new Date()
        }]);
      }
    } else {
      // Если нет сохраненных сообщений - добавляем приветственное сообщение
      setMessages([{
        id: 1,
        text: "Привет! Я ИИ-ассистент для анализа биомедицинских исследований. Выберите датасет и тип данных для контекста, затем задайте свой вопрос.",
        isBot: true,
        timestamp: new Date()
      }]);
    }

    if (savedDataset) {
      setSelectedDataset(savedDataset);
    }
    if (savedContextType) {
      setSelectedContextType(savedContextType);
    }
  }, []);

  // Сохраняем сообщения в localStorage при их изменении
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem('chat-messages', JSON.stringify(messages));
    }
  }, [messages]);

  // Сохраняем настройки контекста в localStorage
  useEffect(() => {
    if (selectedDataset) {
      localStorage.setItem('chat-dataset', selectedDataset);
    } else {
      localStorage.removeItem('chat-dataset');
    }
  }, [selectedDataset]);

  useEffect(() => {
    localStorage.setItem('chat-context-type', selectedContextType);
  }, [selectedContextType]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleContextChange = (dataset: string, contextType: string) => {
    setSelectedDataset(dataset);
    setSelectedContextType(contextType);
    
    // Добавляем сообщение о смене контекста
    if (dataset) {
      const contextMessage: Message = {
        id: Date.now(),
        text: `Контекст изменен: ${dataset.toUpperCase()} / ${contextType.toUpperCase()}`,
        isBot: true,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, contextMessage]);
    }
  };

  const clearChatHistory = () => {
    setMessages([{
      id: 1,
      text: "Привет! Я ИИ-ассистент для анализа биомедицинских исследований. Выберите датасет и тип данных для контекста, затем задайте свой вопрос.",
      isBot: true,
      timestamp: new Date()
    }]);
    localStorage.removeItem('chat-messages');
  };

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage: Message = {
      id: Date.now(),
      text: inputMessage,
      isBot: false,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          dataset: selectedDataset,
          contextType: selectedContextType
        }),
      });

      const data = await response.json();
      
      if (response.ok) {
        const botResponse: Message = {
          id: Date.now() + 1,
          text: data.response,
          isBot: true,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, botResponse]);
      } else {
        const errorMessage: Message = {
          id: Date.now() + 1,
          text: `Ошибка: ${data.error || 'Не удалось получить ответ'}`,
          isBot: true,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: Date.now() + 1,
        text: 'Ошибка соединения. Проверьте настройки API.',
        isBot: true,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="h-screen bg-black text-green-400 font-mono relative overflow-hidden">
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
              ИИ ЧАТ - БИОМЕДИЦИНСКИЕ ИССЛЕДОВАНИЯ
            </h1>
            <div className="text-sm text-green-300 mt-2">
              Анализ данных с помощью Gemini AI
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
            <button
              onClick={clearChatHistory}
              className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white font-bold rounded border-2 border-red-400 transition-all duration-200"
              title="Очистить историю чата"
            >
              ОЧИСТИТЬ ЧАТ
            </button>
            <div className="w-8 h-8 border-2 border-green-400 rounded-full flex items-center justify-center">
              <div className="w-4 h-4 bg-green-400 rounded-full pulse-glow"></div>
            </div>
          </div>
        </div>
      </div>

      {/* Context Selector */}
      <ContextSelector
        onContextChange={handleContextChange}
        selectedDataset={selectedDataset}
        selectedContextType={selectedContextType}
      />

      {/* Chat Container */}
      <div className="flex flex-col h-[calc(100vh-200px)] relative z-10">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message, index) => (
            <div 
              key={message.id} 
              className={`flex ${message.isBot ? 'justify-start' : 'justify-end'} message-bubble`}
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className={`flex items-start space-x-3 max-w-4xl ${message.isBot ? 'flex-row' : 'flex-row-reverse space-x-reverse'}`}>
                {/* Avatar */}
                <div className={`w-12 h-12 rounded-full border-2 border-green-400 flex items-center justify-center relative ${
                  message.isBot ? 'bg-green-900' : 'bg-green-800'
                }`}>
                  <div className="w-6 h-6 bg-green-400 rounded-full pixel-avatar"></div>
                  <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-400 border-2 border-black rounded-full"></div>
                </div>
                
                {/* Message Bubble */}
                <div className={`relative px-4 py-3 rounded-lg border-2 transition-all duration-300 hover:scale-105 ${
                  message.isBot 
                    ? 'bg-gray-800 border-green-500 text-green-300 hover:border-green-400' 
                    : 'bg-green-900 border-green-400 text-green-100 hover:border-green-300'
                }`}>
                  <div className="text-sm leading-relaxed">
                    {message.isBot ? (
                      <MarkdownRenderer content={message.text} />
                    ) : (
                      <div className="whitespace-pre-wrap">{message.text}</div>
                    )}
                  </div>
                  <div className="text-xs text-green-500 mt-2 opacity-70">
                    {message.timestamp.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
                  </div>
                  
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
                  <div className="flex items-center space-x-1">
                    <div className="text-xs">Анализирую данные</div>
                    <div className="flex space-x-1 ml-2">
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
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
                placeholder="Введите ваш вопрос о биомедицинских исследованиях..."
                className="w-full bg-black border-2 border-green-500 rounded-lg px-4 py-3 text-green-400 placeholder-green-600 resize-none focus:outline-none focus:border-green-300 font-mono transition-all duration-300"
                rows={2}
                disabled={isTyping}
              />
              {inputMessage && (
                <div className="absolute right-2 bottom-2 text-green-500 text-xs terminal-cursor">
                  {inputMessage.length}
                </div>
              )}
            </div>
            <button
              onClick={sendMessage}
              disabled={!inputMessage.trim() || isTyping}
              className="px-6 py-3 bg-green-600 hover:bg-green-500 text-black font-bold rounded-lg border-2 border-green-400 transition-all duration-200 hover:shadow-lg hover:shadow-green-500/50 pixel-button disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isTyping ? 'АНАЛИЗ...' : 'ОТПРАВИТЬ'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
} 