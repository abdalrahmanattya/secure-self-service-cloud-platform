import { Alert, Card, CardContent, Stack, Typography } from "@mui/material";
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
              <Alert severity="info">
                This build performs simulation only. No infrastructure is
                applied.
              </Alert>
            </Stack>
          ) : (
            <Alert severity="warning">No installation has been created.</Alert>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardContent>
          <Typography variant="h2" fontSize={24} gutterBottom>
            Provider simulations
          </Typography>
          <Stack spacing={1}>
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
