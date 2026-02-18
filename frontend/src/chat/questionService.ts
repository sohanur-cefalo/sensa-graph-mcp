// Service to load and search evaluation questions from CSV

export interface Question {
  question: string;
  answer?: string;
  type?: string;
}

let questionsCache: Question[] | null = null;

/**
 * Load questions from the CSV file
 */
async function loadQuestions(): Promise<Question[]> {
  if (questionsCache) {
    return questionsCache;
  }

  try {
    // Try public folder first (for Vite dev server)
    let response = await fetch('/docs/evaluation_questions.csv');
    
    // If that fails, try the backend API
    if (!response.ok) {
      const apiBase = (import.meta as any).env?.VITE_API_URL || '';
      response = await fetch(`${apiBase}/docs/evaluation_questions.csv`);
    }
    
    if (!response.ok) {
      console.warn('Failed to load evaluation questions CSV');
      return [];
    }
    
    const csvText = await response.text();
    const lines = csvText.split('\n').filter(line => line.trim());
    
    // Skip header row if present
    const startIndex = lines[0]?.includes('Question') ? 1 : 0;
    
    const questions: Question[] = [];
    
    for (let i = startIndex; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;
      
      // Skip lines that are clearly headers or categories
      if (line.includes('Question,Probable Answer,Type') || 
          line.match(/^[A-Z][^,]*:$/) || // Category headers like "Totals & counts:"
          line.startsWith('Question') ||
          line.match(/^[A-Z][a-z\s&]+:$/)) { // Category headers without comma
        continue;
      }
      
      // Parse CSV line (simple CSV parsing - handles quoted fields)
      const parts: string[] = [];
      let current = '';
      let inQuotes = false;
      
      for (let j = 0; j < line.length; j++) {
        const char = line[j];
        
        if (char === '"') {
          inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
          parts.push(current.trim());
          current = '';
        } else {
          current += char;
        }
      }
      parts.push(current.trim()); // Add last part
      
      // Handle lines that might not have commas (just a question)
      let question = '';
      let answer: string | undefined = undefined;
      let type: string | undefined = undefined;
      
      if (parts.length === 1) {
        // Single column - might be just a question
        question = parts[0];
      } else if (parts.length >= 2) {
        question = parts[0];
        // Check if second part is a number (answer) or text (could be answer or type)
        const secondPart = parts[1];
        if (secondPart && !isNaN(Number(secondPart)) && secondPart.length < 5) {
          // It's a numeric answer
          answer = secondPart;
          type = parts[2] || undefined;
        } else {
          // It might be an answer or type
          answer = secondPart || undefined;
          type = parts[2] || undefined;
        }
      }
      
      // Clean up question - remove trailing period if it's followed by comma-separated values
      question = question.replace(/^["']|["']$/g, '').replace(/\.$/, '').trim();
      
      // Only add if question is valid (looks like a question)
      const isQuestion = question && 
          question.length > 3 &&
          (question.includes('?') || 
           question.match(/^(how|what|where|when|why|count|list|show|describe|are|do|is|total|give)/i));
      
      if (isQuestion && !question.match(/^[A-Z][^?]*:$/)) {
        questions.push({
          question,
          answer: answer && answer.length > 0 && answer !== 'undefined' ? answer : undefined,
          type: type && type.length > 0 && type !== 'undefined' ? type : undefined,
        });
      }
    }
    
    // Remove duplicates
    const uniqueQuestions = Array.from(
      new Map(questions.map(q => [q.question.toLowerCase(), q])).values()
    );
    
    questionsCache = uniqueQuestions;
    return uniqueQuestions;
  } catch (error) {
    console.error('Error loading questions:', error);
    return [];
  }
}

/**
 * Search questions based on query string
 */
export async function searchQuestions(
  query: string,
  limit: number = 10
): Promise<Question[]> {
  if (!query || query.trim().length === 0) {
    return [];
  }
  
  const questions = await loadQuestions();
  const queryLower = query.toLowerCase().trim();
  
  // Filter questions that contain the query
  const matches = questions
    .filter(q => q.question.toLowerCase().includes(queryLower))
    .slice(0, limit);
  
  return matches;
}

/**
 * Get all questions (for initial suggestions)
 */
export async function getAllQuestions(limit: number = 10): Promise<Question[]> {
  const questions = await loadQuestions();
  return questions.slice(0, limit);
}
