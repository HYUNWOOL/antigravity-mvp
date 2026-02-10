import { useEffect, useState } from "react";

import { supabase } from "../lib/supabase";

type Status = "processing" | "unlocked" | "pending" | "error";

const MAX_ATTEMPTS = 5;
const POLL_DELAY_MS = 1500;

function sleep(ms: number) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

export function SuccessPage() {
  const [status, setStatus] = useState<Status>("processing");
  const [message, setMessage] = useState("Processing payment...");

  useEffect(() => {
    let active = true;

    async function pollEntitlements() {
      for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt += 1) {
        const userResponse = await supabase.auth.getUser();
        const user = userResponse.data.user;

        if (!user) {
          if (active) {
            setStatus("error");
            setMessage("No active user session.");
          }
          return;
        }

        const { data, error } = await supabase
          .from("entitlements")
          .select("id")
          .eq("user_id", user.id)
          .limit(1);

        if (error) {
          if (active) {
            setStatus("error");
            setMessage(error.message);
          }
          return;
        }

        if ((data?.length ?? 0) > 0) {
          if (active) {
            setStatus("unlocked");
            setMessage("Unlocked");
          }
          return;
        }

        if (attempt < MAX_ATTEMPTS) {
          await sleep(POLL_DELAY_MS);
        }
      }

      if (active) {
        setStatus("pending");
        setMessage("Still processing, refresh later");
      }
    }

    void pollEntitlements();

    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="page">
      <div className="card">
        <h1>Payment Status</h1>
        <p>{message}</p>
        {status === "processing" ? <p>Checking entitlement...</p> : null}
        <a className="button-link" href="/products">Back to products</a>
      </div>
    </div>
  );
}
