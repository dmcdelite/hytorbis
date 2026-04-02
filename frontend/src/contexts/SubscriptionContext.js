import { createContext, useContext, useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/config";
import { useAuth } from "./AuthContext";

const SubscriptionContext = createContext(null);
export const useSubscription = () => useContext(SubscriptionContext);

export function SubscriptionProvider({ children }) {
  const { currentUser } = useAuth();

  const [subscription, setSubscription] = useState({ plan: "free", limits: null });
  const [showPricingDialog, setShowPricingDialog] = useState(false);
  const [showSubscriptionDialog, setShowSubscriptionDialog] = useState(false);
  const [paymentHistory, setPaymentHistory] = useState([]);
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  useEffect(() => {
    if (currentUser) { fetchSubscriptionStatus(); }
    else { setSubscription({ plan: "free", limits: null }); }
  }, [currentUser]);

  const fetchSubscriptionStatus = async () => {
    try {
      const response = await axios.get(`${API}/subscription/status`);
      setSubscription(response.data);
    } catch (e) { setSubscription({ plan: "free", limits: null }); }
  };

  const startCheckout = async (planId) => {
    setCheckoutLoading(true);
    try {
      const response = await axios.post(`${API}/subscription/checkout/stripe`, {
        plan_id: planId, origin_url: window.location.origin,
      });
      if (response.data.url) window.location.href = response.data.url;
    } catch (e) { alert(e.response?.data?.detail || "Failed to start checkout"); }
    setCheckoutLoading(false);
  };

  const verifyCheckout = async (sessionId) => {
    try {
      const response = await axios.get(`${API}/subscription/checkout/status/${sessionId}`);
      if (response.data.status === "paid") { await fetchSubscriptionStatus(); return "paid"; }
      return response.data.status;
    } catch (e) { return "error"; }
  };

  const isFeatureGated = (feature) => {
    const plan = subscription?.plan || "free";
    const gateMap = {
      ai: plan === "free",
      collab: plan === "free",
      analytics: plan === "free" || plan === "creator",
      version_history: plan === "free",
    };
    return gateMap[feature] || false;
  };

  const createPaypalOrder = async (planId) => {
    try {
      const response = await axios.post(`${API}/subscription/checkout/paypal`, {
        plan_id: planId, origin_url: window.location.origin,
      });
      return response.data.order_id;
    } catch (e) { throw new Error(e.response?.data?.detail || "Failed to create PayPal order"); }
  };

  const capturePaypalOrder = async (orderId) => {
    try {
      const response = await axios.post(`${API}/subscription/paypal/capture/${orderId}`);
      if (response.data.status === "paid") { await fetchSubscriptionStatus(); return "paid"; }
      return response.data.status;
    } catch (e) { return "error"; }
  };

  const fetchPaymentHistory = async () => {
    try {
      const response = await axios.get(`${API}/subscription/history`);
      setPaymentHistory(response.data.transactions || []);
    } catch (e) { setPaymentHistory([]); }
  };

  const cancelSubscription = async () => {
    try {
      const response = await axios.post(`${API}/subscription/cancel`);
      if (response.data.status === "cancelled") { await fetchSubscriptionStatus(); return true; }
      return false;
    } catch (e) { alert(e.response?.data?.detail || "Failed to cancel"); return false; }
  };

  const value = {
    subscription, showPricingDialog, setShowPricingDialog, checkoutLoading,
    showSubscriptionDialog, setShowSubscriptionDialog, paymentHistory,
    fetchSubscriptionStatus, startCheckout, verifyCheckout, isFeatureGated,
    createPaypalOrder, capturePaypalOrder, fetchPaymentHistory, cancelSubscription,
  };

  return <SubscriptionContext.Provider value={value}>{children}</SubscriptionContext.Provider>;
}
