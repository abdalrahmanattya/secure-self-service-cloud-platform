import type { ReactNode } from "react";
import { Stack, Typography } from "@mui/material";

type EmptyStateProps = {
  title: string;
  description: string;
  action?: ReactNode;
  icon?: ReactNode;
};

export function EmptyState({
  title,
  description,
  action,
  icon,
}: EmptyStateProps) {
  return (
    <Stack spacing={1} alignItems="flex-start" sx={{ py: 2 }}>
      {icon && (
        <Stack color="text.secondary" aria-hidden="true">
          {icon}
        </Stack>
      )}
      <Typography fontWeight={700}>{title}</Typography>
      <Typography variant="body2" color="text.secondary">
        {description}
      </Typography>
      {action}
    </Stack>
  );
}
