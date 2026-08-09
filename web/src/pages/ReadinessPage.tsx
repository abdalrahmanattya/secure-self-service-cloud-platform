import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import CloudQueueOutlinedIcon from "@mui/icons-material/CloudQueueOutlined";
import LockOutlinedIcon from "@mui/icons-material/LockOutlined";
import PolicyOutlinedIcon from "@mui/icons-material/PolicyOutlined";
import RefreshOutlinedIcon from "@mui/icons-material/RefreshOutlined";
import {
  Alert,
  Button,
  CircularProgress,
  Stack,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { Link as RouterLink } from "react-router-dom";
import { api } from "../api/client";
import { EmptyState } from "../components/EmptyState";
import { MetricCard } from "../components/MetricCard";
import { PageHeader } from "../components/PageHeader";
import { ProviderBadge, StatusBadge } from "../components/StatusBadge";
import { SectionCard } from "../components/SectionCard";

const availableCapabilities = [
  {
    title: "Request evaluation",
    description:
      "Validate ownership, budget, network, data classification, and environment policies locally.",
    icon: <PolicyOutlinedIcon />,
  },
  {
    title: "Deterministic proposals",
    description:
      "Generate reviewable Terraform and policy artifacts from an accepted request without cloud credentials.",
    icon: <CheckCircleOutlineIcon />,
  },
  {
    title: "Provider-aware simulation",
    description:
      "Use the selected AWS or Azure adapter to preview the resources that a protected workflow would evaluate.",
    icon: <CloudQueueOutlinedIcon />,
  },
] as const;

const protectedPrerequisites = [
  [
    "GitHub review",
    "A private deployment repository and pull-request review process.",
  ],
  [
    "Protected plan and apply",
    "Manual, OIDC-only workflows with protected environment approval.",
  ],
  [
    "Cloud identity and state",
    "Administrator-supplied AWS or Azure identities, encrypted state, and secrets.",
  ],
  [
    "Operations",
    "Separate drift, rollback, destroy, logging, and incident runbooks.",
  ],
] as const;

function InstallationContext({
  installation,
}: {
  installation?: Awaited<ReturnType<typeof api.installation>>;
}) {
  if (!installation) return null;
  return (
    <Stack
      direction={{ xs: "column", sm: "row" }}
      spacing={1.5}
      alignItems={{ sm: "center" }}
      flexWrap="wrap"
    >
      <Stack spacing={0.25} minWidth={0} flex={1}>
        <Typography variant="overline" color="text.secondary">
          Active installation
        </Typography>
        <Typography fontWeight={750} noWrap>
          {installation.installation_id}
        </Typography>
      </Stack>
      <ProviderBadge provider={installation.provider} />
      <StatusBadge status={installation.mode} label={installation.mode} />
      <StatusBadge status={installation.status} />
    </Stack>
  );
}

export function ReadinessPage() {
  const installation = useQuery({
    queryKey: ["installation"],
    queryFn: api.installation,
    retry: false,
  });
  const providers = useQuery({
    queryKey: ["providers"],
    queryFn: api.providers,
  });
  const unconfigured = installation.isError || !installation.data;

  return (
    <Stack spacing={3}>
      <PageHeader
        eyebrow="Platform control plane"
        title="Platform readiness"
        description="Understand what is available before you request an environment, and what remains under protected administrator control."
        action={
          <Button component={RouterLink} to="/setup" variant="outlined">
            Review installation
          </Button>
        }
      />

      {installation.isLoading ? (
        <SectionCard
          title="Current installation"
          description="Loading the local platform context…"
        >
          <Stack direction="row" spacing={1} alignItems="center">
            <CircularProgress size={20} aria-label="Loading installation" />
            <Typography>Loading installation readiness…</Typography>
          </Stack>
        </SectionCard>
      ) : unconfigured ? (
        <SectionCard
          title="Current installation"
          description="Choose a provider and mode before using the control plane."
        >
          <EmptyState
            title="No installation has been created."
            description="The portal can evaluate requests only after an installation profile selects exactly one cloud provider."
            icon={<CloudQueueOutlinedIcon />}
            action={
              <Button component={RouterLink} to="/setup" variant="contained">
                Set up installation
              </Button>
            }
          />
        </SectionCard>
      ) : (
        <SectionCard
          title="Current installation"
          description="This provider and mode are the context used by request evaluation."
        >
          <InstallationContext installation={installation.data} />
        </SectionCard>
      )}

      <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
        <MetricCard
          label="Available now"
          value={unconfigured ? "—" : availableCapabilities.length}
          description="Credential-free control-plane capabilities"
          icon={<CheckCircleOutlineIcon />}
          accent="success"
        />
        <MetricCard
          label="Protected prerequisites"
          value={protectedPrerequisites.length}
          description="Administrator-owned deployment boundaries"
          icon={<LockOutlinedIcon />}
          accent="warning"
        />
        <MetricCard
          label="Cloud changes"
          value="0"
          description="No direct cloud execution from this portal"
          icon={<RefreshOutlinedIcon />}
          accent="info"
        />
      </Stack>

      <Stack
        direction={{ xs: "column", lg: "row" }}
        spacing={2}
        alignItems="stretch"
      >
        <Stack spacing={2} flex={1}>
          <SectionCard
            title="Available now"
            description="Safe local capabilities available in simulation and proposal-only modes."
          >
            <Stack spacing={1.5}>
              {availableCapabilities.map((item) => (
                <Stack
                  key={item.title}
                  direction="row"
                  spacing={1.5}
                  alignItems="flex-start"
                  sx={{
                    p: 1.5,
                    border: 1,
                    borderColor: "success.light",
                    borderRadius: 2,
                    bgcolor: "success.light",
                  }}
                >
                  <Stack
                    color="success.dark"
                    aria-hidden="true"
                    sx={{ mt: 0.25 }}
                  >
                    {item.icon}
                  </Stack>
                  <Stack spacing={0.35} minWidth={0}>
                    <Stack
                      direction="row"
                      spacing={1}
                      alignItems="center"
                      flexWrap="wrap"
                    >
                      <Typography fontWeight={750}>{item.title}</Typography>
                      <StatusBadge status="available" label="Available" />
                    </Stack>
                    <Typography variant="body2" color="text.secondary">
                      {item.description}
                    </Typography>
                  </Stack>
                </Stack>
              ))}
            </Stack>
          </SectionCard>
        </Stack>

        <Stack spacing={2} flex={1}>
          <SectionCard
            title="Protected external prerequisites"
            description="These stages require administrator-owned infrastructure and are not executed here."
          >
            <Stack spacing={1.5}>
              {protectedPrerequisites.map(([title, description]) => (
                <Stack
                  key={title}
                  direction="row"
                  spacing={1.5}
                  alignItems="flex-start"
                  sx={{
                    p: 1.5,
                    border: 1,
                    borderColor: "divider",
                    borderRadius: 2,
                  }}
                >
                  <Stack
                    color="warning.dark"
                    aria-hidden="true"
                    sx={{ mt: 0.25 }}
                  >
                    <LockOutlinedIcon />
                  </Stack>
                  <Stack spacing={0.35} minWidth={0}>
                    <Stack
                      direction="row"
                      spacing={1}
                      alignItems="center"
                      flexWrap="wrap"
                    >
                      <Typography fontWeight={750}>{title}</Typography>
                      <StatusBadge status="guarded" label="Guarded" />
                    </Stack>
                    <Typography variant="body2" color="text.secondary">
                      {description}
                    </Typography>
                  </Stack>
                </Stack>
              ))}
            </Stack>
          </SectionCard>
        </Stack>
      </Stack>

      <SectionCard
        title="Provider options"
        description="Available provider adapters exposed by the local API."
      >
        {providers.isLoading ? (
          <Stack direction="row" spacing={1} alignItems="center">
            <CircularProgress size={18} aria-label="Loading providers" />
            <Typography>Loading providers…</Typography>
          </Stack>
        ) : providers.isError ? (
          <Alert severity="error">
            Provider options could not be loaded from the local API.
          </Alert>
        ) : (providers.data?.providers ?? []).length === 0 ? (
          <EmptyState
            title="No provider options are available."
            description="Check the local API configuration and try again."
          />
        ) : (
          <Stack spacing={1}>
            {providers.data?.providers.map((item) => (
              <Stack
                key={item.provider}
                direction={{ xs: "column", sm: "row" }}
                spacing={1}
                alignItems={{ sm: "center" }}
                justifyContent="space-between"
                sx={{
                  p: 1.25,
                  borderBottom: 1,
                  borderColor: "divider",
                  "&:last-child": { borderBottom: 0 },
                }}
              >
                <Stack direction="row" spacing={1} alignItems="center">
                  <ProviderBadge provider={item.provider} />
                  <Typography fontWeight={700}>{item.display_name}</Typography>
                </Stack>
                <Stack
                  direction="row"
                  spacing={1}
                  alignItems="center"
                  flexWrap="wrap"
                  minWidth={0}
                  flex={1}
                >
                  <Typography variant="body2" color="text.secondary">
                    {item.description}
                  </Typography>
                  <StatusBadge
                    status={item.available ? "available" : "unavailable"}
                  />
                </Stack>
              </Stack>
            ))}
          </Stack>
        )}
      </SectionCard>
    </Stack>
  );
}
