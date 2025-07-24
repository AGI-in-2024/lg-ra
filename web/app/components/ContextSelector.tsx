'use client';

import { useState, useEffect } from 'react';

interface ContextSelectorProps {
  onContextChange: (dataset: string, contextType: string) => void;
  selectedDataset: string;
  selectedContextType: string;
}

export default function ContextSelector({ 
  onContextChange, 
  selectedDataset, 
  selectedContextType 
}: ContextSelectorProps) {
  const [availableDatasets, setAvailableDatasets] = useState<string[]>([]);

  useEffect(() => {
    // Получаем список доступных датасетов
    async function fetchDatasets() {
      try {
        const response = await fetch('/api/datasets');
        if (response.ok) {
          const datasets = await response.json();
          setAvailableDatasets(datasets);
        }
      } catch (error) {
        console.error('Error fetching datasets:', error);
        // Fallback для dataset1
        setAvailableDatasets(['dataset1']);
      }
    }
    
    fetchDatasets();
  }, []);

  const handleDatasetChange = (dataset: string) => {
    onContextChange(dataset, selectedContextType);
  };

  const handleContextTypeChange = (contextType: string) => {
    onContextChange(selectedDataset, contextType);
  };

  return (
    <div className="border-b border-green-500 p-4 bg-gray-900 bg-opacity-90">
      <div className="text-green-400 text-sm font-bold mb-3 pixel-text">
        ВЫБОР КОНТЕКСТА ДЛЯ АНАЛИЗА
      </div>
      
      <div className="flex flex-wrap gap-4">
        {/* Выбор датасета */}
        <div className="flex flex-col">
          <label className="text-green-300 text-xs font-bold mb-2 pixel-text">
            ДАТАСЕТ:
          </label>
          <select
            value={selectedDataset}
            onChange={(e) => handleDatasetChange(e.target.value)}
            className="bg-black border-2 border-green-500 rounded px-3 py-2 text-green-400 text-sm font-mono focus:outline-none focus:border-green-300 transition-all duration-300"
          >
            <option value="">Без контекста</option>
            {availableDatasets.map((dataset) => (
              <option key={dataset} value={dataset}>
                {dataset.toUpperCase()}
              </option>
            ))}
          </select>
        </div>

        {/* Выбор типа контекста */}
        {selectedDataset && (
          <div className="flex flex-col">
            <label className="text-green-300 text-xs font-bold mb-2 pixel-text">
              ТИП ДАННЫХ:
            </label>
            <select
              value={selectedContextType}
              onChange={(e) => handleContextTypeChange(e.target.value)}
              className="bg-black border-2 border-green-500 rounded px-3 py-2 text-green-400 text-sm font-mono focus:outline-none focus:border-green-300 transition-all duration-300"
            >
              <option value="report">Hierarchical Report</option>
              <option value="graph">Knowledge Graph</option>
            </select>
          </div>
        )}

        {/* Индикатор состояния */}
        <div className="flex items-end">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full border-2 border-green-400 ${
              selectedDataset ? 'bg-green-400 pulse-glow' : 'bg-transparent'
            }`}></div>
            <span className="text-green-300 text-xs font-mono">
              {selectedDataset 
                ? `${selectedDataset.toUpperCase()} / ${selectedContextType.toUpperCase()}`
                : 'КОНТЕКСТ НЕ ВЫБРАН'
              }
            </span>
          </div>
        </div>
      </div>
    </div>
  );
} 