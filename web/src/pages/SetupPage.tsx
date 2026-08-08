import { useState } from "react";
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
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api, apiErrorFields, apiErrorMessage } from "../api/client";
import type { InstallationMode, Provider } from "../api/client";

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
  const mutation = useMutation({
    mutationFn: () => api.createInstallation(provider, mode),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["installation"] });
      navigate("/");
    },
  });
  return (
    <Stack spacing={3} maxWidth={720} mx="auto">
      <div>
        <Typography variant="h1" fontSize={{ xs: 30, md: 42 }}>
          Choose your platform
        </Typography>
        <Typography color="text.secondary" sx={{ mt: 1 }}>
          Select one provider for this installation. Request evaluation and
          proposal generation are local and credential-free.
        </Typography>
      </div>
      <Card component="section" aria-labelledby="setup-heading">
        <CardContent>
          <Typography
            id="setup-heading"
            variant="h2"
            fontSize={24}
            gutterBottom
          >
            Installation setup
          </Typography>
          <Stack spacing={2}>
            <TextField
              select
              label="Provider"
              value={provider}
              onChange={(event) => setProvider(event.target.value as Provider)}
              helperText="Provider is locked after setup."
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
            <TextField
              select
              label="Mode"
              value={mode}
              onChange={(event) =>
                setMode(event.target.value as InstallationMode)
              }
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
            {mode !== "simulation" && (
              <Alert severity="warning" role="status">
                {mode} generates deterministic proposals locally without
                credentials. Cloud execution requires a protected external
                workflow and is not available from this portal.
              </Alert>
            )}
            <Button
              variant="contained"
              onClick={() => mutation.mutate()}
              disabled={mutation.isPending}
            >
              Create installation
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
        </CardContent>
      </Card>
    </Stack>
  );
}
