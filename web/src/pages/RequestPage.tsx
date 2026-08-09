import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";
import ArrowForwardRoundedIcon from "@mui/icons-material/ArrowForwardRounded";
import CheckCircleOutlineRoundedIcon from "@mui/icons-material/CheckCircleOutlineRounded";
import CloudQueueRoundedIcon from "@mui/icons-material/CloudQueueRounded";
import ErrorOutlineRoundedIcon from "@mui/icons-material/ErrorOutlineRounded";
import {
  Alert,
  Breadcrumbs,
  Button,
  Divider,
  Link,
  Skeleton,
  Stack,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef } from "react";
import { Link as RouterLink, useNavigate, useParams } from "react-router-dom";
import { api, apiErrorFields, apiErrorMessage } from "../api/client";
import { CopyValue } from "../components/CopyValue";
import { EmptyState } from "../components/EmptyState";
import { PageHeader } from "../components/PageHeader";
import { PolicyErrors } from "../components/PolicyErrors";
import { SectionCard } from "../components/SectionCard";
import { ProviderBadge, StatusBadge } from "../components/StatusBadge";

const requestFields = [
  ["Environment", "environment"],
  ["Owner", "owner"],
  ["Cost centre", "cost_centre"],
  ["Data classification", "data_classification"],
  ["Region", "region"],
  ["Network CIDR", "network_cidr"],
  ["Cluster size", "cluster_size"],
  ["Monthly budget", "monthly_budget"],
] as const;

export function RequestPage() {
  const { requestId = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const proposalIdempotencyKey = useRef(crypto.randomUUID());
  const query = useQuery({
    queryKey: ["request", requestId],
    queryFn: () => api.request(requestId),
  });
  const proposalMutation = useMutation({
    mutationFn: () =>
      api.createProposal(requestId, proposalIdempotencyKey.current),
    onSuccess: async (proposal) => {
      await queryClient.invalidateQueries({ queryKey: ["proposals"] });
      navigate(`/proposals/${proposal.proposal_id}`);
    },
  });

  if (query.isLoading) {
    return (
      <Stack spacing={3} maxWidth={980} mx="auto">
        <Skeleton variant="text" width="55%" height={24} />
        <Skeleton variant="text" width="70%" height={58} />
        <Skeleton variant="rounded" height={180} />
        <Skeleton variant="rounded" height={260} />
      </Stack>
    );
  }
  if (query.isError || !query.data) {
    return (
      <Stack spacing={2} maxWidth={980} mx="auto">
        <Alert severity="error">Request not found.</Alert>
        <Button
          component={RouterLink}
          to="/"
          startIcon={<ArrowBackRoundedIcon />}
        >
          Back to dashboard
        </Button>
      </Stack>
    );
  }

  const record = query.data;
  const { request, outcome } = record;
  const accepted = outcome.decision.allowed;
  const decisionStatus = accepted ? "accepted" : "denied";

  return (
    <Stack spacing={3} maxWidth={980} mx="auto">
      <Breadcrumbs aria-label="Breadcrumb">
        <Link component={RouterLink} to="/" underline="hover">
          Overview
        </Link>
        <Link component={RouterLink} to="/requests/new" underline="hover">
          New request
        </Link>
        <Typography color="text.primary">Request review</Typography>
      </Breadcrumbs>

      <PageHeader
        eyebrow="Environment request"
        title={request.application}
        description="Review the policy decision and the resources evaluated for this environment request."
        action={
          <StatusBadge
            status={decisionStatus}
            label={accepted ? "Accepted" : "Denied"}
          />
        }
      />

      <Alert
        severity={accepted ? "success" : "error"}
        icon={
          accepted ? (
            <CheckCircleOutlineRoundedIcon />
          ) : (
            <ErrorOutlineRoundedIcon />
          )
        }
        sx={{ alignItems: "flex-start" }}
      >
        <Typography fontWeight={800} gutterBottom>
          {accepted ? "Request accepted" : "Request denied"}
        </Typography>
        <Typography variant="body2">
          {accepted
            ? "This request passed policy evaluation and is ready for deterministic proposal generation. Cloud execution, when configured, remains in a protected external workflow."
            : "This request is blocked until the policy issues are resolved. Denied requests cannot produce a deployment proposal."}
        </Typography>
      </Alert>

      <SectionCard
        title="Decision and next step"
        description="The decision is produced by the configured provider and mode policy set."
        action={<ProviderBadge provider={request.provider} />}
      >
        <Stack spacing={2}>
          {accepted ? (
            <>
              <Stack
                direction={{ xs: "column", sm: "row" }}
                spacing={1.5}
                alignItems={{ sm: "center" }}
              >
                <CloudQueueRoundedIcon color="primary" aria-hidden="true" />
                <Typography>
                  Generate an immutable review proposal containing the evaluated
                  configuration and deterministic artifacts.
                </Typography>
              </Stack>
              <Button
                variant="contained"
                endIcon={<ArrowForwardRoundedIcon />}
                onClick={() => proposalMutation.mutate()}
                disabled={proposalMutation.isPending}
                sx={{ alignSelf: { xs: "stretch", sm: "flex-start" } }}
              >
                {proposalMutation.isPending
                  ? "Creating review proposal…"
                  : "Create review proposal"}
              </Button>
              {proposalMutation.isError && (
                <Alert severity="error" role="alert">
                  {apiErrorMessage(
                    proposalMutation.error,
                    "The review proposal could not be created.",
                  )}
                  {apiErrorFields(proposalMutation.error).map((field) => (
                    <Typography
                      key={`${field.code}-${field.field}`}
                      component="div"
                    >
                      {field.field}: {field.message}
                    </Typography>
                  ))}
                </Alert>
              )}
            </>
          ) : (
            <PolicyErrors violations={outcome.decision.violations} />
          )}
        </Stack>
      </SectionCard>

      <SectionCard
        title="Request summary"
        description="The normalized values that were used for policy evaluation."
        action={
          <CopyValue value={request.request_id} label="Request ID" compact />
        }
      >
        <Stack
          divider={<Divider flexItem />}
          sx={{
            display: "grid",
            gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))" },
            columnGap: 3,
          }}
        >
          {requestFields.map(([label, key]) => (
            <Stack key={key} spacing={0.35} sx={{ py: 1.35, minWidth: 0 }}>
              <Typography variant="overline" color="text.secondary">
                {label}
              </Typography>
              <Typography sx={{ overflowWrap: "anywhere" }}>
                {key === "monthly_budget"
                  ? `$${request[key]}/month`
                  : request[key]}
              </Typography>
            </Stack>
          ))}
        </Stack>
      </SectionCard>

      {outcome.result ? (
        <SectionCard
          title="Evaluated resources"
          description="Provider-native resources represented by the simulation or proposal evaluation."
        >
          <Stack spacing={1}>
            {outcome.result.resources.map((resource) => (
              <Stack
                key={`${resource.kind}-${resource.name}`}
                direction={{ xs: "column", sm: "row" }}
                justifyContent="space-between"
                gap={1}
                sx={{
                  border: 1,
                  borderColor: "divider",
                  borderRadius: 1.5,
                  px: 2,
                  py: 1.5,
                }}
              >
                <Typography fontWeight={700}>{resource.name}</Typography>
                <Typography
                  color="text.secondary"
                  sx={{ overflowWrap: "anywhere" }}
                >
                  {resource.kind}
                </Typography>
              </Stack>
            ))}
          </Stack>
        </SectionCard>
      ) : (
        <SectionCard
          title="Evaluated resources"
          description="No resource evaluation is available for this decision."
        >
          <EmptyState
            icon={<ErrorOutlineRoundedIcon />}
            title="No resources were evaluated"
            description="Resolve the policy issues and submit the request again to receive a provider resource evaluation."
          />
        </SectionCard>
      )}

      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        gap={1}
      >
        <Button
          component={RouterLink}
          to="/"
          variant="outlined"
          startIcon={<ArrowBackRoundedIcon />}
        >
          Back to dashboard
        </Button>
        <Button component={RouterLink} to="/operations" variant="text">
          View operations
        </Button>
      </Stack>
    </Stack>
  );
}
