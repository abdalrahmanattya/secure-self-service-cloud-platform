import ContentCopyOutlinedIcon from "@mui/icons-material/ContentCopyOutlined";
import CheckOutlinedIcon from "@mui/icons-material/CheckOutlined";
import { IconButton, Stack, Tooltip, Typography } from "@mui/material";
import { useState } from "react";

type CopyValueProps = { value: string; label?: string; compact?: boolean };

export function CopyValue({ value, label, compact = false }: CopyValueProps) {
  const [copied, setCopied] = useState(false);
  const [copyFailed, setCopyFailed] = useState(false);
  const copy = async () => {
    setCopied(false);
    setCopyFailed(false);
    try {
      if (!navigator.clipboard?.writeText)
        throw new Error("Clipboard unavailable");
      await navigator.clipboard.writeText(value);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopyFailed(true);
    }
  };
  return (
    <Stack
      direction="row"
      spacing={0.5}
      alignItems="flex-start"
      minWidth={0}
      sx={{
        maxWidth: "100%",
        flexWrap: "wrap",
        rowGap: 0.25,
      }}
    >
      {label && (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ minWidth: 0, overflowWrap: "anywhere" }}
        >
          {label}
        </Typography>
      )}
      <Typography
        variant="body2"
        fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace"
        noWrap={!compact}
        sx={{
          minWidth: 0,
          maxWidth: "100%",
          flex: "1 1 12ch",
          overflowWrap: "anywhere",
        }}
      >
        {value}
      </Typography>
      <Tooltip
        title={copied ? "Copied" : copyFailed ? "Copy failed" : "Copy value"}
      >
        <IconButton
          size="small"
          onClick={() => void copy()}
          aria-label={`Copy ${label ?? "value"}`}
        >
          {copied ? (
            <CheckOutlinedIcon fontSize="inherit" />
          ) : (
            <ContentCopyOutlinedIcon fontSize="inherit" />
          )}
        </IconButton>
      </Tooltip>
      <Typography
        component="span"
        role="status"
        aria-live="polite"
        sx={{
          position: "absolute",
          width: "1px",
          height: "1px",
          p: 0,
          m: -1,
          overflow: "hidden",
          clip: "rect(0 0 0 0)",
          whiteSpace: "nowrap",
          border: 0,
        }}
      >
        {copied ? "Copied" : copyFailed ? "Copy failed" : ""}
      </Typography>
    </Stack>
  );
}
