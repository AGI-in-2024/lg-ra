import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  try {
    const dataPath = path.join(process.cwd(), 'public', 'data');
    
    if (!fs.existsSync(dataPath)) {
      return NextResponse.json([]);
    }
    
    const datasets = fs.readdirSync(dataPath, { withFileTypes: true })
      .filter(dirent => dirent.isDirectory())
      .map(dirent => dirent.name);
    
    return NextResponse.json(datasets);
  } catch (error) {
    console.error('Error reading datasets:', error);
    return NextResponse.json(['dataset1']); // fallback
  }
} 