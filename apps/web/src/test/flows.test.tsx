import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => {
  const signInWithPassword = vi.fn();
  const signUp = vi.fn();
  const getSession = vi.fn();
  const getUser = vi.fn();
  const signOut = vi.fn();
  const productsEq = vi.fn();
  const entitlementsEq = vi.fn();
  const entitlementsLimit = vi.fn();
  const createCheckout = vi.fn();
  const redirectTo = vi.fn();

  return {
    signInWithPassword,
    signUp,
    getSession,
    getUser,
    signOut,
    productsEq,
    entitlementsEq,
    entitlementsLimit,
    createCheckout,
    redirectTo,
  };
});

vi.mock("../lib/api", () => ({
  createCheckout: mocks.createCheckout,
}));

vi.mock("../lib/navigation", () => ({
  redirectTo: mocks.redirectTo,
}));

vi.mock("../lib/supabase", () => ({
  supabase: {
    auth: {
      signInWithPassword: mocks.signInWithPassword,
      signUp: mocks.signUp,
      getSession: mocks.getSession,
      getUser: mocks.getUser,
      signOut: mocks.signOut,
    },
    from: (table: string) => {
      if (table === "products") {
        return {
          select: () => ({ eq: mocks.productsEq }),
        };
      }

      if (table === "entitlements") {
        return {
          select: () => ({ eq: mocks.entitlementsEq }),
        };
      }

      throw new Error(`Unexpected table: ${table}`);
    },
  },
}));

import { LoginPage } from "../pages/LoginPage";
import { ProductsPage } from "../pages/ProductsPage";
import { SuccessPage } from "../pages/SuccessPage";

describe("web flow", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mocks.signInWithPassword.mockResolvedValue({ error: null });
    mocks.signUp.mockResolvedValue({ error: null });
    mocks.getSession.mockResolvedValue({ data: { session: { access_token: "token-123" } } });
    mocks.getUser.mockResolvedValue({ data: { user: { id: "user-1" } } });
    mocks.signOut.mockResolvedValue({ error: null });

    mocks.productsEq.mockResolvedValue({
      data: [{ id: "prod-1", name: "Starter Pack", price_cents: 1500, currency: "USD" }],
      error: null,
    });

    mocks.entitlementsEq.mockReturnValue({ limit: mocks.entitlementsLimit });
    mocks.entitlementsLimit.mockResolvedValue({
      data: [{ id: "ent-1" }],
      error: null,
    });

    mocks.createCheckout.mockResolvedValue("https://checkout.test/session-1");
  });

  it("signs in from login page", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText("Email"), "user@example.com");
    await user.type(screen.getByLabelText("Password"), "pass1234");
    await user.click(screen.getByRole("button", { name: "Sign In" }));

    await waitFor(() => {
      expect(mocks.signInWithPassword).toHaveBeenCalledWith({
        email: "user@example.com",
        password: "pass1234",
      });
    });
  });

  it("creates checkout from products page", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <ProductsPage />
      </MemoryRouter>,
    );

    await screen.findByText("Starter Pack");

    await user.click(screen.getByRole("button", { name: "Buy" }));

    await waitFor(() => {
      expect(mocks.createCheckout).toHaveBeenCalledWith("token-123", "prod-1");
      expect(mocks.redirectTo).toHaveBeenCalledWith("https://checkout.test/session-1");
    });
  });

  it("shows unlocked status on success page", async () => {
    render(
      <MemoryRouter>
        <SuccessPage />
      </MemoryRouter>,
    );

    await screen.findByText("Unlocked");
  });
});
