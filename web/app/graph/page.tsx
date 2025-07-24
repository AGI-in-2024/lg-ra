'use client';

import GraphVisualization from '../components/GraphVisualization';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';

function GraphContent() {
  const searchParams = useSearchParams();
  const focusNodeId = searchParams.get('focus');
  const highlightPapers = searchParams.get('highlight')?.split(',') || [];
  const openSearch = searchParams.get('search') === 'open';
  return (
    <div className="min-h-screen bg-black text-green-400 font-mono">
      {/* Header */}
      <div className="border-b border-green-500 p-4 relative z-10">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-green-400 pixel-text">
              ГРАФ ЗНАНИЙ ДОЛГОЛЕТИЯ
            </h1>
            <div className="text-sm text-green-300 mt-2">
              Интерактивная визуализация научных знаний
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <Link 
              href="/report"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-black font-bold rounded border-2 border-blue-400 transition-all duration-200"
            >
              ОТЧЕТ
            </Link>
            <Link 
              href="/"
              className="px-4 py-2 bg-green-600 hover:bg-green-500 text-black font-bold rounded border-2 border-green-400 transition-all duration-200"
            >
              Главная
            </Link>
          </div>
        </div>
      </div>

      {/* Graph Container */}
      <div className="h-[calc(100vh-100px)]">
        <GraphVisualization 
          focusNodeId={focusNodeId || undefined}
          highlightPapers={highlightPapers}
          openSearch={openSearch}
        />
      </div>
    </div>
  );
}

export default function GraphPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-black text-green-400 font-mono flex items-center justify-center">Loading...</div>}>
      <GraphContent />
    </Suspense>
  );
}