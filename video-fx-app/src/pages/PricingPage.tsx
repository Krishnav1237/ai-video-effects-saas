import { useState, useEffect } from 'react';
import { Check, Star, Zap, Crown, Loader2 } from 'lucide-react';
import { getPlans, createCheckout } from '../services/api';
import type { PricingPlan, PlanTier } from '../types';

export default function PricingPage() {
  const [plans, setPlans] = useState<PricingPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [checkingOut, setCheckingOut] = useState<PlanTier | null>(null);

  useEffect(() => {
    getPlans()
      .then((res) => setPlans(res.plans))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleCheckout = async (tier: PlanTier) => {
    if (tier === 'free') return;
    setCheckingOut(tier);
    try {
      const res = await createCheckout(
        tier,
        window.location.origin + '?payment=success',
        window.location.origin + '?payment=cancelled'
      );
      if (res.checkout_url) {
        window.open(res.checkout_url, '_blank');
      }
    } catch {
      // ignore
    } finally {
      setCheckingOut(null);
    }
  };

  const tierIcons: Record<string, React.ElementType> = {
    free: Star,
    pro: Zap,
    enterprise: Crown,
  };

  const tierColors: Record<string, string> = {
    free: 'zinc',
    pro: 'purple',
    enterprise: 'amber',
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 text-purple-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold gradient-text mb-2">Pricing for Indian Creators</h1>
        <p className="text-zinc-500">
          Affordable plans in INR. Start free, upgrade when you need more.
        </p>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {plans.map((plan) => {
          const Icon = tierIcons[plan.tier] || Star;
          const color = tierColors[plan.tier] || 'zinc';
          const isPopular = plan.tier === 'pro';
          const isCheckingOut = checkingOut === plan.tier;

          return (
            <div
              key={plan.tier}
              className={`glass-card rounded-2xl p-6 relative ${
                isPopular ? 'border-purple-500/40 ring-1 ring-purple-500/20' : ''
              }`}
            >
              {isPopular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="bg-gradient-to-r from-purple-600 to-blue-600 text-white text-xs font-medium px-3 py-1 rounded-full">
                    Most Popular
                  </span>
                </div>
              )}

              <div className="text-center mb-6">
                <div className={`w-12 h-12 mx-auto rounded-xl bg-${color}-500/10 flex items-center justify-center mb-3`}>
                  <Icon className={`w-6 h-6 text-${color}-400`} />
                </div>
                <h3 className="text-lg font-bold text-zinc-100">{plan.name}</h3>
                <div className="mt-2">
                  <span className="text-3xl font-bold text-zinc-100">
                    {plan.price_inr === 0 ? 'Free' : `Rs ${plan.price_inr}`}
                  </span>
                  {plan.price_inr > 0 && (
                    <span className="text-zinc-500 text-sm">/month</span>
                  )}
                </div>
              </div>

              <ul className="space-y-3 mb-6">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-sm text-zinc-300">
                    <Check className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                    {feature}
                  </li>
                ))}
              </ul>

              <button
                onClick={() => handleCheckout(plan.tier)}
                disabled={plan.tier === 'free' || isCheckingOut}
                className={`w-full py-2.5 rounded-lg text-sm font-medium transition-all ${
                  plan.tier === 'free'
                    ? 'bg-zinc-800 text-zinc-400 cursor-default'
                    : isPopular
                    ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:from-purple-500 hover:to-blue-500'
                    : 'border border-purple-500/30 text-purple-300 hover:bg-purple-500/10'
                } disabled:opacity-50`}
              >
                {isCheckingOut ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Processing...
                  </span>
                ) : plan.tier === 'free' ? (
                  'Current Plan'
                ) : (
                  `Upgrade to ${plan.name}`
                )}
              </button>
            </div>
          );
        })}
      </div>

      {/* Payment info */}
      <div className="text-center">
        <p className="text-xs text-zinc-600">
          Payments processed securely via Stripe. All prices in INR.
          Cancel anytime. No hidden charges.
        </p>
      </div>
    </div>
  );
}
