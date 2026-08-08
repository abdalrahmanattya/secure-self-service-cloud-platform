import { useEffect, useRef } from "react";
import { useForm } from "react-hook-form";
import {
  Alert,
  Button,
  Card,
  CardContent,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api, type EnvironmentRequestInput } from "../api/client";

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
  non_production_expiry: "2026-08-20",
};

export function NewRequestPage() {
  const navigate = useNavigate();
  const installation = useQuery({
    queryKey: ["installation"],
    queryFn: api.installation,
  });
  const form = useForm<EnvironmentRequestInput>({ defaultValues: defaults });
  const idempotencyKey = useRef(crypto.randomUUID());

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
    <Stack spacing={3} maxWidth={800} mx="auto">
      <div>
        <Typography variant="h1" fontSize={{ xs: 30, md: 42 }}>
          New environment
        </Typography>
        <Typography color="text.secondary">
          Tell us what you need. The platform selects the configured provider
          automatically.
        </Typography>
      </div>
      <Card component="form" onSubmit={form.handleSubmit(submit)}>
        <CardContent>
          <Stack spacing={2}>
            <Alert severity="info" role="status">
              Provider:{" "}
              {installation.data?.provider?.toUpperCase() ??
                "installation setup required"}
              . Provider cannot be changed per request.
            </Alert>
            <TextField
              label="Application"
              {...form.register("application", {
                required: "Application is required",
              })}
              error={Boolean(fieldError("application"))}
              helperText={fieldError("application") ?? "A short service name"}
            />
            <TextField
              label="Owner"
              {...form.register("owner", { required: "Owner is required" })}
              error={Boolean(fieldError("owner"))}
              helperText={fieldError("owner")}
            />
            <TextField
              label="Cost centre"
              {...form.register("cost_centre", {
                required: "Cost centre is required",
              })}
              error={Boolean(fieldError("cost_centre"))}
              helperText={fieldError("cost_centre")}
            />
            <TextField
              select
              label="Environment"
              defaultValue={defaults.environment}
              {...form.register("environment")}
            >
              <MenuItem value="development">Development</MenuItem>
              <MenuItem value="test">Test</MenuItem>
              <MenuItem value="production">Production</MenuItem>
            </TextField>
            <TextField
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
            <TextField
              label="Region"
              {...form.register("region", { required: "Region is required" })}
              error={Boolean(fieldError("region"))}
              helperText={
                fieldError("region") ??
                "Use a region enabled by the installation"
              }
            />
            <TextField
              label="Private network CIDR"
              {...form.register("network_cidr", {
                required: "Network CIDR is required",
              })}
              error={Boolean(fieldError("network_cidr"))}
              helperText={fieldError("network_cidr")}
            />
            <TextField
              select
              label="Cluster size"
              defaultValue={defaults.cluster_size}
              {...form.register("cluster_size")}
            >
              <MenuItem value="small">Small</MenuItem>
              <MenuItem value="medium">Medium</MenuItem>
              <MenuItem value="large">Large</MenuItem>
            </TextField>
            <TextField
              label="Monthly budget"
              type="number"
              slotProps={{ htmlInput: { min: 1, step: "0.01" } }}
              {...form.register("monthly_budget", {
                required: "Budget is required",
              })}
              error={Boolean(fieldError("monthly_budget"))}
              helperText={fieldError("monthly_budget")}
            />
            <TextField
              label="Expiry for non-production"
              type="date"
              slotProps={{ inputLabel: { shrink: true } }}
              {...form.register("non_production_expiry")}
            />
            <TextField
              label="Why is this environment needed?"
              multiline
              minRows={3}
              {...form.register("business_justification", {
                required: "A business justification is required",
              })}
              error={Boolean(fieldError("business_justification"))}
              helperText={fieldError("business_justification")}
            />
            <Button
              type="submit"
              variant="contained"
              disabled={mutation.isPending}
            >
              Review request
            </Button>
            {mutation.isError && (
              <Alert severity="error" role="alert">
                The request could not be submitted. Try again with the same
                request key or correct the input.
              </Alert>
            )}
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
}
