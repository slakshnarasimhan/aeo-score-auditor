import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AEO/GEO Score Auditor',
  description: 'Analyze and optimize content for AI-powered search engines',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

