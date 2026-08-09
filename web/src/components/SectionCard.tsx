import type { ReactNode } from "react";
import { Card, CardContent, Stack, Typography } from "@mui/material";

type SectionCardProps = {
  title: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
};

export function SectionCard({
  title,
  description,
  action,
  children,
}: SectionCardProps) {
  return (
    <Card component="section">
      <CardContent>
        <Stack
          direction={{ xs: "column", sm: "row" }}
          justifyContent="space-between"
          gap={2}
          mb={2}
        >
          <Stack spacing={0.35}>
            <Typography variant="h2" fontSize={22}>
              {title}
            </Typography>
            {description && (
              <Typography variant="body2" color="text.secondary">
                {description}
              </Typography>
            )}
          </Stack>
          {action}
        </Stack>
        {children}
      </CardContent>
    </Card>
  );
}
