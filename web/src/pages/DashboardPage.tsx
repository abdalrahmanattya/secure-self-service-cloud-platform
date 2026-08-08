import {
  Alert,
  Button,
  Card,
  CardContent,
  Chip,
  Grid,
  Stack,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { Link as RouterLink } from "react-router-dom";
import { api } from "../api/client";

export function DashboardPage() {
  const installation = useQuery({
    queryKey: ["installation"],
    queryFn: api.installation,
  });
  const requests = useQuery({ queryKey: ["requests"], queryFn: api.requests });
  if (installation.isError)
    return (
      <Stack spacing={2} alignItems="flex-start">
        <Alert severity="info">
          Set up an installation to start requesting environments.
        </Alert>
        <Button component={RouterLink} to="/setup" variant="contained">
          Set up installation
        </Button>
      </Stack>
    );
  const profile = installation.data;
  return (
    <Stack spacing={3}>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        gap={2}
      >
        <div>
          <Typography variant="h1" fontSize={{ xs: 30, md: 42 }}>
            Environment dashboard
          </Typography>
          <Typography color="text.secondary">
            A clear view of safe, simulated environments.
          </Typography>
        </div>
        <Button component={RouterLink} to="/requests/new" variant="contained">
          New environment request
        </Button>
      </Stack>
      {profile && (
        <Card>
          <CardContent>
            <Stack
              direction={{ xs: "column", sm: "row" }}
              spacing={2}
              alignItems={{ sm: "center" }}
            >
              <div>
                <Typography variant="overline">Installation</Typography>
                <Typography variant="h2" fontSize={24}>
                  {profile.installation_id}
                </Typography>
              </div>
              <Chip
                label={`${profile.provider?.toUpperCase()} · ${profile.mode}`}
                color="primary"
              />
              <Chip label={profile.status} variant="outlined" />
            </Stack>
          </CardContent>
        </Card>
      )}
      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary">Requests</Typography>
              <Typography variant="h2">
                {requests.data?.requests.length ?? 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary">
                Accepted simulations
              </Typography>
              <Typography variant="h2">
                {requests.data?.requests.filter(
                  (item) => item.state === "accepted",
                ).length ?? 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary">Cloud changes</Typography>
              <Typography variant="h2">0</Typography>
              <Typography color="text.secondary">Simulation only</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      <Card component="section" aria-labelledby="recent-heading">
        <CardContent>
          <Typography
            id="recent-heading"
            variant="h2"
            fontSize={24}
            gutterBottom
          >
            Recent requests
          </Typography>
          <Stack spacing={1}>
            {(requests.data?.requests ?? []).map((item) => (
              <Button
                key={item.request.request_id}
                component={RouterLink}
                to={`/requests/${item.request.request_id}`}
                sx={{ justifyContent: "space-between", textTransform: "none" }}
              >
                {item.request.application}{" "}
                <Chip label={item.state} size="small" />
              </Button>
            ))}
            {requests.data?.requests.length === 0 && (
              <Typography color="text.secondary">No requests yet.</Typography>
            )}
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
}
