'use client';

import Link from 'next/link';
import Image from 'next/image';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-black text-green-400 font-mono relative">
      {/* Animated background particles */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-2 h-2 bg-green-400 rounded-full opacity-20 animate-ping"></div>
        <div className="absolute top-3/4 right-1/4 w-1 h-1 bg-green-300 rounded-full opacity-30 animate-pulse"></div>
        <div className="absolute top-1/2 left-3/4 w-3 h-3 bg-green-500 rounded-full opacity-10 animate-bounce"></div>
        <div className="absolute top-1/3 right-1/3 w-1 h-1 bg-green-400 rounded-full opacity-25 animate-ping"></div>
        <div className="absolute bottom-1/4 left-1/3 w-2 h-2 bg-green-300 rounded-full opacity-15 animate-pulse"></div>
      </div>

      {/* Header */}
      <div className="border-b border-green-500 p-6 relative z-10">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-6">
            <div className="w-40 h-40 flex-shrink-0">
              <Image 
                src="/image.png" 
                alt="Geronome Logo" 
                width={160} 
                height={160}
                className="w-full h-full object-contain"
              />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-green-400 pixel-text mb-2">
                Мы учим машины понимать старение, чтобы человечество могло его остановить
              </h1>
              <div className="text-lg text-green-300">
                Geronome — ии-система, которая анализирует биомедицинские данные, выявляет закономерности старения и помогает находить задачи, решение которых ведёт к долголетию
              </div>
            </div>
          </div>
          <div className="w-12 h-12 border-2 border-green-400 rounded-full flex items-center justify-center">
            <div className="w-6 h-6 bg-green-400 rounded-full pulse-glow"></div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-200px)] p-8 relative z-10">
        {/* Mission Statement */}
        <div className="max-w-4xl text-center mb-12">
          <h2 className="text-3xl font-bold text-green-300 mb-6">
            НАША МИССИЯ
          </h2>
          <p className="text-xl text-green-200 leading-relaxed mb-8">
            Мы верим, что мультиагентные системы и контекстная инженерия способны создать лекарство от старости. 
            На хакатоне мы собираем исследователей, разработчиков и биологов, чтобы вместе двигаться к цели, 
            которая кажется невозможной — но только до тех пор, пока не станет нормой.
          </p>
          <div className="text-lg text-green-300">
            После мероприятия мы продолжим формулировать задачи и искать лучшие решения: 
            это не разовая история, но начало коллективной работы.
          </div>
        </div>

        {/* Navigation Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl w-full">
          {/* Chat */}
          <Link href="/chat" className="group">
            <div className="border-2 border-green-500 rounded-lg p-6 bg-gray-900 hover:bg-gray-800 transition-all duration-300 hover:border-green-400 hover:scale-105">
              <div className="text-center">
                <div className="mb-4 flex justify-center group-hover:scale-110 transition-transform duration-300">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" className="text-green-400">
                    <path d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h4l4 4 4-4h4c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z" fill="currentColor"/>
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-green-400 mb-3">ЧАТ</h3>
                <p className="text-green-300 text-sm">
                  Обсуждение идей биомедицинских исследований и новых подходов
                </p>
              </div>
            </div>
          </Link>

          {/* Knowledge Graph */}
          <Link href="/graph" className="group">
            <div className="border-2 border-green-500 rounded-lg p-6 bg-gray-900 hover:bg-gray-800 transition-all duration-300 hover:border-green-400 hover:scale-105">
              <div className="text-center">
                <div className="mb-4 flex justify-center group-hover:rotate-12 transition-transform duration-300">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" className="text-green-400">
                    <circle cx="12" cy="12" r="3" fill="currentColor"/>
                    <circle cx="12" cy="5" r="2" fill="currentColor"/>
                    <circle cx="12" cy="19" r="2" fill="currentColor"/>
                    <circle cx="5" cy="12" r="2" fill="currentColor"/>
                    <circle cx="19" cy="12" r="2" fill="currentColor"/>
                    <circle cx="7.5" cy="7.5" r="1.5" fill="currentColor"/>
                    <circle cx="16.5" cy="7.5" r="1.5" fill="currentColor"/>
                    <circle cx="7.5" cy="16.5" r="1.5" fill="currentColor"/>
                    <circle cx="16.5" cy="16.5" r="1.5" fill="currentColor"/>
                    <path d="M12 9v6M9 12h6M8.5 8.5l7 7M15.5 8.5l-7 7" stroke="currentColor" strokeWidth="1" opacity="0.5"/>
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-green-400 mb-3">ГРАФ ЗНАНИЙ</h3>
                <p className="text-green-300 text-sm">
                  Интерактивная визуализация связей в биомедицинских исследованиях
                </p>
              </div>
            </div>
          </Link>

          {/* Research Report */}
          <Link href="/report" className="group">
            <div className="border-2 border-green-500 rounded-lg p-6 bg-gray-900 hover:bg-gray-800 transition-all duration-300 hover:border-green-400 hover:scale-105">
              <div className="text-center">
                <div className="mb-4 flex justify-center group-hover:scale-110 transition-transform duration-300">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" className="text-green-400">
                    <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z" fill="currentColor"/>
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-green-400 mb-3">ОТЧЕТ</h3>
                <p className="text-green-300 text-sm">
                  Анализ исследовательских направлений и их потенциала
                </p>
              </div>
            </div>
          </Link>
        </div>

        {/* Call to Action */}
        <div className="mt-12 text-center">
          <div className="text-lg text-green-300 mb-6">
            Готовы изменить будущее медицины?
          </div>
          <Link 
            href="/chat"
            className="px-8 py-4 bg-green-600 hover:bg-green-500 text-black font-bold text-xl rounded-lg border-2 border-green-400 transition-all duration-200 hover:shadow-lg hover:shadow-green-500/50 inline-block"
          >
            НАЧАТЬ ОБСУЖДЕНИЕ
          </Link>
        </div>

        {/* Stats */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 max-w-2xl w-full">
          <div className="text-center border border-green-600 rounded p-4">
            <div className="text-2xl font-bold text-green-400">AI</div>
            <div className="text-green-300 text-sm">Агенты</div>
          </div>
          <div className="text-center border border-green-600 rounded p-4">
            <div className="text-2xl font-bold text-green-400">∞</div>
            <div className="text-green-300 text-sm">Возможности</div>
          </div>
          <div className="text-center border border-green-600 rounded p-4">
            <div className="text-2xl font-bold text-green-400">+∞</div>
            <div className="text-green-300 text-sm">Лет жизни</div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-green-500 p-4 text-center text-green-400 text-sm relative z-10">
        <div>
          Вместе мы можем победить старость через науку и технологии
        </div>
      </div>
    </div>
  );
}
