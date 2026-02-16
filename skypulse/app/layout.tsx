import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'SkyPulse Phase 2',
  description: 'Authenticated flight-deal dashboard with analytics and settings',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
