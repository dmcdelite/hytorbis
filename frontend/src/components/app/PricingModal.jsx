import { useEffect, useState } from "react";
import { useApp } from "@/contexts/AppContext";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Check, Loader2, Sparkles, Crown, Zap, X, CreditCard, ArrowLeft } from "lucide-react";
import { PayPalScriptProvider, PayPalButtons } from "@paypal/react-paypal-js";

const PAYPAL_CLIENT_ID = process.env.REACT_APP_PAYPAL_CLIENT_ID;

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
  const [selectedPlan, setSelectedPlan] = useState(null);

  // Handle Stripe checkout return from URL params
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sessionId = params.get("session_id");
    const cancelled = params.get("cancelled");

    if (sessionId) {
      ctx.setShowPricingDialog(true);
      setCheckoutResult("verifying");
      ctx.verifyCheckout(sessionId).then((status) => {
        setCheckoutResult(status);
        window.history.replaceState({}, document.title, window.location.pathname);
      });
    } else if (cancelled) {
      ctx.setShowPricingDialog(true);
      setCheckoutResult("cancelled");
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  const currentPlan = ctx.subscription?.plan || "free";

  const handleSelectPlan = (planId) => {
    setSelectedPlan(planId);
    setCheckoutResult(null);
  };

  const handleBack = () => {
    setSelectedPlan(null);
    setCheckoutResult(null);
  };

  const handlePayPalSuccess = async (orderId) => {
    setCheckoutResult("verifying");
    try {
      const result = await ctx.capturePaypalOrder(orderId);
      if (result === "paid") {
        setCheckoutResult("paid");
      } else {
        setCheckoutResult("error");
      }
    } catch {
      setCheckoutResult("error");
    }
  };

  return (
    <Dialog open={ctx.showPricingDialog} onOpenChange={(open) => {
      ctx.setShowPricingDialog(open);
      if (!open) { setSelectedPlan(null); setCheckoutResult(null); }
    }}>
      <DialogContent className="pricing-dialog" data-testid="pricing-dialog">
        <DialogHeader>
          <DialogTitle className="pricing-dialog-title">
            <Crown size={22} />
            {selectedPlan ? "Choose Payment Method" : "Choose Your Plan"}
          </DialogTitle>
          <DialogDescription className="pricing-dialog-desc">
            {selectedPlan
              ? `Upgrade to ${PLANS.find(p => p.id === selectedPlan)?.name} — $${PLANS.find(p => p.id === selectedPlan)?.price}/month`
              : "Unlock AI world generation and more with a premium plan"}
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
            <Button size="sm" onClick={() => { setCheckoutResult(null); setSelectedPlan(null); ctx.setShowPricingDialog(false); }}>
              Start Building
            </Button>
          </div>
        )}

        {checkoutResult === "cancelled" && (
          <div className="pricing-status pricing-cancelled" data-testid="pricing-cancelled">
            <X size={24} />
            <span>Checkout was cancelled. You can try again anytime.</span>
            <Button size="sm" variant="outline" onClick={() => setCheckoutResult(null)}>Try Again</Button>
          </div>
        )}

        {checkoutResult === "error" && (
          <div className="pricing-status pricing-cancelled" data-testid="pricing-error">
            <X size={24} />
            <span>Something went wrong. Please try again.</span>
            <Button size="sm" variant="outline" onClick={() => { setCheckoutResult(null); setSelectedPlan(null); }}>Try Again</Button>
          </div>
        )}

        {/* Payment method selection */}
        {selectedPlan && !checkoutResult && (
          <div className="payment-methods" data-testid="payment-methods">
            <Button variant="ghost" size="sm" onClick={handleBack} className="payment-back-btn" data-testid="payment-back-btn">
              <ArrowLeft size={16} /> Back to plans
            </Button>

            <div className="payment-options">
              {/* Stripe */}
              <button
                className="payment-option"
                onClick={() => ctx.startCheckout(selectedPlan)}
                disabled={ctx.checkoutLoading}
                data-testid="pay-stripe"
              >
                <CreditCard size={28} />
                <span className="payment-option-title">Credit / Debit Card</span>
                <span className="payment-option-desc">Pay securely with Stripe</span>
                {ctx.checkoutLoading && <Loader2 className="animate-spin payment-option-loader" size={18} />}
              </button>

              {/* PayPal */}
              <div className="payment-option payment-option-paypal" data-testid="pay-paypal">
                <div className="paypal-label">
                  <svg viewBox="0 0 24 24" width="28" height="28" fill="none"><path d="M7.076 21.337H2.47a.641.641 0 0 1-.633-.74L4.944.901C5.026.382 5.474 0 5.998 0h7.46c2.57 0 4.578.543 5.69 1.81 1.01 1.15 1.304 2.42 1.012 4.287-.023.143-.047.288-.077.437-.983 5.05-4.349 6.797-8.647 6.797H9.603c-.536 0-.99.39-1.075.919l-.952 6.087Z" fill="#253B80"/><path d="M8.076 21.337H5.47a.641.641 0 0 1-.633-.74L7.944.901C8.026.382 8.474 0 8.998 0h7.46c2.57 0 4.578.543 5.69 1.81.386.44.655.935.822 1.48-1.192-.58-2.607-.86-4.353-.86H11.47c-.536 0-.99.39-1.075.919L8.076 21.337Z" fill="#179BD7"/></svg>
                  <div>
                    <span className="payment-option-title">PayPal</span>
                    <span className="payment-option-desc">Pay with your PayPal account</span>
                  </div>
                </div>
                <PayPalScriptProvider options={{ clientId: PAYPAL_CLIENT_ID, currency: "USD" }}>
                  <PayPalButtons
                    style={{ layout: "horizontal", color: "blue", shape: "rect", label: "paypal", height: 40 }}
                    createOrder={async () => {
                      const result = await ctx.createPaypalOrder(selectedPlan);
                      return result;
                    }}
                    onApprove={async (data) => {
                      await handlePayPalSuccess(data.orderID);
                    }}
                    onCancel={() => setCheckoutResult("cancelled")}
                    onError={() => setCheckoutResult("error")}
                  />
                </PayPalScriptProvider>
              </div>
            </div>
          </div>
        )}

        {/* Plan selection grid */}
        {!selectedPlan && !checkoutResult && (
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
                        onClick={() => handleSelectPlan(plan.id)}
                        data-testid={`select-plan-${plan.id}`}
                      >
                        Upgrade to {plan.name}
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
