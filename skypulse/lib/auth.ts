import { cookies } from 'next/headers'
import { randomBytes, pbkdf2Sync, timingSafeEqual } from 'node:crypto'
import { prisma } from './prisma'

const SESSION_COOKIE = 'skypulse_session'

export function hashPassword(password: string): string {
  const salt = randomBytes(16).toString('hex')
  const hash = pbkdf2Sync(password, salt, 100000, 64, 'sha512').toString('hex')
  return `${salt}:${hash}`
}

export function verifyPassword(password: string, stored: string): boolean {
  const [salt, originalHash] = stored.split(':')
  if (!salt || !originalHash) return false

  const hashBuffer = Buffer.from(pbkdf2Sync(password, salt, 100000, 64, 'sha512').toString('hex'), 'hex')
  const originalBuffer = Buffer.from(originalHash, 'hex')
  if (hashBuffer.length !== originalBuffer.length) return false
  return timingSafeEqual(hashBuffer, originalBuffer)
}

export async function getCurrentUser() {
  const cookieStore = await cookies()
  const sessionUserId = cookieStore.get(SESSION_COOKIE)?.value
  if (!sessionUserId) return null

  return prisma.user.findUnique({ where: { id: sessionUserId } })
}

export async function setSession(userId: string) {
  const cookieStore = await cookies()
  cookieStore.set(SESSION_COOKIE, userId, {
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: 60 * 60 * 24 * 30,
  })
}

export async function clearSession() {
  const cookieStore = await cookies()
  cookieStore.delete(SESSION_COOKIE)
}

export function generateToken() {
  return randomBytes(24).toString('hex')
}
