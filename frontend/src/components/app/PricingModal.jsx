import { useEffect, useState } from "react";
import { useApp } from "@/contexts/AppContext";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Check, Loader2, Sparkles, Crown, Zap, X } from "lucide-react";

const PLANS = [
  {
    id: "free",
    name: "Explorer",
    price: 0,
    description: "Get started building worlds",
    features: [
      "Up to 5 worlds",
      "128x128 max map size",
      "JSON & Prefab exports",
      "Community gallery access",
    ],
    excluded: [
      "AI World Generation",
      "Real-time collaboration",
      "Version history",
      "Analytics dashboard",
    ],
    icon: Zap,
    color: "var(--text-secondary)",
  },
  {
    id: "creator",
    name: "Creator",
    price: 9,
    description: "Unlock AI and collaboration",
    features: [
      "Unlimited worlds",
      "512x512 max map size",
      "All export formats",
      "AI World Generation",
      "Real-time collaboration",
      "Version history",
      "Community gallery access",
    ],
    excluded: [
      "Analytics dashboard",
    ],
    icon: Sparkles,
    color: "var(--brand-primary)",
    popular: true,
  },
  {
    id: "developer",
    name: "Developer",
    price: 29,
    description: "Everything, plus analytics",
    features: [
      "Everything in Creator",
      "Analytics dashboard",
      "Priority support",
      "Early access to features",
    ],
    excluded: [],
    icon: Crown,
    color: "var(--brand-warning)",
  },
];

export function PricingModal() {
  const ctx = useApp();
  const [checkoutResult, setCheckoutResult] = useState(null);

  // Handle checkout return from Stripe
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sessionId = params.get("session_id");
    const cancelled = params.get("cancelled");

    if (sessionId) {
      ctx.setShowPricingDialog(true);
      setCheckoutResult("verifying");
      ctx.verifyCheckout(sessionId).then((status) => {
        setCheckoutResult(status);
        // Clean URL
        window.history.replaceState({}, document.title, window.location.pathname);
      });
    } else if (cancelled) {
      ctx.setShowPricingDialog(true);
      setCheckoutResult("cancelled");
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  const currentPlan = ctx.subscription?.plan || "free";

  return (
    <Dialog open={ctx.showPricingDialog} onOpenChange={ctx.setShowPricingDialog}>
      <DialogContent className="pricing-dialog" data-testid="pricing-dialog">
        <DialogHeader>
          <DialogTitle className="pricing-dialog-title">
            <Crown size={22} /> Choose Your Plan
          </DialogTitle>
          <DialogDescription className="pricing-dialog-desc">
            Unlock AI world generation and more with a premium plan
          </DialogDescription>
        </DialogHeader>

        {checkoutResult === "verifying" && (
          <div className="pricing-status" data-testid="pricing-verifying">
            <Loader2 className="animate-spin" size={24} />
            <span>Verifying your payment...</span>
          </div>
        )}

        {checkoutResult === "paid" && (
          <div className="pricing-status pricing-success" data-testid="pricing-success">
            <Check size={24} />
            <span>Payment successful! Your plan has been upgraded.</span>
            <Button size="sm" onClick={() => { setCheckoutResult(null); ctx.setShowPricingDialog(false); }}>
              Start Building
            </Button>
          </div>
        )}

        {checkoutResult === "cancelled" && (
          <div className="pricing-status pricing-cancelled" data-testid="pricing-cancelled">
            <X size={24} />
            <span>Checkout was cancelled. You can try again anytime.</span>
          </div>
        )}

        {checkoutResult !== "verifying" && checkoutResult !== "paid" && (
          <div className="pricing-grid" data-testid="pricing-grid">
            {PLANS.map((plan) => {
              const Icon = plan.icon;
              const isCurrent = currentPlan === plan.id;

              return (
                <div
                  key={plan.id}
                  className={`pricing-card ${plan.popular ? "pricing-popular" : ""} ${isCurrent ? "pricing-current" : ""}`}
                  data-testid={`pricing-card-${plan.id}`}
                >
                  {plan.popular && <div className="pricing-popular-badge">Most Popular</div>}
                  <div className="pricing-card-header">
                    <Icon size={28} style={{ color: plan.color }} />
                    <h3 className="pricing-plan-name">{plan.name}</h3>
                    <p className="pricing-plan-desc">{plan.description}</p>
                  </div>

                  <div className="pricing-price">
                    <span className="pricing-amount">${plan.price}</span>
                    {plan.price > 0 && <span className="pricing-period">/month</span>}
                  </div>

                  <ul className="pricing-features">
                    {plan.features.map((f, i) => (
                      <li key={i} className="pricing-feature-item">
                        <Check size={14} className="pricing-check" />
                        <span>{f}</span>
                      </li>
                    ))}
                    {plan.excluded.map((f, i) => (
                      <li key={`ex-${i}`} className="pricing-feature-item pricing-excluded">
                        <X size={14} className="pricing-x" />
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>

                  <div className="pricing-card-footer">
                    {isCurrent ? (
                      <Badge variant="outline" className="pricing-current-badge" data-testid={`current-plan-${plan.id}`}>
                        Current Plan
                      </Badge>
                    ) : plan.price === 0 ? (
                      <span className="pricing-free-label">Free forever</span>
                    ) : (
                      <Button
                        className="pricing-upgrade-btn"
                        onClick={() => ctx.startCheckout(plan.id)}
                        disabled={ctx.checkoutLoading}
                        data-testid={`checkout-${plan.id}`}
                      >
                        {ctx.checkoutLoading ? (
                          <Loader2 className="animate-spin" size={16} />
                        ) : (
                          <>Upgrade to {plan.name}</>
                        )}
                      </Button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
