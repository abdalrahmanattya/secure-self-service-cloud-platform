import { alpha, createTheme } from "@mui/material/styles";

const navy = "#102a43";
const slate = "#243b53";
const teal = "#087f8c";

export const theme = createTheme({
  palette: {
    primary: {
      main: teal,
      dark: "#05616b",
      light: "#4fb3bf",
      contrastText: "#ffffff",
    },
    secondary: {
      main: navy,
      dark: "#071a2b",
      light: "#486581",
      contrastText: "#ffffff",
    },
    info: { main: "#147d92", light: "#d9f3f7", dark: "#07566a" },
    success: { main: "#227a57", light: "#e3f5eb", dark: "#14563d" },
    warning: { main: "#a15c07", light: "#fff4dc", dark: "#713e05" },
    error: { main: "#ba3a3a", light: "#fde8e8", dark: "#842029" },
    background: { default: "#f4f7f9", paper: "#ffffff" },
    text: { primary: "#172b4d", secondary: "#526579" },
    divider: "#d9e2ec",
  },
  typography: {
    fontFamily:
      'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    h1: {
      fontSize: "2.25rem",
      lineHeight: 1.15,
      fontWeight: 750,
      letterSpacing: "-0.025em",
    },
    h2: {
      fontSize: "1.35rem",
      lineHeight: 1.3,
      fontWeight: 700,
      letterSpacing: "-0.01em",
    },
    h3: { fontSize: "1.05rem", lineHeight: 1.4, fontWeight: 700 },
    body1: { lineHeight: 1.55 },
    body2: { lineHeight: 1.5 },
    overline: {
      fontSize: "0.7rem",
      lineHeight: 1.4,
      fontWeight: 750,
      letterSpacing: "0.1em",
    },
    button: { fontWeight: 700, textTransform: "none" },
  },
  shape: { borderRadius: 12 },
  spacing: 8,
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: { margin: 0 },
        "*": { scrollbarColor: `${alpha(navy, 0.28)} transparent` },
        "*:focus-visible": {
          outline: `3px solid ${alpha(teal, 0.45)}`,
          outlineOffset: 2,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          border: "1px solid #d9e2ec",
          boxShadow: "0 6px 20px rgba(16, 42, 67, 0.055)",
          backgroundImage: "none",
        },
      },
    },
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: { borderRadius: 9, minHeight: 40, paddingInline: 16 },
        containedPrimary: { boxShadow: `0 4px 10px ${alpha(teal, 0.2)}` },
      },
    },
    MuiTextField: { defaultProps: { variant: "outlined", size: "small" } },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          backgroundColor: "#ffffff",
          borderRadius: 9,
          "&:hover .MuiOutlinedInput-notchedOutline": { borderColor: teal },
          "&.Mui-focused .MuiOutlinedInput-notchedOutline": { borderWidth: 2 },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { borderRadius: 7, fontWeight: 700 },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: { borderRadius: 10, alignItems: "flex-start" },
        message: { paddingBlock: 2 },
      },
    },
    MuiTooltip: {
      defaultProps: { arrow: true },
      styleOverrides: {
        tooltip: { backgroundColor: navy, fontSize: "0.75rem" },
      },
    },
    MuiSkeleton: {
      styleOverrides: { root: { borderRadius: 8, transform: "none" } },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: { borderRight: "1px solid rgba(255,255,255,0.09)" },
      },
    },
  },
});
