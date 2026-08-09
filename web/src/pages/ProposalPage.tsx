import ExpandMoreRoundedIcon from "@mui/icons-material/ExpandMoreRounded";
import FactCheckOutlinedIcon from "@mui/icons-material/FactCheckOutlined";
import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Alert,
  Breadcrumbs,
  Button,
  Link,
  Skeleton,
  Stack,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { Link as RouterLink, useParams } from "react-router-dom";
import { api } from "../api/client";
import { CopyValue } from "../components/CopyValue";
import { EmptyState } from "../components/EmptyState";
import { PageHeader } from "../components/PageHeader";
import { SectionCard } from "../components/SectionCard";
import { ProviderBadge, StatusBadge } from "../components/StatusBadge";

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
      <Stack spacing={3} maxWidth={980} mx="auto">
        <Skeleton variant="text" width="55%" height={24} />
        <Skeleton variant="text" width="70%" height={58} />
        <Skeleton variant="rounded" height={130} />
        <Skeleton variant="rounded" height={260} />
      </Stack>
    );
  }
  if (query.isError || !query.data) {
    return (
      <Stack spacing={2} maxWidth={980} mx="auto">
        <Alert severity="error">This proposal could not be found.</Alert>
        <Button
          component={RouterLink}
          to="/operations"
          startIcon={<ArrowBackRoundedIcon />}
        >
          Return to operations
        </Button>
      </Stack>
    );
  }

  const proposal = query.data;
  const stateLabel =
    proposal.state === "ready_for_review" ? "Ready for review" : proposal.state;

  return (
    <Stack spacing={3} maxWidth={980} mx="auto">
      <Breadcrumbs aria-label="Breadcrumb">
        <Link component={RouterLink} to="/operations" underline="hover">
          Operations
        </Link>
        <Link
          component={RouterLink}
          to={`/requests/${proposal.request_id}`}
          underline="hover"
        >
          Request
        </Link>
        <Typography color="text.primary">Proposal evidence</Typography>
      </Breadcrumbs>

      <PageHeader
        eyebrow="Deployment proposal"
        title="Deployment proposal"
        description="Inspect the immutable bundle generated from the accepted environment request."
        action={
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            <StatusBadge status={proposal.state} label={stateLabel} />
            <ProviderBadge provider={proposal.provider} />
            <StatusBadge
              status={proposal.mode}
              label={proposal.mode}
              variant="outlined"
            />
          </Stack>
        }
      />
      <Typography
        variant="body2"
        color="text.secondary"
        sx={{
          fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
          overflowWrap: "anywhere",
        }}
      >
        {proposal.proposal_id}
      </Typography>

      <Alert severity="warning" role="note" icon={<FactCheckOutlinedIcon />}>
        <Typography fontWeight={800} gutterBottom>
          Review-only boundary
        </Typography>
        <Typography variant="body2">
          This portal creates a deterministic proposal bundle for review. It has
          no cloud credentials, makes no cloud changes, and does not run direct
          plan, apply, destroy, or rollback actions.
        </Typography>
      </Alert>

      <SectionCard
        title="Proposal metadata"
        description="Use these identifiers to correlate the proposal with the request and protected external review."
      >
        <Stack spacing={1.5} sx={{ minWidth: 0, maxWidth: "100%" }}>
          <CopyValue value={proposal.proposal_id} label="Proposal ID" compact />
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
          <Stack
            direction={{ xs: "column", sm: "row" }}
            spacing={{ xs: 1, sm: 4 }}
            flexWrap="wrap"
            useFlexGap
            sx={{ minWidth: 0 }}
          >
            <Typography
              variant="body2"
              sx={{ minWidth: 0, overflowWrap: "anywhere" }}
            >
              <Typography
                component="span"
                variant="body2"
                color="text.secondary"
              >
                Request:{" "}
              </Typography>
              <Link
                component={RouterLink}
                to={`/requests/${proposal.request_id}`}
              >
                {proposal.request_id}
              </Link>
            </Typography>
            <Typography
              variant="body2"
              sx={{ minWidth: 0, overflowWrap: "anywhere" }}
            >
              <Typography
                component="span"
                variant="body2"
                color="text.secondary"
              >
                Installation:{" "}
              </Typography>
              {proposal.installation_id}
            </Typography>
            <Typography
              variant="body2"
              sx={{ minWidth: 0, overflowWrap: "anywhere" }}
            >
              <Typography
                component="span"
                variant="body2"
                color="text.secondary"
              >
                Schema:{" "}
              </Typography>
              {proposal.schema_version}
            </Typography>
          </Stack>
        </Stack>
      </SectionCard>

      <SectionCard
        title="Deterministic artifacts"
        description="Expand an artifact to inspect its generated content. The artifact content is shown exactly as returned by the API, with a length-limited preview for readability."
      >
        {proposal.artifacts.length === 0 ? (
          <EmptyState
            icon={<FactCheckOutlinedIcon />}
            title="No artifacts are available"
            description="The proposal was returned without an artifact bundle. Review the API response before continuing."
          />
        ) : (
          <Stack spacing={1.5}>
            {proposal.artifacts.map((artifact, index) => (
              <Accordion
                key={artifact.relative_path}
                defaultExpanded={index === 0}
                disableGutters
              >
                <AccordionSummary
                  expandIcon={<ExpandMoreRoundedIcon />}
                  aria-controls={`${artifact.relative_path}-content`}
                  id={`${artifact.relative_path}-header`}
                  sx={{ px: 2 }}
                >
                  <Typography
                    component="span"
                    fontWeight={700}
                    sx={{ overflowWrap: "anywhere", pr: 1 }}
                  >
                    {artifact.relative_path}
                  </Typography>
                </AccordionSummary>
                <AccordionDetails
                  id={`${artifact.relative_path}-content`}
                  sx={{ pt: 0, px: 2 }}
                >
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ mb: 1 }}
                  >
                    Content preview
                  </Typography>
                  <Typography
                    component="pre"
                    aria-label={`${artifact.relative_path} content preview`}
                    sx={{
                      bgcolor: "grey.100",
                      borderRadius: 1,
                      fontFamily:
                        "ui-monospace, SFMono-Regular, Menlo, monospace",
                      fontSize: 13,
                      maxHeight: 220,
                      overflow: "auto",
                      p: 1.5,
                      whiteSpace: "pre-wrap",
                      overflowWrap: "anywhere",
                      m: 0,
                    }}
                  >
                    {preview(artifact.content)}
                  </Typography>
                </AccordionDetails>
              </Accordion>
            ))}
          </Stack>
        )}
      </SectionCard>

      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        gap={1}
      >
        <Button
          component={RouterLink}
          to={`/requests/${proposal.request_id}`}
          variant="outlined"
          startIcon={<ArrowBackRoundedIcon />}
        >
          Back to request
        </Button>
        <Button component={RouterLink} to="/operations" variant="text">
          View operations
        </Button>
      </Stack>
    </Stack>
  );
}
