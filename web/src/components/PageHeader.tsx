import type { ReactNode } from "react";
import { Stack, Typography } from "@mui/material";

type PageHeaderProps = {
  title: string;
  description?: string;
  eyebrow?: string;
  action?: ReactNode;
};

export function PageHeader({
  title,
  description,
  eyebrow,
  action,
}: PageHeaderProps) {
  return (
    <Stack
      direction={{ xs: "column", sm: "row" }}
      justifyContent="space-between"
      gap={2}
    >
      <Stack spacing={0.75}>
        {eyebrow && (
          <Typography variant="overline" color="primary.main">
            {eyebrow}
          </Typography>
        )}
        <Typography variant="h1" fontSize={{ xs: 30, md: 38 }}>
          {title}
        </Typography>
        {description && (
          <Typography color="text.secondary" maxWidth={720}>
            {description}
          </Typography>
        )}
      </Stack>
      {action && (
        <Stack direction="row" alignItems="center" flexShrink={0}>
          {action}
        </Stack>
      )}
    </Stack>
  );
}
