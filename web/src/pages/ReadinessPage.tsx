import {
  Alert,
  Card,
  CardContent,
  CircularProgress,
  Stack,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";

export function ReadinessPage() {
  const installation = useQuery({
    queryKey: ["installation"],
    queryFn: api.installation,
  });
  const providers = useQuery({
    queryKey: ["providers"],
    queryFn: api.providers,
  });
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h1" fontSize={{ xs: 30, md: 42 }}>
          Platform readiness
        </Typography>
        <Typography color="text.secondary">
          Understand what is available before you request an environment.
        </Typography>
      </div>
      <Card>
        <CardContent>
          <Typography variant="h2" fontSize={24} gutterBottom>
            Current installation
          </Typography>
          {installation.data ? (
            <Stack spacing={1}>
              <Typography>
                <strong>Provider:</strong>{" "}
                {installation.data.provider?.toUpperCase()}
              </Typography>
              <Typography>
                <strong>Mode:</strong> {installation.data.mode}
              </Typography>
              <Typography>
                <strong>Status:</strong> {installation.data.status}
              </Typography>
              <Stack spacing={1}>
                <Alert severity="success">
                  Available now: credential-free request evaluation and
                  deterministic proposal generation from accepted requests.
                </Alert>
                <Alert severity="warning">
                  Guarded prerequisites: GitHub review, protected plan,
                  approval, apply, drift, rollback, and destroy require an
                  explicitly configured protected workflow. They are not enabled
                  or executed by this portal.
                </Alert>
              </Stack>
            </Stack>
          ) : installation.isLoading ? (
            <Stack direction="row" spacing={1} alignItems="center">
              <CircularProgress size={20} aria-label="Loading installation" />
              <Typography>Loading installation readiness…</Typography>
            </Stack>
          ) : (
            <Alert severity="warning">No installation has been created.</Alert>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardContent>
          <Typography variant="h2" fontSize={24} gutterBottom>
            Provider options
          </Typography>
          <Stack spacing={1}>
            {providers.isLoading && <Typography>Loading providers…</Typography>}
            {!providers.isLoading &&
              !providers.isError &&
              (providers.data?.providers ?? []).length === 0 && (
                <Typography color="text.secondary">
                  No provider options are available.
                </Typography>
              )}
            {providers.isError && (
              <Alert severity="error">
                Provider options could not be loaded from the local API.
              </Alert>
            )}
            {(providers.data?.providers ?? []).map((item) => (
              <Typography key={item.provider}>
                {item.display_name}:{" "}
                {item.available ? "available" : "unavailable"}
              </Typography>
            ))}
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
}
