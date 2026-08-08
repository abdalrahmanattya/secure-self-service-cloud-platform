import {
  Alert,
  Breadcrumbs,
  Card,
  CardContent,
  Chip,
  Link,
  Skeleton,
  Stack,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { Link as RouterLink, useParams } from "react-router-dom";
import { api } from "../api/client";

function preview(content: string): string {
  const limit = 420;
  return content.length > limit ? `${content.slice(0, limit)}\n…` : content;
}

export function ProposalPage() {
  const { proposalId = "" } = useParams();
  const query = useQuery({
    queryKey: ["proposal", proposalId],
    queryFn: () => api.proposal(proposalId),
  });

  if (query.isLoading) {
    return (
      <Stack spacing={2} maxWidth={900} mx="auto">
        <Skeleton variant="text" width="55%" height={60} />
        <Skeleton variant="rounded" height={150} />
        <Skeleton variant="rounded" height={240} />
      </Stack>
    );
  }
  if (query.isError || !query.data) {
    return (
      <Stack spacing={2} maxWidth={900} mx="auto">
        <Alert severity="error">This proposal could not be found.</Alert>
        <Link component={RouterLink} to="/operations">
          Return to operations
        </Link>
      </Stack>
    );
  }

  const proposal = query.data;
  const stateLabel =
    proposal.state === "ready_for_review" ? "Ready for review" : proposal.state;
  return (
    <Stack spacing={3} maxWidth={900} mx="auto">
      <Breadcrumbs aria-label="Breadcrumb">
        <Link component={RouterLink} to="/operations" underline="hover">
          Operations
        </Link>
        <Typography color="text.primary">Proposal</Typography>
      </Breadcrumbs>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        gap={2}
      >
        <div>
          <Typography variant="h1" fontSize={{ xs: 30, md: 42 }}>
            Deployment proposal
          </Typography>
          <Typography color="text.secondary" sx={{ overflowWrap: "anywhere" }}>
            {proposal.proposal_id}
          </Typography>
        </div>
        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
          <Chip label={stateLabel} color="success" />
          <Chip label={proposal.provider.toUpperCase()} color="primary" />
          <Chip label={proposal.mode} variant="outlined" />
        </Stack>
      </Stack>

      <Alert severity="warning" role="note">
        <strong>Review-only boundary.</strong> This portal creates a
        deterministic proposal bundle for review. It has no cloud credentials,
        makes no cloud changes, and does not run direct plan, apply, destroy, or
        rollback actions.
      </Alert>

      <Card>
        <CardContent>
          <Typography variant="h2" fontSize={24} gutterBottom>
            Proposal evidence
          </Typography>
          <Stack spacing={1}>
            <Typography sx={{ overflowWrap: "anywhere" }}>
              <strong>Proposal ID:</strong> {proposal.proposal_id}
            </Typography>
            <Typography>
              <strong>State:</strong> {stateLabel}
            </Typography>
            <Typography>
              <strong>Provider / mode:</strong>{" "}
              {proposal.provider.toUpperCase()} / {proposal.mode}
            </Typography>
            <Typography>
              <strong>Request:</strong>{" "}
              <Link
                component={RouterLink}
                to={`/requests/${proposal.request_id}`}
              >
                {proposal.request_id}
              </Link>
            </Typography>
            <Typography sx={{ overflowWrap: "anywhere" }}>
              <strong>Content hash:</strong>{" "}
              <code>{proposal.content_hash}</code>
            </Typography>
            <Typography>
              <strong>Schema:</strong> {proposal.schema_version}
            </Typography>
          </Stack>
        </CardContent>
      </Card>

      <Card component="section" aria-labelledby="artifacts-heading">
        <CardContent>
          <Typography
            id="artifacts-heading"
            variant="h2"
            fontSize={24}
            gutterBottom
          >
            Deterministic artifacts
          </Typography>
          <Typography color="text.secondary" sx={{ mb: 2 }}>
            These paths and previews are generated from the accepted request,
            installation, and deterministic evaluation. They contain no
            credentials, timestamps, or cloud identifiers.
          </Typography>
          <Stack spacing={2}>
            {proposal.artifacts.map((artifact) => (
              <Card key={artifact.relative_path} variant="outlined">
                <CardContent>
                  <Typography
                    component="h3"
                    fontWeight={700}
                    sx={{ overflowWrap: "anywhere" }}
                  >
                    {artifact.relative_path}
                  </Typography>
                  <Typography
                    component="div"
                    color="text.secondary"
                    sx={{ mt: 1 }}
                  >
                    Content preview
                  </Typography>
                  <BoxPreview
                    content={preview(artifact.content)}
                    path={artifact.relative_path}
                  />
                </CardContent>
              </Card>
            ))}
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
}

function BoxPreview({ content, path }: { content: string; path: string }) {
  return (
    <Typography
      component="pre"
      aria-label={`${path} content preview`}
      sx={{
        bgcolor: "grey.100",
        borderRadius: 1,
        fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
        fontSize: 13,
        maxHeight: 220,
        overflow: "auto",
        p: 1.5,
        whiteSpace: "pre-wrap",
        overflowWrap: "anywhere",
      }}
    >
      {content}
    </Typography>
  );
}
