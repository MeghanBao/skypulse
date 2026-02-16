import { openai } from './openai';

export interface ParsedSubscription {
    origin: string;
    destination: string;
    maxPrice?: number;
    startDate?: string;
    endDate?: string;
}

export async function parseSubscription(prompt: string): Promise<ParsedSubscription> {
    // If no API key, return mock data for testing
    if (!process.env.OPENAI_API_KEY) {
        console.warn("No OpenAI API Key found. Returning mock parsing.");
        return {
            origin: "NYC",
            destination: "London",
            maxPrice: 800,
            startDate: "2024-05-01",
            endDate: "2024-05-10"
        };
    }

    try {
        const completion = await openai.chat.completions.create({
            model: "gpt-3.5-turbo", // Cost-effective for simple parsing
            messages: [
                {
                    role: "system",
                    content: `You are a flight subscription parser. Extract the following fields from the user's natural language request: origin, destination, maxPrice (number), startDate, endDate. Return JSON only.`
                },
                { role: "user", content: prompt }
            ],
            response_format: { type: "json_object" }
        });

        const content = completion.choices[0].message.content;
        if (!content) throw new Error("No content from LLM");

        return JSON.parse(content) as ParsedSubscription;
    } catch (error) {
        console.error("LLM Parsing Error:", error);
        // Fallback or re-throw
        throw error;
    }
}

export interface FlightDealInput {
    airline: string
    flightNumber?: string | null
    departureCity: string
    arrivalCity: string
    departureDate: string
    returnDate: string
    price: number
    bookingLink: string
}

export async function generateDealSummary(flight: FlightDealInput, userPrompt: string): Promise<string> {
    if (!process.env.OPENAI_API_KEY) {
        return "🔥 Excellent deal found based on your preferences! (Mock AI Summary)";
    }

    try {
        const completion = await openai.chat.completions.create({
            model: "gpt-3.5-turbo",
            messages: [
                {
                    role: "system",
                    content: "You are a helpful travel assistant. Explain why this flight deal is good based on the user's original request. Keep it short and exciting (max 2 sentences)."
                },
                {
                    role: "user",
                    content: `User Request: "${userPrompt}"\nFlight: ${JSON.stringify(flight)}`
                }
            ]
        });
        return completion.choices[0].message.content || "Great deal found!";
    } catch {
        return "Great deal found!";
    }
}
