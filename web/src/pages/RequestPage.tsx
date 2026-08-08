import {
  Alert,
  Button,
  Card,
  CardContent,
  Chip,
  Stack,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef } from "react";
import { Link as RouterLink, useNavigate, useParams } from "react-router-dom";
import { api, apiErrorFields, apiErrorMessage } from "../api/client";
import { PolicyErrors } from "../components/PolicyErrors";

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
            <Stack spacing={2}>
              <Alert severity="success">
                This accepted request is ready for deterministic proposal
                generation. Cloud execution, when configured, happens through a
                protected external workflow.
              </Alert>
              <Button
                variant="contained"
                onClick={() => proposalMutation.mutate()}
                disabled={proposalMutation.isPending}
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
            </Stack>
          ) : (
            <Stack spacing={2}>
              <Alert severity="error">
                This request is blocked until the policy issues are resolved.
                Denied requests cannot produce a deployment proposal.
              </Alert>
            </Stack>
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
              Evaluated resources
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
