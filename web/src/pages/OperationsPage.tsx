import AssignmentTurnedInOutlinedIcon from "@mui/icons-material/AssignmentTurnedInOutlined";
import FingerprintOutlinedIcon from "@mui/icons-material/FingerprintOutlined";
import LockOutlinedIcon from "@mui/icons-material/LockOutlined";
import OpenInNewOutlinedIcon from "@mui/icons-material/OpenInNewOutlined";
import { Alert, Button, Stack, Typography } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { Link as RouterLink } from "react-router-dom";
import { api } from "../api/client";
import { CopyValue } from "../components/CopyValue";
import { EmptyState } from "../components/EmptyState";
import {
  LifecycleStatus,
  type LifecycleStage,
} from "../components/LifecycleStatus";
import { MetricCard } from "../components/MetricCard";
import { PageHeader } from "../components/PageHeader";
import { ProviderBadge, StatusBadge } from "../components/StatusBadge";
import { SectionCard } from "../components/SectionCard";

const guardedStages = [
  [
    "GitHub review",
    "Guarded prerequisite; not executed here, and no pull request is created by this portal.",
  ],
  [
    "Protected plan",
    "Guarded prerequisite; not executed here, and no plan is run by this portal.",
  ],
  [
    "Approval",
    "Guarded prerequisite; not executed here, and protected environment approval is external.",
  ],
  [
    "Apply",
    "Guarded prerequisite; not executed here, and no direct apply control exists here.",
  ],
  [
    "Drift / rollback / destroy",
    "Separate guarded operational workflows; not executed here.",
  ],
] as const;

export function OperationsPage() {
  const query = useQuery({
    queryKey: ["proposals"],
    queryFn: api.proposals,
  });
  const proposals = query.data?.proposals ?? [];
  const hasReadyProposal = proposals.some(
    (proposal) => proposal.state === "ready_for_review",
  );
  const stages: LifecycleStage[] = [
    {
      name: "Proposal ready",
      description: "Deterministic artifacts are available for review.",
      status: hasReadyProposal ? "ready" : "not_executed",
    },
    ...guardedStages.map(([name, description]) => ({
      name,
      description,
      status: "guarded" as const,
    })),
  ];

  return (
    <Stack spacing={3}>
      <PageHeader
        eyebrow="Protected delivery lifecycle"
        title="Operations"
        description="Follow proposal evidence and the guarded deployment lifecycle without implying that external cloud stages have run."
        action={
          <Button component={RouterLink} to="/requests/new" variant="contained">
            New environment request
          </Button>
        }
      />

      <Alert severity="info">
        Proposal state is held in process memory by this local API. Restarting
        the API clears the list; this page does not imply that any external
        review, plan, approval, apply, drift, rollback, or destroy stage ran.
      </Alert>

      <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
        <MetricCard
          label="Review proposals"
          value={query.isLoading ? "—" : proposals.length}
          description="Immutable proposal bundles in this API process"
          icon={<AssignmentTurnedInOutlinedIcon />}
          accent="primary"
        />
        <MetricCard
          label="Ready for review"
          value={
            query.isLoading
              ? "—"
              : proposals.filter((item) => item.state === "ready_for_review")
                  .length
          }
          description="The only lifecycle state this service can claim"
          icon={<FingerprintOutlinedIcon />}
          accent="success"
        />
        <MetricCard
          label="External stages"
          value={guardedStages.length}
          description="Guarded and not executed by the portal"
          icon={<LockOutlinedIcon />}
          accent="warning"
        />
      </Stack>

      <SectionCard
        title="Guarded lifecycle"
        description="A proposal becomes review evidence; deployment remains a separate protected workflow."
      >
        <LifecycleStatus stages={stages} />
      </SectionCard>

      <SectionCard
        title="Proposal evidence"
        description="Review the immutable metadata and content hash before an administrator takes action in the protected delivery repository."
      >
        {query.isLoading ? (
          <Stack spacing={1.5} aria-label="Loading proposals">
            <Stack
              sx={{ height: 92, bgcolor: "action.hover", borderRadius: 2 }}
            />
            <Stack
              sx={{ height: 92, bgcolor: "action.hover", borderRadius: 2 }}
            />
          </Stack>
        ) : query.isError ? (
          <Alert severity="error">
            Proposals are temporarily unavailable. Check that the local API is
            running and try again.
          </Alert>
        ) : proposals.length === 0 ? (
          <EmptyState
            title="No proposals are stored in this API process yet."
            description="Submit and accept an environment request, then generate a proposal to create review evidence."
            icon={<AssignmentTurnedInOutlinedIcon />}
            action={
              <Button component={RouterLink} to="/" variant="outlined">
                View dashboard
              </Button>
            }
          />
        ) : (
          <Stack spacing={1.5}>
            {proposals.map((proposal) => (
              <Stack
                key={proposal.proposal_id}
                spacing={1.5}
                sx={{
                  p: { xs: 1.5, sm: 2 },
                  border: 1,
                  borderColor: "divider",
                  borderRadius: 2,
                  bgcolor: "background.default",
                }}
              >
                <Stack
                  direction={{ xs: "column", md: "row" }}
                  spacing={1.5}
                  justifyContent="space-between"
                  alignItems={{ md: "center" }}
                >
                  <Stack spacing={0.45} minWidth={0}>
                    <Stack
                      direction="row"
                      spacing={1}
                      alignItems="center"
                      flexWrap="wrap"
                    >
                      <Typography fontWeight={750}>
                        {proposal.proposal_id}
                      </Typography>
                      <StatusBadge
                        status={proposal.state}
                        label="Ready for review"
                      />
                    </Stack>
                    <Typography variant="body2" color="text.secondary">
                      Request {proposal.request_id} · installation{" "}
                      {proposal.installation_id}
                    </Typography>
                  </Stack>
                  <Stack
                    direction="row"
                    spacing={1}
                    alignItems="center"
                    flexWrap="wrap"
                  >
                    <ProviderBadge provider={proposal.provider} />
                    <StatusBadge
                      status={proposal.mode}
                      label={proposal.mode}
                      variant="outlined"
                    />
                    <Button
                      component={RouterLink}
                      to={`/proposals/${proposal.proposal_id}`}
                      variant="outlined"
                      size="small"
                      endIcon={<OpenInNewOutlinedIcon />}
                      aria-label={`Open evidence for ${proposal.proposal_id}`}
                    >
                      Open evidence
                    </Button>
                  </Stack>
                </Stack>
                <Stack
                  direction={{ xs: "column", md: "row" }}
                  spacing={{ xs: 0.5, md: 3 }}
                  flexWrap="wrap"
                  useFlexGap
                  sx={{ minWidth: 0, maxWidth: "100%" }}
                >
                  <CopyValue
                    value={proposal.content_hash}
                    label="Content hash"
                    compact
                  />
                  <CopyValue
                    value={proposal.request_fingerprint}
                    label="Request fingerprint"
                    compact
                  />
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ minWidth: 0, overflowWrap: "anywhere" }}
                  >
                    {proposal.artifacts.length} artifacts ·{" "}
                    {proposal.schema_version}
                  </Typography>
                </Stack>
              </Stack>
            ))}
          </Stack>
        )}
      </SectionCard>
    </Stack>
  );
}
