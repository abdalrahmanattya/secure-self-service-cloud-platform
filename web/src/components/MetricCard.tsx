import type { ReactNode } from "react";
import { Card, CardContent, Stack, Typography } from "@mui/material";

type MetricCardProps = {
  label: string;
  value: ReactNode;
  description?: string;
  icon?: ReactNode;
  accent?: "primary" | "info" | "success" | "warning";
};

export function MetricCard({
  label,
  value,
  description,
  icon,
  accent = "primary",
}: MetricCardProps) {
  return (
    <Card
      sx={{ height: "100%", borderTop: 3, borderTopColor: `${accent}.main` }}
    >
      <CardContent>
        <Stack direction="row" justifyContent="space-between" gap={2}>
          <Stack spacing={0.5}>
            <Typography variant="body2" color="text.secondary" fontWeight={700}>
              {label}
            </Typography>
            <Typography variant="h2" sx={{ fontSize: { xs: 28, md: 32 } }}>
              {value}
            </Typography>
            {description && (
              <Typography variant="body2" color="text.secondary">
                {description}
              </Typography>
            )}
          </Stack>
          {icon && (
            <Stack color={`${accent}.main`} aria-hidden="true">
              {icon}
            </Stack>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}
