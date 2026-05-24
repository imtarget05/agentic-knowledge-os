import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Agentic Knowledge OS | Multi-Agent RAG Platform',
  description: 'MCP-powered Multi-Agent RAG Knowledge Operating System for Engineering Teams',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  )
}
