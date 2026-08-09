import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import LockOutlinedIcon from "@mui/icons-material/LockOutlined";
import RadioButtonUncheckedOutlinedIcon from "@mui/icons-material/RadioButtonUncheckedOutlined";
import { Box, Stack, Typography } from "@mui/material";
import { StatusBadge } from "./StatusBadge";

export type LifecycleStage = {
  name: string;
  description: string;
  status: "complete" | "ready" | "guarded" | "not_executed";
};
type LifecycleStatusProps = { stages: readonly LifecycleStage[] };

export function LifecycleStatus({ stages }: LifecycleStatusProps) {
  return (
    <Stack spacing={0}>
      {stages.map((stage, index) => {
        const complete = stage.status === "complete";
        const guarded =
          stage.status === "guarded" || stage.status === "not_executed";
        return (
          <Stack
            key={stage.name}
            direction="row"
            spacing={1.5}
            sx={{
              position: "relative",
              pb: index === stages.length - 1 ? 0 : 2,
            }}
          >
            {index < stages.length - 1 && (
              <Box
                sx={{
                  position: "absolute",
                  left: 11,
                  top: 24,
                  bottom: 0,
                  width: 2,
                  bgcolor: "divider",
                }}
                aria-hidden="true"
              />
            )}
            <Stack
              sx={{
                zIndex: 1,
                bgcolor: "background.paper",
                color: complete
                  ? "success.main"
                  : guarded
                    ? "text.secondary"
                    : "primary.main",
              }}
            >
              {complete ? (
                <CheckCircleOutlineIcon />
              ) : guarded ? (
                <LockOutlinedIcon />
              ) : (
                <RadioButtonUncheckedOutlinedIcon />
              )}
            </Stack>
            <Stack spacing={0.45} minWidth={0}>
              <Stack
                direction="row"
                gap={1}
                alignItems="center"
                flexWrap="wrap"
              >
                <Typography fontWeight={700}>{stage.name}</Typography>
                <StatusBadge
                  status={stage.status}
                  label={
                    stage.status === "not_executed"
                      ? "Not executed"
                      : stage.status
                  }
                />
              </Stack>
              <Typography variant="body2" color="text.secondary">
                {stage.description}
              </Typography>
            </Stack>
          </Stack>
        );
      })}
    </Stack>
  );
}
