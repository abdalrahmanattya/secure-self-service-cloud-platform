import { lazy, StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CssBaseline, ThemeProvider } from "@mui/material";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { theme } from "./theme";

const queryClient = new QueryClient();

const DashboardPage = lazy(() =>
  import("./pages/DashboardPage").then(({ DashboardPage }) => ({
    default: DashboardPage,
  })),
);
const SetupPage = lazy(() =>
  import("./pages/SetupPage").then(({ SetupPage }) => ({ default: SetupPage })),
);
const NewRequestPage = lazy(() =>
  import("./pages/NewRequestPage").then(({ NewRequestPage }) => ({
    default: NewRequestPage,
  })),
);
const RequestPage = lazy(() =>
  import("./pages/RequestPage").then(({ RequestPage }) => ({
    default: RequestPage,
  })),
);
const ReadinessPage = lazy(() =>
  import("./pages/ReadinessPage").then(({ ReadinessPage }) => ({
    default: ReadinessPage,
  })),
);
const OperationsPage = lazy(() =>
  import("./pages/OperationsPage").then(({ OperationsPage }) => ({
    default: OperationsPage,
  })),
);
const ProposalPage = lazy(() =>
  import("./pages/ProposalPage").then(({ ProposalPage }) => ({
    default: ProposalPage,
  })),
);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            <Route element={<Layout />}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/setup" element={<SetupPage />} />
              <Route path="/requests/new" element={<NewRequestPage />} />
              <Route path="/requests/:requestId" element={<RequestPage />} />
              <Route path="/readiness" element={<ReadinessPage />} />
              <Route path="/operations" element={<OperationsPage />} />
              <Route path="/proposals/:proposalId" element={<ProposalPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </ThemeProvider>
  </StrictMode>,
);
