import {
  Alert,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  Skeleton,
  Stack,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { Link as RouterLink } from "react-router-dom";
import { api } from "../api/client";

const stages = [
  ["Proposal ready", "Deterministic artifacts are available for review."],
  ["GitHub review", "Guarded prerequisite; no pull request is created here."],
  ["Protected plan", "Guarded prerequisite; no plan is run by this portal."],
  [
    "Approval",
    "Guarded prerequisite; protected environment approval is external.",
  ],
  ["Apply", "Guarded prerequisite; no direct apply control exists here."],
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
  const hasReadyProposal =
    query.data?.proposals.some(
      (proposal) => proposal.state === "ready_for_review",
    ) ?? false;

  return (
    <Stack spacing={3}>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        gap={2}
      >
        <div>
          <Typography variant="h1" fontSize={{ xs: 30, md: 42 }}>
            Operations
          </Typography>
          <Typography color="text.secondary">
            Follow proposal evidence and the guarded deployment lifecycle.
          </Typography>
        </div>
        <Button component={RouterLink} to="/requests/new" variant="contained">
          New environment request
        </Button>
      </Stack>

      <Alert severity="info">
        Proposal state is held in process memory by this local API. Restarting
        the API clears the list; this page does not imply that any external
        review, plan, approval, apply, drift, rollback, or destroy stage ran.
      </Alert>

      <Card component="section" aria-labelledby="lifecycle-heading">
        <CardContent>
          <Typography
            id="lifecycle-heading"
            variant="h2"
            fontSize={24}
            gutterBottom
          >
            Guarded lifecycle
          </Typography>
          <Stack divider={<Divider flexItem />}>
            {stages.map(([name, description], index) => (
              <Stack
                key={name}
                direction={{ xs: "column", sm: "row" }}
                spacing={1.5}
                alignItems={{ sm: "center" }}
                sx={{ py: 1.5 }}
              >
                <Chip
                  label={
                    index === 0 && hasReadyProposal
                      ? "Ready for review"
                      : "Not executed"
                  }
                  color={
                    index === 0 && hasReadyProposal ? "success" : "default"
                  }
                  size="small"
                />
                <div>
                  <Typography fontWeight={700}>{name}</Typography>
                  <Typography color="text.secondary">{description}</Typography>
                </div>
              </Stack>
            ))}
          </Stack>
        </CardContent>
      </Card>

      <Card component="section" aria-labelledby="proposals-heading">
        <CardContent>
          <Typography
            id="proposals-heading"
            variant="h2"
            fontSize={24}
            gutterBottom
          >
            Proposals
          </Typography>
          {query.isLoading && (
            <Stack spacing={1}>
              <Skeleton variant="rounded" height={64} />
              <Skeleton variant="rounded" height={64} />
            </Stack>
          )}
          {query.isError && (
            <Alert severity="error">
              Proposals are temporarily unavailable. Check that the local API is
              running and try again.
            </Alert>
          )}
          {!query.isLoading &&
            !query.isError &&
            query.data?.proposals.length === 0 && (
              <Stack spacing={1} alignItems="flex-start">
                <Typography color="text.secondary">
                  No proposals are stored in this API process yet.
                </Typography>
                <Button component={RouterLink} to="/" variant="outlined">
                  View dashboard
                </Button>
              </Stack>
            )}
          {!query.isLoading &&
            !query.isError &&
            (query.data?.proposals.length ?? 0) > 0 && (
              <Stack spacing={1}>
                {query.data?.proposals.map((proposal) => (
                  <Button
                    key={proposal.proposal_id}
                    component={RouterLink}
                    to={`/proposals/${proposal.proposal_id}`}
                    variant="outlined"
                    sx={{
                      justifyContent: "space-between",
                      textTransform: "none",
                      textAlign: "left",
                    }}
                  >
                    <span>
                      <strong>{proposal.proposal_id}</strong>
                      <br />
                      {proposal.request_id} · {proposal.provider.toUpperCase()}{" "}
                      · {proposal.mode}
                    </span>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Chip
                        label={
                          proposal.state === "ready_for_review"
                            ? "Ready for review"
                            : proposal.state
                        }
                        color="success"
                        size="small"
                      />
                      <Chip
                        label={proposal.content_hash.slice(0, 12)}
                        size="small"
                        variant="outlined"
                      />
                    </Stack>
                  </Button>
                ))}
              </Stack>
            )}
        </CardContent>
      </Card>
    </Stack>
  );
}
