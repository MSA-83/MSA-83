import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

interface PricingTier {
  id: string
  name: string
  price_monthly: number
  price_yearly: number
  description: string
  features: string[]
  limits: Record<string, number>
}

export default function BillingPage() {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly')

  const { data: tiers, isLoading } = useQuery({
    queryKey: ['pricing'],
    queryFn: () => fetch('/api/billing/pricing').then(r => r.json()),
  })

  const handleSubscribe = async (tierId: string) => {
    const response = await fetch('/api/billing/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tier_id: tierId,
        billing_cycle: billingCycle,
      }),
    })

    const data = await response.json()

    if (data.checkout_url) {
      window.location.href = data.checkout_url
    } else {
      alert(data.message || 'Tier activated!')
    }
  }

  if (isLoading) {
    return <div className="flex items-center justify-center h-64">Loading pricing...</div>
  }

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-titanium-100">Pricing</h2>
        <p className="text-titanium-400 mt-1">Choose the plan that fits your needs</p>
      </div>

      <div className="flex items-center justify-center gap-4 mb-8">
        <span className={`text-sm ${billingCycle === 'monthly' ? 'text-titanium-100' : 'text-titanium-500'}`}>Monthly</span>
        <button
          onClick={() => setBillingCycle(prev => prev === 'monthly' ? 'yearly' : 'monthly')}
          className={`relative w-14 h-7 rounded-full transition-colors ${
            billingCycle === 'yearly' ? 'bg-accent-500' : 'bg-titanium-700'
          }`}
        >
          <span
            className={`absolute top-0.5 left-0.5 w-6 h-6 bg-white rounded-full transition-transform ${
              billingCycle === 'yearly' ? 'translate-x-7' : ''
            }`}
          />
        </button>
        <span className={`text-sm ${billingCycle === 'yearly' ? 'text-titanium-100' : 'text-titanium-500'}`}>
          Yearly <span className="text-green-400 text-xs">(save 17%)</span>
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {tiers?.map((tier: PricingTier) => {
          const price = billingCycle === 'yearly' ? tier.price_yearly : tier.price_monthly
          const isPopular = tier.id === 'pro'

          return (
            <div
              key={tier.id}
              className={`card relative ${
                isPopular ? 'border-accent-500/50 ring-2 ring-accent-500/20' : ''
              }`}
            >
              {isPopular && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-accent-500 text-white text-xs font-medium px-3 py-1 rounded-full">
                  Most Popular
                </span>
              )}

              <h3 className="text-xl font-bold text-titanium-100">{tier.name}</h3>
              <p className="text-sm text-titanium-400 mt-2">{tier.description}</p>

              <div className="mt-4 mb-6">
                {price === 0 ? (
                  <span className="text-4xl font-bold text-titanium-100">Free</span>
                ) : (
                  <div>
                    <span className="text-4xl font-bold text-titanium-100">${price}</span>
                    <span className="text-titanium-400">/{billingCycle === 'yearly' ? 'mo (billed yearly)' : 'month'}</span>
                  </div>
                )}
              </div>

              <button
                onClick={() => handleSubscribe(tier.id)}
                className={`w-full py-3 rounded-lg font-medium transition-colors ${
                  tier.id === 'defense'
                    ? 'btn-secondary'
                    : isPopular
                    ? 'btn-primary'
                    : 'bg-titanium-700 hover:bg-titanium-600 text-titanium-100'
                }`}
              >
                {tier.id === 'defense' ? 'Contact Sales' : price === 0 ? 'Get Started' : 'Subscribe'}
              </button>

              <ul className="mt-6 space-y-3">
                {tier.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-sm text-titanium-300">
                    <span className="text-green-400 mt-0.5">✓</span>
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </div>
          )
        })}
      </div>
    </div>
  )
}
