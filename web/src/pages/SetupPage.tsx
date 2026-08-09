import CheckCircleRoundedIcon from "@mui/icons-material/CheckCircleRounded";
import CloudOutlinedIcon from "@mui/icons-material/CloudOutlined";
import SecurityOutlinedIcon from "@mui/icons-material/SecurityOutlined";
import WarningAmberRoundedIcon from "@mui/icons-material/WarningAmberRounded";
import {
  Alert,
  Box,
  Button,
  Card,
  CardActionArea,
  CardContent,
  Grid,
  MenuItem,
  Skeleton,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api, apiErrorFields, apiErrorMessage } from "../api/client";
import type { InstallationMode, Provider } from "../api/client";
import { PageHeader } from "../components/PageHeader";
import { ProviderBadge, StatusBadge } from "../components/StatusBadge";
import { SectionCard } from "../components/SectionCard";

const providerIcons: Record<Provider, React.ReactNode> = {
  aws: <CloudOutlinedIcon sx={{ fontSize: 36 }} />,
  azure: <CloudOutlinedIcon sx={{ fontSize: 36 }} />,
};

const modeDescriptions: Record<InstallationMode, string> = {
  simulation:
    "Evaluate the full request and proposal flow locally with no credentials or cloud calls.",
  sandbox:
    "Prepare constrained, non-production proposals for a single account or subscription.",
  enterprise:
    "Prepare governed proposals for an organization with separated production boundaries.",
};

function ChoiceCard({
  title,
  description,
  selected,
  onSelect,
  icon,
  value,
  groupLabel,
}: {
  title: string;
  description: string;
  selected: boolean;
  onSelect: () => void;
  icon?: React.ReactNode;
  value: string;
  groupLabel: string;
}) {
  return (
    <Card
      variant="outlined"
      sx={{
        height: "100%",
        borderColor: selected ? "primary.main" : "divider",
        bgcolor: selected ? "rgba(8,127,140,0.045)" : "background.paper",
        boxShadow: selected ? "0 0 0 2px rgba(8,127,140,0.14)" : undefined,
      }}
    >
      <CardActionArea
        component="div"
        role="radio"
        aria-checked={selected}
        aria-label={`${groupLabel}: ${title}`}
        tabIndex={0}
        onClick={onSelect}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            onSelect();
          }
        }}
        sx={{ height: "100%" }}
      >
        <CardContent>
          <Stack direction="row" justifyContent="space-between" gap={2}>
            <Stack spacing={1}>
              <Stack
                direction="row"
                spacing={1.25}
                alignItems="center"
                color="primary.main"
              >
                {icon}
                <Typography variant="h3">{title}</Typography>
              </Stack>
              <Typography variant="body2" color="text.secondary">
                {description}
              </Typography>
            </Stack>
            {selected && (
              <CheckCircleRoundedIcon
                color="primary"
                aria-label={`${value} selected`}
              />
            )}
          </Stack>
        </CardContent>
      </CardActionArea>
    </Card>
  );
}

export function SetupPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [provider, setProvider] = useState<Provider>("aws");
  const [mode, setMode] = useState<InstallationMode>("simulation");
  const providers = useQuery({
    queryKey: ["providers"],
    queryFn: api.providers,
  });
  const modes = useQuery({ queryKey: ["modes"], queryFn: api.modes });
  const providerHasOption = providers.data?.providers.some(
    (item) => item.provider === provider,
  );
  const modeHasOption = modes.data?.modes.some((item) => item.mode === mode);
  const selectedProvider = providers.data?.providers.find(
    (item) => item.provider === provider,
  );
  const selectedMode = modes.data?.modes.find((item) => item.mode === mode);
  const mutation = useMutation({
    mutationFn: () => api.createInstallation(provider, mode),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["installation"] });
      navigate("/");
    },
  });

  return (
    <Stack spacing={3}>
      <PageHeader
        eyebrow="Installation setup"
        title="Choose your platform"
        description="Create one provider-locked installation. Start in simulation to explore the experience, or prepare a sandbox or enterprise deployment boundary."
      />

      {(providers.isError || modes.isError) && (
        <Alert severity="error">
          Provider or mode discovery is unavailable. Start the local API and try
          again.
        </Alert>
      )}

      <SectionCard
        title="1. Select a cloud provider"
        description="The provider is locked after setup. AWS and Azure are separate installation choices, not a hybrid deployment."
      >
        <Grid container spacing={2} role="radiogroup" aria-label="Provider">
          {providers.isPending &&
            [1, 2].map((item) => (
              <Grid key={item} size={{ xs: 12, md: 6 }}>
                <Skeleton variant="rounded" height={136} />
              </Grid>
            ))}
          {!providers.isPending &&
            (providers.data?.providers ?? []).map((item) => (
              <Grid key={item.provider} size={{ xs: 12, md: 6 }}>
                <ChoiceCard
                  value={item.provider}
                  groupLabel="Provider"
                  title={item.display_name}
                  description={item.description}
                  icon={providerIcons[item.provider]}
                  selected={provider === item.provider}
                  onSelect={() => setProvider(item.provider)}
                />
              </Grid>
            ))}
          {!providers.isPending && !providerHasOption && (
            <Grid size={{ xs: 12 }}>
              <Alert severity="info">
                No provider options are currently available.
              </Alert>
            </Grid>
          )}
        </Grid>
        <TextField
          select
          fullWidth
          label="Provider"
          value={provider}
          onChange={(event) => setProvider(event.target.value as Provider)}
          helperText="Use the cards above or this keyboard-friendly selection control. Provider is locked after setup."
          sx={{ mt: 2 }}
        >
          {!providerHasOption && (
            <MenuItem value={provider} disabled>
              {providers.isPending
                ? "Loading providers…"
                : `${provider.toUpperCase()} unavailable`}
            </MenuItem>
          )}
          {(providers.data?.providers ?? []).map((item) => (
            <MenuItem key={item.provider} value={item.provider}>
              {item.display_name}
            </MenuItem>
          ))}
        </TextField>
      </SectionCard>

      <SectionCard
        title="2. Select an operating mode"
        description="Modes describe the guardrails and hand-off expected by the eventual deployment environment."
      >
        <Grid container spacing={2} role="radiogroup" aria-label="Mode">
          {modes.isPending &&
            [1, 2, 3].map((item) => (
              <Grid key={item} size={{ xs: 12, md: 4 }}>
                <Skeleton variant="rounded" height={182} />
              </Grid>
            ))}
          {!modes.isPending &&
            (modes.data?.modes ?? []).map((item) => (
              <Grid key={item.mode} size={{ xs: 12, md: 4 }}>
                <ChoiceCard
                  value={item.mode}
                  groupLabel="Mode"
                  title={item.display_name}
                  description={modeDescriptions[item.mode] ?? item.description}
                  icon={<SecurityOutlinedIcon sx={{ fontSize: 30 }} />}
                  selected={mode === item.mode}
                  onSelect={() => setMode(item.mode)}
                />
              </Grid>
            ))}
          {!modes.isPending && !modeHasOption && (
            <Grid size={{ xs: 12 }}>
              <Alert severity="info">
                No operating modes are currently available.
              </Alert>
            </Grid>
          )}
        </Grid>
        <TextField
          select
          fullWidth
          label="Mode"
          value={mode}
          onChange={(event) => setMode(event.target.value as InstallationMode)}
          helperText="Use the cards above or this keyboard-friendly selection control."
          sx={{ mt: 2 }}
        >
          {!modeHasOption && (
            <MenuItem value={mode} disabled>
              {modes.isPending ? "Loading modes…" : `${mode} unavailable`}
            </MenuItem>
          )}
          {(modes.data?.modes ?? []).map((item) => (
            <MenuItem key={item.mode} value={item.mode}>
              {item.display_name} — {item.execution}
            </MenuItem>
          ))}
        </TextField>
      </SectionCard>

      <SectionCard
        title="3. Review installation"
        description="Confirm the boundary before creating the local installation profile."
      >
        <Stack spacing={2}>
          <Box
            sx={{
              p: 2,
              borderRadius: 2,
              bgcolor: "grey.50",
              border: 1,
              borderColor: "divider",
            }}
          >
            <Stack
              direction={{ xs: "column", sm: "row" }}
              spacing={1.5}
              alignItems={{ sm: "center" }}
              flexWrap="wrap"
            >
              <ProviderBadge provider={providerHasOption ? provider : null} />
              <StatusBadge
                status={modeHasOption ? mode : "not_available"}
                label={
                  modeHasOption
                    ? selectedMode?.display_name
                    : "Mode unavailable"
                }
              />
              <Typography variant="body2" color="text.secondary">
                {selectedProvider?.display_name ?? "Provider discovery pending"}
              </Typography>
            </Stack>
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ mt: 1.25 }}
            >
              {modeDescriptions[mode]} Cloud changes are not executed by this
              portal; protected external workflows remain required.
            </Typography>
          </Box>
          {mode !== "simulation" && modeHasOption && (
            <Alert
              severity="warning"
              icon={<WarningAmberRoundedIcon />}
              role="status"
            >
              {mode} generates deterministic proposals locally without
              credentials. Cloud execution requires a protected external
              workflow and is not available from this portal.
            </Alert>
          )}
          <Button
            variant="contained"
            onClick={() => mutation.mutate()}
            disabled={
              mutation.isPending ||
              !providerHasOption ||
              !modeHasOption ||
              providers.isError ||
              modes.isError
            }
            sx={{ alignSelf: { xs: "stretch", sm: "flex-start" } }}
          >
            {mutation.isPending
              ? "Creating installation…"
              : "Create installation"}
          </Button>
          {mutation.isError && (
            <Alert severity="error" role="alert">
              {apiErrorMessage(
                mutation.error,
                "The installation could not be created.",
              )}
              {apiErrorFields(mutation.error).map((field) => (
                <Typography
                  key={`${field.code}-${field.field}`}
                  component="div"
                >
                  {field.field}: {field.message}
                </Typography>
              ))}
            </Alert>
          )}
          {mutation.data && (
            <Alert
              severity={
                mutation.data.validation?.allowed ? "success" : "warning"
              }
            >
              {mutation.data.validation?.allowed
                ? "Installation is ready."
                : "Installation created; readiness needs attention."}
            </Alert>
          )}
        </Stack>
      </SectionCard>
    </Stack>
  );
}
