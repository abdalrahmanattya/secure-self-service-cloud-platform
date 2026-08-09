import AccountTreeOutlinedIcon from "@mui/icons-material/AccountTreeOutlined";
import AttachMoneyOutlinedIcon from "@mui/icons-material/AttachMoneyOutlined";
import BusinessOutlinedIcon from "@mui/icons-material/BusinessOutlined";
import CloudOutlinedIcon from "@mui/icons-material/CloudOutlined";
import DescriptionOutlinedIcon from "@mui/icons-material/DescriptionOutlined";
import LanOutlinedIcon from "@mui/icons-material/LanOutlined";
import PolicyOutlinedIcon from "@mui/icons-material/PolicyOutlined";
import {
  Alert,
  Button,
  Grid,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useEffect, useRef } from "react";
import { useForm } from "react-hook-form";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  api,
  apiErrorFields,
  apiErrorMessage,
  type EnvironmentRequestInput,
} from "../api/client";
import { PageHeader } from "../components/PageHeader";
import { ProviderBadge, StatusBadge } from "../components/StatusBadge";
import { SectionCard } from "../components/SectionCard";

function defaultNonProductionExpiry() {
  const date = new Date();
  date.setDate(date.getDate() + 14);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

const defaults: EnvironmentRequestInput = {
  application: "",
  environment: "development",
  owner: "",
  cost_centre: "",
  data_classification: "internal",
  region: "",
  network_cidr: "10.42.0.0/16",
  cluster_size: "small",
  monthly_budget: "250.00",
  business_justification: "",
  non_production_expiry: defaultNonProductionExpiry(),
};

export function NewRequestPage() {
  const navigate = useNavigate();
  const installation = useQuery({
    queryKey: ["installation"],
    queryFn: api.installation,
    retry: false,
  });
  const form = useForm<EnvironmentRequestInput>({ defaultValues: defaults });
  const idempotencyKey = useRef(crypto.randomUUID());
  const watched = form.watch();

  useEffect(() => {
    const region = installation.data?.guardrails?.allowed_regions?.[0];
    if (region) form.setValue("region", region, { shouldValidate: true });
  }, [form, installation.data]);

  const mutation = useMutation({
    mutationFn: (input: EnvironmentRequestInput) =>
      api.createRequest(input, idempotencyKey.current),
    onSuccess: (result) => navigate(`/requests/${result.request.request_id}`),
  });
  const submit = (input: EnvironmentRequestInput) =>
    mutation.mutate({
      ...input,
      non_production_expiry:
        input.environment === "production" ? null : input.non_production_expiry,
    });
  const fieldError = (name: keyof EnvironmentRequestInput) =>
    form.formState.errors[name]?.message;

  return (
    <Stack spacing={3}>
      <PageHeader
        eyebrow="Environment request"
        title="New environment"
        description="Describe the environment your application needs. The configured installation evaluates it against policy before producing review evidence."
      />

      <Alert severity="info" role="status" icon={<PolicyOutlinedIcon />}>
        Provider and mode come from the active installation. This request can
        generate a deterministic proposal, but it cannot execute cloud changes.
      </Alert>

      <Grid container spacing={3} alignItems="flex-start">
        <Grid size={{ xs: 12, lg: 8 }}>
          <Stack
            component="form"
            spacing={2}
            onSubmit={form.handleSubmit(submit)}
          >
            <SectionCard
              title="Ownership"
              description="Identify the service and the people responsible for it."
            >
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField
                    fullWidth
                    label="Application"
                    {...form.register("application", {
                      required: "Application is required",
                    })}
                    error={Boolean(fieldError("application"))}
                    helperText={
                      fieldError("application") ?? "A short service name"
                    }
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField
                    fullWidth
                    label="Owner"
                    {...form.register("owner", {
                      required: "Owner is required",
                    })}
                    error={Boolean(fieldError("owner"))}
                    helperText={fieldError("owner")}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField
                    fullWidth
                    label="Cost centre"
                    {...form.register("cost_centre", {
                      required: "Cost centre is required",
                    })}
                    error={Boolean(fieldError("cost_centre"))}
                    helperText={fieldError("cost_centre")}
                  />
                </Grid>
              </Grid>
            </SectionCard>

            <SectionCard
              title="Environment intent"
              description="Set the lifecycle and data sensitivity for this environment."
            >
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField
                    fullWidth
                    select
                    label="Environment"
                    defaultValue={defaults.environment}
                    {...form.register("environment")}
                  >
                    <MenuItem value="development">Development</MenuItem>
                    <MenuItem value="test">Test</MenuItem>
                    <MenuItem value="production">Production</MenuItem>
                  </TextField>
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField
                    fullWidth
                    select
                    label="Data classification"
                    defaultValue={defaults.data_classification}
                    {...form.register("data_classification")}
                  >
                    <MenuItem value="public">Public</MenuItem>
                    <MenuItem value="internal">Internal</MenuItem>
                    <MenuItem value="confidential">Confidential</MenuItem>
                    <MenuItem value="restricted">Restricted</MenuItem>
                  </TextField>
                </Grid>
                <Grid size={{ xs: 12 }}>
                  <TextField
                    fullWidth
                    label="Why is this environment needed?"
                    multiline
                    minRows={3}
                    {...form.register("business_justification", {
                      required: "A business justification is required",
                    })}
                    error={Boolean(fieldError("business_justification"))}
                    helperText={fieldError("business_justification")}
                  />
                </Grid>
              </Grid>
            </SectionCard>

            <SectionCard
              title="Infrastructure"
              description="Choose the private network and compute shape for the request."
            >
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField
                    fullWidth
                    label="Region"
                    {...form.register("region", {
                      required: "Region is required",
                    })}
                    error={Boolean(fieldError("region"))}
                    helperText={
                      fieldError("region") ??
                      "Use a region enabled by the installation"
                    }
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField
                    fullWidth
                    label="Private network CIDR"
                    {...form.register("network_cidr", {
                      required: "Network CIDR is required",
                    })}
                    error={Boolean(fieldError("network_cidr"))}
                    helperText={fieldError("network_cidr")}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField
                    fullWidth
                    select
                    label="Cluster size"
                    defaultValue={defaults.cluster_size}
                    {...form.register("cluster_size")}
                  >
                    <MenuItem value="small">Small</MenuItem>
                    <MenuItem value="medium">Medium</MenuItem>
                    <MenuItem value="large">Large</MenuItem>
                  </TextField>
                </Grid>
              </Grid>
            </SectionCard>

            <SectionCard
              title="Governance"
              description="Set the budget and expiry guardrails that travel with the proposal."
            >
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField
                    fullWidth
                    label="Monthly budget"
                    type="number"
                    slotProps={{ htmlInput: { min: 1, step: "0.01" } }}
                    {...form.register("monthly_budget", {
                      required: "Budget is required",
                    })}
                    error={Boolean(fieldError("monthly_budget"))}
                    helperText={fieldError("monthly_budget")}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField
                    fullWidth
                    label="Expiry for non-production"
                    type="date"
                    slotProps={{ inputLabel: { shrink: true } }}
                    {...form.register("non_production_expiry")}
                  />
                </Grid>
              </Grid>
            </SectionCard>

            <Button
              type="submit"
              variant="contained"
              size="large"
              disabled={mutation.isPending}
              startIcon={<DescriptionOutlinedIcon />}
              sx={{ alignSelf: { xs: "stretch", sm: "flex-start" } }}
            >
              {mutation.isPending ? "Submitting request…" : "Review request"}
            </Button>
            {mutation.isError && (
              <Alert severity="error" role="alert">
                {apiErrorMessage(
                  mutation.error,
                  "The request could not be submitted.",
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
          </Stack>
        </Grid>

        <Grid size={{ xs: 12, lg: 4 }}>
          <Paper
            component="aside"
            aria-label="Request summary"
            variant="outlined"
            sx={{ p: 2.5, position: { lg: "sticky" }, top: { lg: 24 } }}
          >
            <Stack spacing={2}>
              <Stack direction="row" spacing={1.25} alignItems="center">
                <AccountTreeOutlinedIcon color="primary" />
                <Stack>
                  <Typography variant="h3">Request summary</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Live preview of the submitted intent
                  </Typography>
                </Stack>
              </Stack>
              <Stack spacing={1.25}>
                <SummaryRow
                  icon={<BusinessOutlinedIcon />}
                  label="Application"
                  value={watched.application || "Not provided"}
                />
                <SummaryRow
                  icon={<LanOutlinedIcon />}
                  label="Environment"
                  value={watched.environment}
                  capitalize
                />
                <SummaryRow
                  icon={<CloudOutlinedIcon />}
                  label="Region"
                  value={watched.region || "Installation default"}
                />
                <SummaryRow
                  icon={<AttachMoneyOutlinedIcon />}
                  label="Monthly budget"
                  value={
                    watched.monthly_budget
                      ? `${watched.monthly_budget} / month`
                      : "Not provided"
                  }
                />
              </Stack>
              <Stack
                spacing={1}
                sx={{ pt: 1.5, borderTop: 1, borderColor: "divider" }}
              >
                <Typography variant="overline" color="text.secondary">
                  Installation context
                </Typography>
                <Stack direction="row" gap={1} flexWrap="wrap">
                  <ProviderBadge provider={installation.data?.provider} />
                  <StatusBadge
                    status={installation.data?.mode ?? "not_configured"}
                    label={installation.data?.mode ?? "Mode not configured"}
                  />
                </Stack>
                <Typography variant="body2" color="text.secondary">
                  Provider cannot be changed per request. Policy evaluation
                  happens before proposal generation.
                </Typography>
              </Stack>
            </Stack>
          </Paper>
        </Grid>
      </Grid>
    </Stack>
  );
}

function SummaryRow({
  icon,
  label,
  value,
  capitalize = false,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  capitalize?: boolean;
}) {
  return (
    <Stack direction="row" spacing={1.25} alignItems="center" minWidth={0}>
      <Stack color="text.secondary" aria-hidden="true">
        {icon}
      </Stack>
      <Stack minWidth={0}>
        <Typography variant="caption" color="text.secondary">
          {label}
        </Typography>
        <Typography
          fontWeight={700}
          textTransform={capitalize ? "capitalize" : undefined}
          noWrap
        >
          {value}
        </Typography>
      </Stack>
    </Stack>
  );
}
