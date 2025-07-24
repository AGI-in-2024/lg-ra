'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface Critique {
  is_interesting: boolean;
  novelty_score: number;
  impact_score: number;
  feasibility_score: number;
  final_score: number;
  strengths: string[];
  weaknesses: string[];
  recommendation: string;
}

interface Direction {
  rank: number;
  title: string;
  description: string;
  critique: Critique;
  supporting_papers: string[];
  research_type: string;
}

interface Subgroup {
  subgroup_type: string;
  subgroup_description: string;
  directions: Direction[];
}

interface Program {
  program_title: string;
  program_summary: string;
  subgroups: Subgroup[];
}

interface ReportData {
  timestamp: string;
  total_programs: number;
  programs: Program[];
}

export default function ReportPage() {
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadReportData();
  }, []);

  const loadReportData = async () => {
    try {
      const response = await fetch('/data/dataset1/hierarchical_research_report.json');
      if (!response.ok) {
        throw new Error('Ошибка загрузки отчета');
      }
      const data = await response.json();
      setReportData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Неизвестная ошибка');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 8) return 'text-green-400';
    if (score >= 6) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getTypeColor = (type: string) => {
    if (type === 'White Spot') return 'bg-blue-600';
    if (type === 'Bridge') return 'bg-purple-600';
    return 'bg-gray-600';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-green-400 font-mono flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl mb-4">Загрузка отчета...</div>
          <div className="flex justify-center space-x-1">
            <div className="w-3 h-3 bg-green-400 rounded-full animate-bounce"></div>
            <div className="w-3 h-3 bg-green-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
            <div className="w-3 h-3 bg-green-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-black text-green-400 font-mono flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-400 text-xl mb-4">Ошибка: {error}</div>
          <button 
            onClick={loadReportData}
            className="px-6 py-3 bg-green-600 hover:bg-green-500 text-black font-bold rounded border-2 border-green-400"
          >
            Повторить
          </button>
        </div>
      </div>
    );
  }

  if (!reportData) {
    return null;
  }

  // Собираем все статьи из отчета
  const allPapers = reportData.programs.flatMap(program => 
    program.subgroups.flatMap(subgroup => 
      subgroup.directions.flatMap(direction => direction.supporting_papers)
    )
  );

  const uniquePapers = [...new Set(allPapers)];

  return (
    <div className="min-h-screen bg-black text-green-400 font-mono">
      {/* Header */}
      <div className="border-b border-green-500 p-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold mb-2">ИССЛЕДОВАТЕЛЬСКИЙ ОТЧЕТ</h1>
            <div className="text-green-300 text-sm">
              Создан: {new Date(reportData.timestamp).toLocaleString('ru-RU')}
            </div>
            <div className="text-green-300 text-sm">
              Программ: {reportData.total_programs}
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <a 
              href="/graph"
              className="px-4 py-2 bg-green-600 hover:bg-green-500 text-black font-bold rounded border-2 border-green-400 transition-all duration-200"
            >
              ГРАФ ЗНАНИЙ
            </a>
            {uniquePapers.length > 0 && (
              <Link 
                href={`/graph?highlight=${uniquePapers.join(',')}&search=open`}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-black font-bold rounded border-2 border-purple-400 transition-all duration-200"
              >
                📊 ВСЕ СТАТЬИ В ГРАФЕ
              </Link>
            )}
            <Link 
              href="/"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-black font-bold rounded border-2 border-blue-400 transition-all duration-200"
            >
              ГЛАВНАЯ
            </Link>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-8">
        {reportData.programs.map((program, programIndex) => (
          <div key={programIndex} className="border border-green-500 rounded-lg p-6">
            {/* Program Title */}
            <h2 className="text-2xl font-bold text-green-400 mb-4">
              {program.program_title}
            </h2>
            
            {/* Program Summary */}
            <div className="mb-6 p-4 bg-gray-900 rounded border border-green-600">
              <h3 className="text-lg font-bold mb-2 text-green-300">Описание программы:</h3>
              <p className="text-green-200 leading-relaxed">{program.program_summary}</p>
            </div>

            {/* Subgroups */}
            <div className="space-y-6">
              {program.subgroups.map((subgroup, subgroupIndex) => (
                <div key={subgroupIndex} className="border border-green-600 rounded p-4">
                  <h3 className="text-xl font-bold text-green-300 mb-3">
                    {subgroup.subgroup_type}
                  </h3>
                  <p className="text-green-200 mb-4">{subgroup.subgroup_description}</p>

                  {/* Directions */}
                  <div className="space-y-4">
                    {subgroup.directions.map((direction, directionIndex) => (
                      <div key={directionIndex} className="border border-green-700 rounded p-4 bg-gray-900">
                        {/* Direction Header */}
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <span className="text-2xl font-bold text-green-400">#{direction.rank}</span>
                              <span className={`px-3 py-1 rounded text-xs font-bold text-white ${getTypeColor(direction.research_type)}`}>
                                {direction.research_type}
                              </span>
                            </div>
                            <h4 className="text-lg font-bold text-green-300">{direction.title}</h4>
                          </div>
                          <div className="text-right">
                            <div className={`text-2xl font-bold ${getScoreColor(direction.critique.final_score)}`}>
                              {direction.critique.final_score.toFixed(1)}
                            </div>
                            <div className="text-sm text-green-400">Итого</div>
                          </div>
                        </div>

                        {/* Description */}
                        <div className="mb-4">
                          <p className="text-green-200 leading-relaxed">{direction.description}</p>
                        </div>

                        {/* Scores */}
                        <div className="grid grid-cols-3 gap-4 mb-4 p-3 bg-black rounded border border-green-800">
                          <div className="text-center">
                            <div className={`text-lg font-bold ${getScoreColor(direction.critique.novelty_score)}`}>
                              {direction.critique.novelty_score.toFixed(1)}
                            </div>
                            <div className="text-xs text-green-400">Новизна</div>
                          </div>
                          <div className="text-center">
                            <div className={`text-lg font-bold ${getScoreColor(direction.critique.impact_score)}`}>
                              {direction.critique.impact_score.toFixed(1)}
                            </div>
                            <div className="text-xs text-green-400">Влияние</div>
                          </div>
                          <div className="text-center">
                            <div className={`text-lg font-bold ${getScoreColor(direction.critique.feasibility_score)}`}>
                              {direction.critique.feasibility_score.toFixed(1)}
                            </div>
                            <div className="text-xs text-green-400">Выполнимость</div>
                          </div>
                        </div>

                        {/* Strengths and Weaknesses */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                          <div>
                            <h5 className="font-bold text-green-300 mb-2">Сильные стороны:</h5>
                            <ul className="space-y-1">
                              {direction.critique.strengths.map((strength, idx) => (
                                <li key={idx} className="text-green-200 text-sm">• {strength}</li>
                              ))}
                            </ul>
                          </div>
                          <div>
                            <h5 className="font-bold text-red-300 mb-2">Слабые стороны:</h5>
                            <ul className="space-y-1">
                              {direction.critique.weaknesses.map((weakness, idx) => (
                                <li key={idx} className="text-red-200 text-sm">• {weakness}</li>
                              ))}
                            </ul>
                          </div>
                        </div>

                        {/* Recommendation and Papers */}
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-4">
                            <span className="font-bold text-green-300">Рекомендация:</span>
                            <span className={`px-3 py-1 rounded text-sm font-bold ${
                              direction.critique.recommendation === 'Strongly Recommend' 
                                ? 'bg-green-600 text-white' 
                                : 'bg-yellow-600 text-white'
                            }`}>
                              {direction.critique.recommendation}
                            </span>
                          </div>
                          <div className="text-sm text-green-400">
                            Статей: {direction.supporting_papers.length}
                          </div>
                        </div>

                        {/* Links to Graph */}
                        {direction.supporting_papers.length > 0 && (
                          <div className="flex flex-wrap gap-2">
                            <a 
                              href={`/graph?highlight=${direction.supporting_papers.join(',')}&search=open`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="px-3 py-1 bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold rounded border border-purple-400 transition-all duration-200"
                            >
                              📊 Показать статьи в графе
                            </a>
                            {direction.supporting_papers.map((paperId, idx) => (
                              <a 
                                key={idx}
                                href={`/graph?focus=${paperId}&highlight=${direction.supporting_papers.join(',')}&search=open`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="px-2 py-1 bg-blue-600 hover:bg-blue-500 text-white text-xs rounded border border-blue-400 transition-all duration-200"
                                title={`Фокус на статье ${paperId}`}
                              >
                                🔍 {paperId}
                              </a>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
} 