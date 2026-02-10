const API_BASE = (import.meta.env.VITE_API_BASE as string) || "http://localhost:8000";

type CheckoutResponse = {
  checkout_url: string;
};

export async function createCheckout(accessToken: string, productId: string): Promise<string> {
  const response = await fetch(`${API_BASE}/api/checkout`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ product_id: productId }),
  });

  if (!response.ok) {
    let detail = "Checkout request failed";
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      // Keep generic fallback.
    }
    throw new Error(detail);
  }

  const payload = (await response.json()) as CheckoutResponse;
  if (!payload.checkout_url) {
    throw new Error("Missing checkout URL");
  }

  return payload.checkout_url;
}
