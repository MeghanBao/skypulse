import OpenAI from 'openai';

export const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY || 'mock-key', // Fallback for dev if key missing
    dangerouslyAllowBrowser: true // Only if used in client components (not recommended), but we use it in server actions
});
