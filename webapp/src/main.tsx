import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import { SWRConfig } from "swr";
import { Toaster } from "@/components/ui/sonner";
import { router } from "./router";
import { swrConfig } from "./api/swr";
import "./globals.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <SWRConfig value={swrConfig}>
      <RouterProvider router={router} />
      <Toaster />
    </SWRConfig>
  </StrictMode>,
);
