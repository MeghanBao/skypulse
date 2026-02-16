'use server'

import { prisma } from '@/lib/prisma'
import { parseSubscription, generateDealSummary } from '@/lib/llm-service'
import { findDeals } from '@/lib/flight-service'
import { revalidatePath } from 'next/cache'
import { clearSession, generateToken, getCurrentUser, hashPassword, setSession, verifyPassword } from '@/lib/auth'

export async function registerUser(formData: FormData): Promise<void> {
  const email = (formData.get('email') as string)?.trim().toLowerCase()
  const password = formData.get('password') as string
  if (!email || !password || password.length < 8) return

  const existing = await prisma.user.findUnique({ where: { email } })
  if (existing) return

  const user = await prisma.user.create({
    data: {
      email,
      passwordHash: hashPassword(password),
      notificationEmail: email,
      verificationTokens: {
        create: {
          token: generateToken(),
          expiresAt: new Date(Date.now() + 1000 * 60 * 60 * 24),
        },
      },
    },
  })

  await setSession(user.id)
  revalidatePath('/')
}

export async function loginUser(formData: FormData): Promise<void> {
  const email = (formData.get('email') as string)?.trim().toLowerCase()
  const password = formData.get('password') as string
  if (!email || !password) return

  const user = await prisma.user.findUnique({ where: { email } })
  if (!user || !verifyPassword(password, user.passwordHash)) return

  await setSession(user.id)
  revalidatePath('/')
}

export async function logoutUser(): Promise<void> {
  await clearSession()
  revalidatePath('/')
}

export async function verifyEmail(formData: FormData): Promise<void> {
  const token = formData.get('token') as string
  if (!token) return

  const record = await prisma.verificationToken.findUnique({ where: { token } })
  if (!record || record.expiresAt < new Date()) return

  await prisma.user.update({ where: { id: record.userId }, data: { isVerified: true } })
  await prisma.verificationToken.delete({ where: { token } })
  revalidatePath('/')
}

export async function createSubscription(formData: FormData): Promise<void> {
  const user = await getCurrentUser()
  if (!user) return

  const prompt = formData.get('prompt') as string
  if (!prompt) return

  try {
    const parsed = await parseSubscription(prompt)
    const sub = await prisma.subscription.create({
      data: {
        userId: user.id,
        prompt,
        origin: parsed.origin ?? user.preferredOrigin,
        destination: parsed.destination,
        maxPrice: parsed.maxPrice ?? user.preferredMaxPrice ?? undefined,
        startDate: parsed.startDate,
        endDate: parsed.endDate,
      },
    })

    const deals = await findDeals(
      parsed.origin || user.preferredOrigin || null,
      parsed.destination || null,
      parsed.maxPrice ?? user.preferredMaxPrice ?? undefined,
    )

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
          reasonToBuy: summary,
        },
      })
    }

    revalidatePath('/')
  } catch (error) {
    console.error('Action Error:', error)
  }
}

export async function updateSubscriptionStatus(formData: FormData): Promise<void> {
  const user = await getCurrentUser()
  if (!user) return

  const id = formData.get('id') as string
  const isActive = formData.get('isActive') === 'true'
  await prisma.subscription.updateMany({ where: { id, userId: user.id }, data: { isActive } })
  revalidatePath('/')
}

export async function deleteSubscription(formData: FormData): Promise<void> {
  const user = await getCurrentUser()
  if (!user) return

  const id = formData.get('id') as string
  await prisma.subscription.deleteMany({ where: { id, userId: user.id } })
  revalidatePath('/')
}

export async function updatePreferences(formData: FormData): Promise<void> {
  const user = await getCurrentUser()
  if (!user) return

  const preferredOrigin = (formData.get('preferredOrigin') as string)?.trim() || null
  const preferredMaxPriceRaw = formData.get('preferredMaxPrice') as string
  const preferredMaxPrice = preferredMaxPriceRaw ? Number(preferredMaxPriceRaw) : null
  const notificationEmail = (formData.get('notificationEmail') as string)?.trim() || user.email

  await prisma.user.update({
    where: { id: user.id },
    data: {
      preferredOrigin,
      preferredMaxPrice: Number.isNaN(preferredMaxPrice) ? null : preferredMaxPrice,
      notificationEmail,
    },
  })

  revalidatePath('/')
}

export async function getDashboardData() {
  const user = await getCurrentUser()
  if (!user) return { user: null, subscriptions: [], deals: [], analytics: null }

  const subscriptions = await prisma.subscription.findMany({
    where: { userId: user.id },
    include: { matchedDeals: true },
    orderBy: { createdAt: 'desc' },
  })

  const deals = subscriptions.flatMap((sub) => sub.matchedDeals)
  const destinationStats = deals.reduce<Record<string, number>>((acc, deal) => {
    acc[deal.arrivalCity] = (acc[deal.arrivalCity] ?? 0) + 1
    return acc
  }, {})

  const avgPrice = deals.length ? Math.round(deals.reduce((sum, deal) => sum + deal.price, 0) / deals.length) : 0

  return {
    user,
    subscriptions,
    deals,
    analytics: {
      avgPrice,
      destinationStats,
      dealFrequency: deals.length,
      activeSubscriptions: subscriptions.filter((sub) => sub.isActive).length,
    },
  }
}
