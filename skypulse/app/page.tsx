import { getSubscriptions } from './actions'
import SubscriptionForm from '@/components/SubscriptionForm'
import DealCard from '@/components/DealCard'

export const dynamic = 'force-dynamic'

export default async function Home() {
  const subscriptions = await getSubscriptions()

  // Flatten deals from all subscriptions for a "feed" view
  // In a real app, strict typing would be handled by Prisma generated types
  const allDeals = subscriptions.flatMap((sub: any) => sub.matchedDeals)

  return (
    <main className="min-h-screen pb-20">
      {/* Hero Section */}
      <div className="relative overflow-hidden bg-gradient-premium pt-20 pb-32">
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10"></div>
        <div className="container mx-auto px-4 relative z-10 text-center space-y-6">
          <div className="inline-block px-4 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-300 text-sm font-medium mb-4 animate-float">
            ✨ AI-Powered Flight Assistant
          </div>
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight">
            Sky<span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">Pulse</span>
          </h1>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed">
            Stop searching. Start flying. <br />
            Tell us where you want to go in plain English, and we'll watch the prices for you.
          </p>

          <div className="mt-12">
            <SubscriptionForm />
          </div>
        </div>
      </div>

      {/* Dashboard Section */}
      <div className="container mx-auto px-4 -mt-20 relative z-20">

        {/* Active Subscriptions (Debug view or List) */}
        {/* For this MVP, we focus on the Deal Feed */}

        <div className="space-y-8">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-white">Recommended Deals</h2>
            <span className="text-sm text-gray-500">{allDeals.length} deals found</span>
          </div>

          {allDeals.length === 0 ? (
            <div className="glass-panel p-12 rounded-2xl text-center space-y-4">
              <div className="text-4xl">✈️</div>
              <h3 className="text-xl font-semibold text-white">No deals found yet</h3>
              <p className="text-gray-400">
                Try creating a subscription above (e.g., "Flights to Paris under $500")
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {allDeals.map((deal: any) => (
                <DealCard key={deal.id} deal={deal} />
              ))}
            </div>
          )}
        </div>
      </div>
    </main>
  )
}
