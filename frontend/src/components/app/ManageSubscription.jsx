import { useState, useEffect } from "react";
import { useApp } from "@/contexts/AppContext";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Crown, Sparkles, Zap, CreditCard, Calendar, Check } from "lucide-react";

const PLAN_META = {
  free: { name: "Explorer", icon: Zap, color: "var(--text-secondary)" },
  creator: { name: "Creator", icon: Sparkles, color: "var(--brand-primary)" },
  developer: { name: "Developer", icon: Crown, color: "var(--brand-warning)" },
};

export function ManageSubscription() {
  const ctx = useApp();
  const [showCancel, setShowCancel] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [cancelled, setCancelled] = useState(false);

  const plan = ctx.subscription?.plan || "free";
  const meta = PLAN_META[plan] || PLAN_META.free;
  const Icon = meta.icon;
  const sub = ctx.subscription?.subscription;

  useEffect(() => {
    if (ctx.showSubscriptionDialog) {
      ctx.fetchPaymentHistory();
      setCancelled(false);
      setShowCancel(false);
    }
  }, [ctx.showSubscriptionDialog]);

  const handleCancel = async () => {
    setCancelling(true);
    const ok = await ctx.cancelSubscription();
    setCancelling(false);
    if (ok) setCancelled(true);
  };

  return (
    <Dialog open={ctx.showSubscriptionDialog} onOpenChange={ctx.setShowSubscriptionDialog}>
      <DialogContent className="manage-sub-dialog" data-testid="manage-subscription-dialog">
        <DialogHeader>
          <DialogTitle className="manage-sub-title">Subscription</DialogTitle>
          <DialogDescription className="sr-only">Manage your subscription plan and view payment history</DialogDescription>
        </DialogHeader>

        {/* Current Plan Card */}
        <div className="manage-sub-plan" data-testid="manage-sub-plan">
          <div className="manage-sub-plan-info">
            <Icon size={32} style={{ color: meta.color }} />
            <div>
              <h3 className="manage-sub-plan-name">{meta.name} Plan</h3>
              {plan === "free" ? (
                <span className="manage-sub-plan-price">Free</span>
              ) : (
                <span className="manage-sub-plan-price">
                  ${plan === "creator" ? "9" : "29"}/month
                </span>
              )}
            </div>
          </div>
          {sub?.started_at && (
            <div className="manage-sub-meta">
              <Calendar size={13} />
              <span>Since {new Date(sub.started_at).toLocaleDateString()}</span>
              {sub.provider && (
                <Badge variant="outline" className="manage-sub-provider">
                  {sub.provider === "stripe" ? "Card" : "PayPal"}
                </Badge>
              )}
            </div>
          )}
          {plan === "free" && (
            <Button
              size="sm"
              className="manage-sub-upgrade-btn"
              onClick={() => { ctx.setShowSubscriptionDialog(false); ctx.setShowPricingDialog(true); }}
              data-testid="manage-sub-upgrade"
            >
              <Crown size={14} /> Upgrade Plan
            </Button>
          )}
        </div>

        {/* Payment History */}
        {ctx.paymentHistory.length > 0 && (
          <div className="manage-sub-history" data-testid="manage-sub-history">
            <h4 className="manage-sub-section-title">Payment History</h4>
            <div className="manage-sub-txns">
              {ctx.paymentHistory.map((txn, i) => (
                <div key={i} className="manage-sub-txn">
                  <div className="manage-sub-txn-left">
                    <CreditCard size={14} />
                    <span className="manage-sub-txn-plan">
                      {PLAN_META[txn.plan_id]?.name || txn.plan_id} Plan
                    </span>
                  </div>
                  <div className="manage-sub-txn-right">
                    <span className="manage-sub-txn-amount">${txn.amount?.toFixed(2)}</span>
                    <Badge
                      variant="outline"
                      className={`manage-sub-txn-status ${txn.payment_status === "paid" ? "status-paid" : ""}`}
                    >
                      {txn.payment_status === "paid" && <Check size={10} />}
                      {txn.payment_status}
                    </Badge>
                    <span className="manage-sub-txn-date">
                      {new Date(txn.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Cancel - deliberately subtle */}
        {plan !== "free" && !cancelled && (
          <div className="manage-sub-footer">
            {!showCancel ? (
              <button
                className="manage-sub-cancel-trigger"
                onClick={() => setShowCancel(true)}
                data-testid="manage-sub-cancel-trigger"
              >
                Need to make changes to your plan?
              </button>
            ) : (
              <div className="manage-sub-cancel-confirm" data-testid="manage-sub-cancel-confirm">
                <p className="manage-sub-cancel-text">
                  Your plan will revert to Explorer (Free). You'll lose access to AI features and collaboration.
                </p>
                <div className="manage-sub-cancel-actions">
                  <button
                    className="manage-sub-cancel-btn"
                    onClick={handleCancel}
                    disabled={cancelling}
                    data-testid="manage-sub-cancel-btn"
                  >
                    {cancelling ? "Processing..." : "Cancel subscription"}
                  </button>
                  <button
                    className="manage-sub-cancel-nevermind"
                    onClick={() => setShowCancel(false)}
                  >
                    Never mind
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {cancelled && (
          <div className="manage-sub-cancelled" data-testid="manage-sub-cancelled">
            <p>Your subscription has been cancelled. You're now on the Explorer (Free) plan.</p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
