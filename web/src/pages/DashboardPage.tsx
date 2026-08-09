import ArrowForwardRoundedIcon from "@mui/icons-material/ArrowForwardRounded";
import CloudDoneOutlinedIcon from "@mui/icons-material/CloudDoneOutlined";
import DescriptionOutlinedIcon from "@mui/icons-material/DescriptionOutlined";
import FactCheckOutlinedIcon from "@mui/icons-material/FactCheckOutlined";
import LockOutlinedIcon from "@mui/icons-material/LockOutlined";
import PlaylistAddCheckOutlinedIcon from "@mui/icons-material/PlaylistAddCheckOutlined";
import RequestQuoteOutlinedIcon from "@mui/icons-material/RequestQuoteOutlined";
import {
  Alert,
  Button,
  Chip,
  Grid,
  Link,
  Skeleton,
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

export function DashboardPage() {
  const installation = useQuery({
    queryKey: ["installation"],
    queryFn: api.installation,
    retry: false,
  });
  const requests = useQuery({ queryKey: ["requests"], queryFn: api.requests });
  const proposals = useQuery({
    queryKey: ["proposals"],
    queryFn: api.proposals,
  });

  if (installation.isError) {
    return (
      <Stack spacing={2} maxWidth={640}>
        <PageHeader
          eyebrow="Workspace"
          title="Your control plane is not configured"
          description="Create an installation profile before requesting environments."
        />
        <Alert severity="info">
          Set up an installation to start requesting environments.
        </Alert>
        <Button component={RouterLink} to="/setup" variant="contained">
          Set up installation
        </Button>
      </Stack>
    );
  }

  if (installation.isPending) {
    return (
      <Stack spacing={3}>
        <PageHeader
          eyebrow="Platform overview"
          title="Environment dashboard"
          description="Loading the current installation and governance context."
        />
        <Skeleton variant="rounded" height={120} />
        <Grid container spacing={2}>
          {[1, 2, 3, 4].map((item) => (
            <Grid key={item} size={{ xs: 12, sm: 6, lg: 3 }}>
              <Skeleton variant="rounded" height={150} />
            </Grid>
          ))}
        </Grid>
      </Stack>
    );
  }

  const profile = installation.data;
  const requestItems = requests.data?.requests ?? [];
  const proposalItems = proposals.data?.proposals ?? [];
  const acceptedCount = requestItems.filter(
    (item) => item.state === "accepted",
  ).length;

  return (
    <Stack spacing={3}>
      <PageHeader
        eyebrow="Platform overview"
        title="Environment dashboard"
        description="A governed workspace for requesting environments, reviewing evidence, and handing approved changes to protected delivery workflows."
        action={
          <Button
            component={RouterLink}
            to="/requests/new"
            variant="contained"
            startIcon={<DescriptionOutlinedIcon />}
          >
            New environment request
          </Button>
        }
      />

      <SectionCard
        title="Installation context"
        description="This installation selects one provider and mode for every request."
        action={
          profile ? (
            <Stack direction="row" gap={1} flexWrap="wrap">
              <ProviderBadge provider={profile.provider} />
              <StatusBadge status={profile.status} />
            </Stack>
          ) : undefined
        }
      >
        {profile ? (
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 4 }}>
              <Typography variant="overline" color="text.secondary">
                Installation ID
              </Typography>
              <Typography fontWeight={750}>
                {profile.installation_id}
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <Typography variant="overline" color="text.secondary">
                Operating mode
              </Typography>
              <Typography fontWeight={750} textTransform="capitalize">
                {profile.mode}
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <Typography variant="overline" color="text.secondary">
                Cloud execution
              </Typography>
              <Typography fontWeight={750}>
                Protected external workflow
              </Typography>
            </Grid>
          </Grid>
        ) : (
          <Skeleton width="80%" />
        )}
      </SectionCard>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
          <MetricCard
            label="Requests"
            value={requests.isPending ? "—" : requestItems.length}
            description="Submitted to the policy gate"
            icon={<RequestQuoteOutlinedIcon fontSize="large" />}
            accent="primary"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
          <MetricCard
            label="Accepted requests"
            value={requests.isPending ? "—" : acceptedCount}
            description="Ready for proposal generation"
            icon={<PlaylistAddCheckOutlinedIcon fontSize="large" />}
            accent="success"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
          <MetricCard
            label="Review proposals"
            value={proposals.isPending ? "—" : proposalItems.length}
            description="Immutable evidence bundles"
            icon={<FactCheckOutlinedIcon fontSize="large" />}
            accent="info"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
          <MetricCard
            label="Cloud changes"
            value="0"
            description="No cloud changes executed"
            icon={<CloudDoneOutlinedIcon fontSize="large" />}
            accent="warning"
          />
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, lg: 7 }}>
          <SectionCard
            title="Recent activity"
            description="Requests and proposals held by this API process."
            action={
              <Button
                component={RouterLink}
                to="/operations"
                endIcon={<ArrowForwardRoundedIcon />}
              >
                Open operations
              </Button>
            }
          >
            {requestItems.length === 0 && proposalItems.length === 0 ? (
              <EmptyState
                icon={<DescriptionOutlinedIcon />}
                title="No activity yet"
                description="Submit an environment request to see its policy outcome and review path here."
                action={
                  <Button
                    component={RouterLink}
                    to="/requests/new"
                    variant="outlined"
                  >
                    Create your first request
                  </Button>
                }
              />
            ) : (
              <Stack spacing={1}>
                {requestItems.slice(0, 5).map((item) => (
                  <Button
                    key={item.request.request_id}
                    component={RouterLink}
                    to={`/requests/${item.request.request_id}`}
                    variant="text"
                    sx={{
                      justifyContent: "space-between",
                      textAlign: "left",
                      py: 1.25,
                    }}
                  >
                    <Stack minWidth={0} alignItems="flex-start">
                      <Typography fontWeight={750} noWrap maxWidth="100%">
                        {item.request.application}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" noWrap>
                        {item.request.environment} · {item.request.request_id}
                      </Typography>
                    </Stack>
                    <StatusBadge status={item.state} sx={{ flexShrink: 0 }} />
                  </Button>
                ))}
                {proposalItems.slice(0, 3).map((proposal) => (
                  <Button
                    key={proposal.proposal_id}
                    component={RouterLink}
                    to={`/proposals/${proposal.proposal_id}`}
                    variant="text"
                    sx={{
                      justifyContent: "space-between",
                      textAlign: "left",
                      py: 1.25,
                    }}
                  >
                    <Stack minWidth={0} alignItems="flex-start">
                      <Typography fontWeight={750} noWrap maxWidth="100%">
                        Review proposal {proposal.proposal_id}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" noWrap>
                        {proposal.provider.toUpperCase()} · {proposal.mode}
                      </Typography>
                    </Stack>
                    <StatusBadge
                      status={proposal.state}
                      sx={{ flexShrink: 0 }}
                    />
                  </Button>
                ))}
              </Stack>
            )}
          </SectionCard>
        </Grid>
        <Grid size={{ xs: 12, lg: 5 }}>
          <SectionCard
            title="Governance boundary"
            description="The portal prepares evidence; protected workflows control execution."
          >
            <Stack spacing={1.5}>
              <Alert
                severity="success"
                icon={<FactCheckOutlinedIcon />}
                role="status"
              >
                Policy evaluation and deterministic proposal generation are
                available locally.
              </Alert>
              <Stack direction="row" spacing={1.25} alignItems="flex-start">
                <LockOutlinedIcon color="disabled" />
                <Stack spacing={0.25}>
                  <Typography fontWeight={750}>
                    Cloud execution is guarded
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Review, plan, approval, apply, drift, rollback, and destroy
                    remain outside this portal.
                  </Typography>
                </Stack>
              </Stack>
              <Link component={RouterLink} to="/readiness" underline="hover">
                Review platform readiness{" "}
                <ArrowForwardRoundedIcon
                  sx={{ fontSize: 16, verticalAlign: "middle" }}
                />
              </Link>
            </Stack>
          </SectionCard>
        </Grid>
      </Grid>
    </Stack>
  );
}
