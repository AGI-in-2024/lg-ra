'use client';

import { useState, useEffect } from 'react';

interface DatasetSelectorProps {
  onDatasetChange: (dataset: string) => void;
  selectedDataset: string;
}

export default function DatasetSelector({ 
  onDatasetChange, 
  selectedDataset
}: DatasetSelectorProps) {
  const [availableDatasets, setAvailableDatasets] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchDatasets() {
      try {
        const response = await fetch('/api/datasets');
        if (response.ok) {
          const datasets = await response.json();
          setAvailableDatasets(datasets);
          
          // Если нет выбранного датасета и есть доступные датасеты, выбираем первый
          if (!selectedDataset && datasets.length > 0) {
            onDatasetChange(datasets[0]);
          }
        }
      } catch (error) {
        console.error('Error fetching datasets:', error);
        setAvailableDatasets(['dataset1']);
        if (!selectedDataset) {
          onDatasetChange('dataset1');
        }
      } finally {
        setLoading(false);
      }
    }
    
    fetchDatasets();
  }, [selectedDataset, onDatasetChange]);

  const handleDatasetChange = (dataset: string) => {
    onDatasetChange(dataset);
  };

  if (loading) {
    return <span className="text-green-400">загрузка...</span>;
  }

  return (
    <span className="inline-flex items-center gap-1">
      <select
        value={selectedDataset}
        onChange={(e) => handleDatasetChange(e.target.value)}
        className="bg-transparent border border-green-500 rounded px-1 py-0.5 text-green-400 font-mono focus:outline-none focus:border-green-300 transition-all duration-300 text-sm"
      >
        {availableDatasets.map((dataset) => (
          <option key={dataset} value={dataset} className="bg-black">
            {dataset.toUpperCase()}
          </option>
        ))}
      </select>
    </span>
  );
} 