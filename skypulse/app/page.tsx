import {
  deleteSubscription,
  getDashboardData,
  loginUser,
  logoutUser,
  registerUser,
  updatePreferences,
  updateSubscriptionStatus,
  verifyEmail,
} from './actions'
import SubscriptionForm from '@/components/SubscriptionForm'
import DealCard from '@/components/DealCard'

export const dynamic = 'force-dynamic'

export default async function Home() {
  const { user, subscriptions, deals, analytics } = await getDashboardData()

  return (
    <main className="min-h-screen pb-20">
      <div className="relative overflow-hidden bg-gradient-premium pt-20 pb-20">
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10"></div>
        <div className="container mx-auto px-4 relative z-10 text-center space-y-6">
          <div className="inline-block px-4 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-300 text-sm font-medium mb-4 animate-float">
            ✨ SkyPulse Phase 2 Dashboard
          </div>
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight">SkyPulse</h1>
          <p className="text-lg text-gray-300 max-w-2xl mx-auto">Authentication, subscription management, analytics, price trends, and settings are now integrated.</p>

          {!user ? (
            <div className="grid md:grid-cols-3 gap-4 max-w-5xl mx-auto text-left">
              <form action={registerUser} className="glass-panel p-5 rounded-xl space-y-3">
                <h3 className="font-semibold">Register</h3>
                <input name="email" placeholder="Email" className="glass-input w-full p-2 rounded-lg" required />
                <input name="password" type="password" placeholder="Password (8+)" className="glass-input w-full p-2 rounded-lg" required />
                <button className="btn-primary w-full">Create Account</button>
              </form>

              <form action={loginUser} className="glass-panel p-5 rounded-xl space-y-3">
                <h3 className="font-semibold">Sign In</h3>
                <input name="email" placeholder="Email" className="glass-input w-full p-2 rounded-lg" required />
                <input name="password" type="password" placeholder="Password" className="glass-input w-full p-2 rounded-lg" required />
                <button className="btn-primary w-full">Sign In</button>
              </form>

              <form action={verifyEmail} className="glass-panel p-5 rounded-xl space-y-3">
                <h3 className="font-semibold">Email Verification</h3>
                <input name="token" placeholder="Verification token" className="glass-input w-full p-2 rounded-lg" required />
                <button className="btn-primary w-full">Verify Email</button>
              </form>
            </div>
          ) : (
            <div className="flex justify-center gap-4 items-center">
              <span className="text-sm text-gray-300">{user.email} · {user.isVerified ? 'Verified' : 'Unverified'}</span>
              <form action={logoutUser}>
                <button className="btn-primary">Sign Out</button>
              </form>
            </div>
          )}
        </div>
      </div>

      {user && (
        <div className="container mx-auto px-4 -mt-8 relative z-20 space-y-8">
          <section className="glass-panel p-6 rounded-2xl">
            <h2 className="text-2xl font-bold mb-4">Create Subscription</h2>
            <SubscriptionForm />
          </section>

          <section className="grid lg:grid-cols-4 gap-4">
            <div className="glass-panel p-4 rounded-xl">
              <div className="text-gray-400 text-sm">Deals</div>
              <div className="text-3xl font-bold">{analytics?.dealFrequency ?? 0}</div>
            </div>
            <div className="glass-panel p-4 rounded-xl">
              <div className="text-gray-400 text-sm">Average Price</div>
              <div className="text-3xl font-bold">${analytics?.avgPrice ?? 0}</div>
            </div>
            <div className="glass-panel p-4 rounded-xl">
              <div className="text-gray-400 text-sm">Active Subscriptions</div>
              <div className="text-3xl font-bold">{analytics?.activeSubscriptions ?? 0}</div>
            </div>
            <div className="glass-panel p-4 rounded-xl">
              <div className="text-gray-400 text-sm">History</div>
              <div className="text-3xl font-bold">{subscriptions.length}</div>
            </div>
          </section>

          <section className="grid lg:grid-cols-2 gap-6">
            <div className="glass-panel p-6 rounded-2xl space-y-4">
              <h3 className="text-xl font-semibold">Subscription Management</h3>
              {subscriptions.length === 0 ? (
                <p className="text-gray-400">No subscriptions yet.</p>
              ) : (
                subscriptions.map((sub) => (
                  <div key={sub.id} className="border border-slate-700 rounded-xl p-4 space-y-2">
                    <p className="font-medium">{sub.prompt}</p>
                    <p className="text-sm text-gray-400">{sub.origin ?? 'Any'} → {sub.destination ?? 'Any'} · Budget {sub.maxPrice ? `$${sub.maxPrice}` : 'No limit'}</p>
                    <div className="flex gap-2">
                      <form action={updateSubscriptionStatus}>
                        <input type="hidden" name="id" value={sub.id} />
                        <input type="hidden" name="isActive" value={String(!sub.isActive)} />
                        <button className="btn-primary">{sub.isActive ? 'Pause' : 'Activate'}</button>
                      </form>
                      <form action={deleteSubscription}>
                        <input type="hidden" name="id" value={sub.id} />
                        <button className="px-4 py-2 rounded-full bg-red-600 text-white">Delete</button>
                      </form>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="glass-panel p-6 rounded-2xl space-y-4">
              <h3 className="text-xl font-semibold">Settings</h3>
              <form action={updatePreferences} className="space-y-3">
                <input name="preferredOrigin" defaultValue={user.preferredOrigin ?? ''} placeholder="Default origin city (e.g. NYC)" className="glass-input w-full p-2 rounded-lg" />
                <input name="preferredMaxPrice" defaultValue={user.preferredMaxPrice ?? ''} placeholder="Default max budget" className="glass-input w-full p-2 rounded-lg" />
                <input name="notificationEmail" defaultValue={user.notificationEmail ?? user.email} placeholder="Notification email" className="glass-input w-full p-2 rounded-lg" />
                <button className="btn-primary">Save Settings</button>
              </form>

              <div>
                <h4 className="font-medium mb-2">Top Destinations</h4>
                <div className="space-y-2">
                  {Object.entries(analytics?.destinationStats ?? {}).map(([city, count]) => (
                    <div key={city} className="flex items-center gap-2">
                      <div className="w-24 text-sm text-gray-300">{city}</div>
                      <div className="h-2 bg-blue-500 rounded" style={{ width: `${count * 20}px` }}></div>
                      <span className="text-xs text-gray-400">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-bold">Deals + Email Preview</h2>
            {deals.length === 0 ? (
              <div className="glass-panel p-8 rounded-xl text-gray-400">No matching flights yet.</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {deals.map((deal) => (
                  <div key={deal.id} className="space-y-3">
                    <DealCard deal={deal} />
                    <div className="glass-panel p-3 rounded-lg text-xs text-gray-300">
                      <div className="font-semibold mb-1">Email Preview</div>
                      Subject: ✈️ {deal.departureCity} → {deal.arrivalCity} ${deal.price}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      )}
    </main>
  )
}
