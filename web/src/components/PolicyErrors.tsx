import { Alert, Stack } from "@mui/material";
import type { PolicyViolation } from "../api/client";

export function PolicyErrors({
  violations,
}: {
  violations: PolicyViolation[];
}) {
  if (violations.length === 0) return null;
  return (
    <Stack role="alert" spacing={1} sx={{ mb: 2 }}>
      {violations.map((violation) => (
        <Alert key={`${violation.code}-${violation.field}`} severity="error">
          <strong>{violation.field}:</strong> {violation.message}
        </Alert>
      ))}
    </Stack>
  );
}
