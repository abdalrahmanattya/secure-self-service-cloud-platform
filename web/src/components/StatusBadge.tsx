import type { ChipProps } from "@mui/material";
import { Chip } from "@mui/material";

type StatusBadgeProps = Omit<ChipProps, "color" | "label"> & {
  status: string;
  label?: string;
};

function statusColor(status: string): ChipProps["color"] {
  const normalized = status.toLowerCase();
  if (/(ready|accept|active|success|available|complete)/.test(normalized))
    return "success";
  if (/(deny|error|fail|blocked)/.test(normalized)) return "error";
  if (/(review|pending|warn|guard|not_configured)/.test(normalized))
    return "warning";
  return "default";
}

export function StatusBadge({ status, label, ...props }: StatusBadgeProps) {
  return (
    <Chip
      {...props}
      label={label ?? status.replaceAll("_", " ")}
      color={statusColor(status)}
      size={props.size ?? "small"}
    />
  );
}

type ProviderBadgeProps = Omit<ChipProps, "color" | "label"> & {
  provider?: string | null;
};

export function ProviderBadge({ provider, ...props }: ProviderBadgeProps) {
  return (
    <Chip
      {...props}
      label={provider ? provider.toUpperCase() : "Provider not set"}
      color="info"
      size={props.size ?? "small"}
    />
  );
}
