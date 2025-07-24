import { NextRequest, NextResponse } from 'next/server';
import { GoogleGenAI } from '@google/genai';
import fs from 'fs';
import path from 'path';

const ai = new GoogleGenAI({
  apiKey: process.env.GEMINI_API_KEY || ''
});

interface ResearchData {
  timestamp: string;
  total_programs: number;
  programs: Array<{
    program_title: string;
    program_summary: string;
    subgroups: Array<{
      subgroup_type: string;
      subgroup_description: string;
      directions: Array<{
        rank: number;
        title: string;
        description: string;
        research_type: string;
        supporting_papers?: string[];
        critique: {
          is_interesting: boolean;
          novelty_score: number;
          impact_score: number;
          feasibility_score: number;
          final_score: number;
          recommendation: string;
          strengths?: string[];
          weaknesses?: string[];
        };
      }>;
    }>;
  }>;
}

function convertJsonToMarkdown(jsonData: ResearchData): string {
  const lines: string[] = [];
  
  lines.push("# Research Report");
  lines.push("");
  lines.push(`**Generated:** ${jsonData.timestamp}`);
  lines.push(`**Total Programs:** ${jsonData.total_programs}`);
  lines.push("");
  
  for (const program of jsonData.programs) {
    lines.push(`## ${program.program_title}`);
    lines.push("");
    lines.push(program.program_summary);
    lines.push("");
    
    for (const subgroup of program.subgroups) {
      lines.push(`### ${subgroup.subgroup_type}`);
      lines.push("");
      lines.push(subgroup.subgroup_description);
      lines.push("");
      
      for (const direction of subgroup.directions) {
        lines.push(`#### ${direction.rank}. ${direction.title}`);
        lines.push("");
        lines.push("**Description:**");
        lines.push(direction.description);
        lines.push("");
        
        const critique = direction.critique;
        lines.push("**Critique:**");
        lines.push("");
        lines.push(`- **Interesting:** ${critique.is_interesting}`);
        lines.push(`- **Novelty Score:** ${critique.novelty_score}`);
        lines.push(`- **Impact Score:** ${critique.impact_score}`);
        lines.push(`- **Feasibility Score:** ${critique.feasibility_score}`);
        lines.push(`- **Final Score:** ${critique.final_score}`);
        lines.push(`- **Recommendation:** ${critique.recommendation}`);
        lines.push("");
        
        if (critique.strengths) {
          lines.push("**Strengths:**");
          for (const strength of critique.strengths) {
            lines.push(`- ${strength}`);
          }
          lines.push("");
        }
        
        if (critique.weaknesses) {
          lines.push("**Weaknesses:**");
          for (const weakness of critique.weaknesses) {
            lines.push(`- ${weakness}`);
          }
          lines.push("");
        }
        
        if (direction.supporting_papers) {
          lines.push("**Supporting Papers:**");
          for (const paper of direction.supporting_papers) {
            lines.push(`- ${paper}`);
          }
          lines.push("");
        }
        
        lines.push(`**Research Type:** ${direction.research_type}`);
        lines.push("");
        lines.push("---");
        lines.push("");
      }
    }
  }
  
  return lines.join('\n');
}

export async function POST(request: NextRequest) {
  try {
    const { message, dataset, contextType } = await request.json();
    
    if (!message) {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 });
    }
    
    let contextData = '';
    
    if (dataset && contextType) {
      const dataPath = path.join(process.cwd(), 'public', 'data', dataset);
      
      if (contextType === 'report') {
        const reportPath = path.join(dataPath, 'hierarchical_research_report.json');
        if (fs.existsSync(reportPath)) {
          const jsonData = JSON.parse(fs.readFileSync(reportPath, 'utf-8'));
          contextData = convertJsonToMarkdown(jsonData);
        }
      } else if (contextType === 'graph') {
        const graphPath = path.join(dataPath, 'longevity_knowledge_graph.graphml');
        if (fs.existsSync(graphPath)) {
          contextData = fs.readFileSync(graphPath, 'utf-8');
        }
      }
    }
    
    const model = ai.models.generateContent;
    const prompt = contextData 
      ? `Контекст данных:\n\n${contextData}\n\nВопрос пользователя: ${message}`
      : message;
    
    const response = await model({
      model: "gemini-2.5-flash",
      contents: prompt,
    });
    
    return NextResponse.json({ 
      response: response.text || 'Извините, не удалось получить ответ'
    });
    
  } catch (error) {
    console.error('Error in chat API:', error);
    return NextResponse.json(
      { error: 'Internal server error' }, 
      { status: 500 }
    );
  }
} 