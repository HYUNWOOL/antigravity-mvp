import { useEffect, useState } from "react";

import { createCheckout } from "../lib/api";
import { redirectTo } from "../lib/navigation";
import { supabase } from "../lib/supabase";

type Product = {
  id: string;
  name: string;
  price_cents: number;
  currency: string;
};

export function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState("");

  useEffect(() => {
    async function loadProducts() {
      setLoading(true);
      setError("");

      const { data, error: queryError } = await supabase
        .from("products")
        .select("id, name, price_cents, currency")
        .eq("active", true);

      setLoading(false);

      if (queryError) {
        setError(queryError.message);
        return;
      }

      setProducts((data as Product[]) ?? []);
    }

    void loadProducts();
  }, []);

  async function handleBuy(product: Product) {
    setBusyId(product.id);
    setError("");

    const sessionResponse = await supabase.auth.getSession();
    const accessToken = sessionResponse.data.session?.access_token;

    if (!accessToken) {
      setBusyId("");
      setError("Session expired. Please sign in again.");
      return;
    }

    try {
      const checkoutUrl = await createCheckout(accessToken, product.id);
      redirectTo(checkoutUrl);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create checkout");
      setBusyId("");
    }
  }

  async function handleSignOut() {
    await supabase.auth.signOut();
    redirectTo("/login");
  }

  return (
    <div className="page">
      <div className="content">
        <div className="header-row">
          <h1>Products</h1>
          <button type="button" className="secondary" onClick={handleSignOut}>Sign Out</button>
        </div>

        {loading ? <p>Loading products...</p> : null}
        {error ? <p className="error">{error}</p> : null}

        <div className="grid">
          {products.map((product) => (
            <article className="card" key={product.id}>
              <h2>{product.name}</h2>
              <p>
                {(product.price_cents / 100).toFixed(2)} {product.currency}
              </p>
              <button
                type="button"
                onClick={() => void handleBuy(product)}
                disabled={busyId === product.id}
              >
                {busyId === product.id ? "Starting checkout..." : "Buy"}
              </button>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}
