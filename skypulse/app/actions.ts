'use server'

import { prisma } from '@/lib/prisma'
import { parseSubscription, generateDealSummary } from '@/lib/llm-service'
import { findDeals } from '@/lib/flight-service'
import { revalidatePath } from 'next/cache'

export async function createSubscription(formData: FormData) {
    const prompt = formData.get('prompt') as string
    if (!prompt) return { error: "Prompt is required" }

    try {
        // 1. Parse the natural language prompt using LLM
        const parsed = await parseSubscription(prompt)

        // 2. Save subscription to DB
        const sub = await prisma.subscription.create({
            data: {
                prompt,
                origin: parsed.origin,
                destination: parsed.destination,
                maxPrice: parsed.maxPrice,
                startDate: parsed.startDate,
                endDate: parsed.endDate,
            }
        })

        // 3. Immediately search for deals (Mock)
        const deals = await findDeals(parsed.origin || null, parsed.destination || null, parsed.maxPrice)

        // 4. If deals found, generate AI summaries and save
        for (const deal of deals) {
            const summary = await generateDealSummary(deal, prompt)
            await prisma.deal.create({
                data: {
                    subscriptionId: sub.id,
                    airline: deal.airline,
                    flightNumber: deal.flightNumber,
                    departureCity: deal.departureCity,
                    arrivalCity: deal.arrivalCity,
                    departureDate: new Date(deal.departureDate),
                    returnDate: new Date(deal.returnDate),
                    price: deal.price,
                    bookingLink: deal.bookingLink,
                    reasonToBuy: summary
                }
            })
        }

        revalidatePath('/')
        return { success: true, subscriptionId: sub.id, dealsFound: deals.length }
    } catch (error) {
        console.error("Action Error:", error)
        return { error: "Failed to create subscription" }
    }
}

export async function getSubscriptions() {
    return await prisma.subscription.findMany({
        include: { matchedDeals: true },
        orderBy: { createdAt: 'desc' }
    })
}
