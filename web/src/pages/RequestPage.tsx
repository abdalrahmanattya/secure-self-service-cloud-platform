import {
  Alert,
  Button,
  Card,
  CardContent,
  Chip,
  Stack,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { Link as RouterLink, useParams } from "react-router-dom";
import { api } from "../api/client";
import { PolicyErrors } from "../components/PolicyErrors";

export function RequestPage() {
  const { requestId = "" } = useParams();
  const query = useQuery({
    queryKey: ["request", requestId],
    queryFn: () => api.request(requestId),
  });
  if (query.isLoading) return <Typography>Loading request…</Typography>;
  if (query.isError || !query.data)
    return <Alert severity="error">Request not found.</Alert>;
  const record = query.data;
  const { request, outcome } = record;
  return (
    <Stack spacing={3} maxWidth={800} mx="auto">
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        gap={2}
      >
        <div>
          <Typography variant="h1" fontSize={{ xs: 30, md: 42 }}>
            {request.application}
          </Typography>
          <Typography color="text.secondary">
            Request review and result
          </Typography>
        </div>
        <Chip
          label={record.state}
          color={record.state === "accepted" ? "success" : "error"}
        />
      </Stack>
      <Card>
        <CardContent>
          <Typography variant="h2" fontSize={24} gutterBottom>
            Decision
          </Typography>
          <PolicyErrors violations={outcome.decision.violations} />
          {outcome.decision.allowed ? (
            <Alert severity="success">
              This environment is ready as a deterministic simulation.
            </Alert>
          ) : (
            <Alert severity="error">
              This request is blocked until the policy issues are resolved.
            </Alert>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardContent>
          <Typography variant="h2" fontSize={24} gutterBottom>
            Configuration
          </Typography>
          <Stack spacing={1}>
            {[
              ["Provider", request.provider.toUpperCase()],
              ["Environment", request.environment],
              ["Region", request.region],
              ["Network", request.network_cidr],
              ["Cluster", request.cluster_size],
              ["Request ID", request.request_id],
            ].map(([label, value]) => (
              <Typography key={label}>
                <strong>{label}:</strong> {value}
              </Typography>
            ))}
          </Stack>
        </CardContent>
      </Card>
      {outcome.result && (
        <Card>
          <CardContent>
            <Typography variant="h2" fontSize={24} gutterBottom>
              Simulated resources
            </Typography>
            <Stack spacing={1}>
              {outcome.result.resources.map((resource) => (
                <Typography key={`${resource.kind}-${resource.name}`}>
                  {resource.kind}: {resource.name}
                </Typography>
              ))}
            </Stack>
          </CardContent>
        </Card>
      )}
      <Button component={RouterLink} to="/" variant="outlined">
        Back to dashboard
      </Button>
    </Stack>
  );
}
