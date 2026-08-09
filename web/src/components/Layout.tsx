import CloudQueueOutlinedIcon from "@mui/icons-material/CloudQueueOutlined";
import DashboardOutlinedIcon from "@mui/icons-material/DashboardOutlined";
import DescriptionOutlinedIcon from "@mui/icons-material/DescriptionOutlined";
import FactCheckOutlinedIcon from "@mui/icons-material/FactCheckOutlined";
import MenuOutlinedIcon from "@mui/icons-material/MenuOutlined";
import ShieldOutlinedIcon from "@mui/icons-material/ShieldOutlined";
import TimelineOutlinedIcon from "@mui/icons-material/TimelineOutlined";
import {
  Alert,
  AppBar,
  Box,
  Button,
  Chip,
  CircularProgress,
  Drawer,
  Divider,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Skeleton,
  Stack,
  Toolbar,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { Suspense, useState } from "react";
import { Link as RouterLink, Outlet, useLocation } from "react-router-dom";
import { api } from "../api/client";
import { ProviderBadge, StatusBadge } from "./StatusBadge";

const drawerWidth = 264;
const pageOwnedInstallationPaths = new Set(["/", "/setup", "/readiness"]);

const navigation = [
  { label: "Overview", to: "/", icon: <DashboardOutlinedIcon /> },
  {
    label: "New request",
    to: "/requests/new",
    icon: <DescriptionOutlinedIcon />,
  },
  { label: "Readiness", to: "/readiness", icon: <FactCheckOutlinedIcon /> },
  { label: "Operations", to: "/operations", icon: <TimelineOutlinedIcon /> },
];

function PlatformMark({ compact = false }: { compact?: boolean }) {
  return (
    <Stack direction="row" spacing={1.25} alignItems="center" minWidth={0}>
      <Box
        sx={{
          position: "relative",
          display: "grid",
          placeItems: "center",
          width: 38,
          height: 38,
          color: "info.light",
          flexShrink: 0,
        }}
        aria-hidden="true"
      >
        <CloudQueueOutlinedIcon sx={{ fontSize: 36 }} />
        <ShieldOutlinedIcon
          sx={{
            position: "absolute",
            fontSize: 16,
            bottom: 0,
            right: 0,
            color: "primary.light",
          }}
        />
      </Box>
      {!compact && (
        <Stack minWidth={0}>
          <Typography
            variant="subtitle1"
            fontWeight={800}
            lineHeight={1.15}
            noWrap
          >
            Secure Self-Service
          </Typography>
          <Typography
            variant="caption"
            sx={{ color: "rgba(255,255,255,0.65)" }}
            noWrap
          >
            Cloud Platform
          </Typography>
        </Stack>
      )}
    </Stack>
  );
}

function isActive(pathname: string, to: string) {
  if (to === "/") return pathname === "/";
  return pathname === to || pathname.startsWith(`${to}/`);
}

type InstallationQueryState = {
  data?: { provider?: string | null; mode?: string; status?: string };
  isPending: boolean;
};
type SidebarProps = {
  onNavigate?: () => void;
  installation: InstallationQueryState;
};

function Sidebar({ onNavigate, installation }: SidebarProps) {
  const location = useLocation();
  const profile = installation.data;
  const configured = Boolean(profile);
  return (
    <Box
      sx={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        bgcolor: "secondary.main",
        color: "common.white",
      }}
    >
      <Box sx={{ px: 2.5, py: 2.25 }}>
        <PlatformMark />
      </Box>
      <Divider sx={{ borderColor: "rgba(255,255,255,0.1)" }} />
      <Box
        component="nav"
        aria-label="Primary navigation"
        sx={{ px: 1.5, py: 2 }}
      >
        <Typography
          variant="overline"
          sx={{ px: 1.5, color: "rgba(255,255,255,0.5)" }}
        >
          Workspace
        </Typography>
        <List disablePadding sx={{ mt: 0.75 }}>
          {navigation.map((item) => {
            const active = isActive(location.pathname, item.to);
            return (
              <ListItemButton
                key={item.to}
                component={RouterLink}
                to={item.to}
                onClick={onNavigate}
                selected={active}
                aria-current={active ? "page" : undefined}
                sx={{
                  color: "rgba(255,255,255,0.75)",
                  borderRadius: 2,
                  mb: 0.5,
                  py: 1.05,
                  "&.Mui-selected": {
                    color: "common.white",
                    bgcolor: "rgba(79,179,191,0.2)",
                  },
                  "&.Mui-selected:hover": { bgcolor: "rgba(79,179,191,0.28)" },
                  "&:hover": { bgcolor: "rgba(255,255,255,0.08)" },
                }}
              >
                <ListItemIcon sx={{ color: "inherit", minWidth: 38 }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.label}
                  primaryTypographyProps={{ fontWeight: active ? 750 : 600 }}
                />
              </ListItemButton>
            );
          })}
        </List>
      </Box>
      <Box sx={{ mt: "auto", px: 2, pb: 2 }}>
        <Box
          sx={{
            p: 1.5,
            border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: 2,
            bgcolor: "rgba(0,0,0,0.12)",
          }}
        >
          <Stack
            direction="row"
            justifyContent="space-between"
            alignItems="center"
            gap={1}
            mb={1}
          >
            <Typography
              variant="caption"
              fontWeight={750}
              color="rgba(255,255,255,0.8)"
            >
              Installation context
            </Typography>
            {configured ? (
              <StatusBadge status={profile?.status ?? "active"} />
            ) : (
              <Chip
                label="Not configured"
                size="small"
                sx={{
                  color: "common.white",
                  borderColor: "rgba(255,255,255,0.35)",
                }}
                variant="outlined"
              />
            )}
          </Stack>
          {installation.isPending ? (
            <Skeleton
              variant="rounded"
              height={20}
              sx={{ bgcolor: "rgba(255,255,255,0.12)" }}
            />
          ) : configured ? (
            <Stack direction="row" gap={0.75} flexWrap="wrap">
              <ProviderBadge provider={profile?.provider} />
              <Chip
                label={profile?.mode ?? "mode unknown"}
                size="small"
                sx={{
                  color: "rgba(255,255,255,0.8)",
                  borderColor: "rgba(255,255,255,0.25)",
                }}
                variant="outlined"
              />
            </Stack>
          ) : (
            <Button
              component={RouterLink}
              to="/setup"
              onClick={onNavigate}
              size="small"
              variant="outlined"
              sx={{
                color: "common.white",
                borderColor: "rgba(255,255,255,0.4)",
                mt: 0.5,
              }}
            >
              Set up installation
            </Button>
          )}
          <Typography
            variant="caption"
            display="block"
            sx={{ color: "rgba(255,255,255,0.55)", mt: 1 }}
          >
            Review-only · no direct cloud execution
          </Typography>
        </Box>
      </Box>
    </Box>
  );
}

export function Layout() {
  const theme = useTheme();
  const desktop = useMediaQuery(theme.breakpoints.up("md"));
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const installation = useQuery({
    queryKey: ["installation"],
    queryFn: api.installation,
    retry: false,
  });

  return (
    <Box
      sx={{
        minHeight: "100vh",
        bgcolor: "background.default",
        display: "flex",
      }}
    >
      <Box
        component="aside"
        sx={{
          display: { xs: "none", md: "block" },
          width: drawerWidth,
          flexShrink: 0,
        }}
      >
        <Drawer
          variant="permanent"
          sx={{
            width: drawerWidth,
            "& .MuiDrawer-paper": {
              width: drawerWidth,
              boxSizing: "border-box",
            },
          }}
        >
          <Sidebar installation={installation} />
        </Drawer>
      </Box>
      {!desktop && (
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{
            "& .MuiDrawer-paper": {
              width: drawerWidth,
              boxSizing: "border-box",
            },
          }}
        >
          <Sidebar
            onNavigate={() => setMobileOpen(false)}
            installation={installation}
          />
        </Drawer>
      )}
      <Box sx={{ minWidth: 0, flexGrow: 1 }}>
        <AppBar
          position="sticky"
          color="secondary"
          sx={{ display: { xs: "block", md: "none" } }}
        >
          <Toolbar sx={{ minHeight: 64, gap: 1.5 }}>
            <IconButton
              color="inherit"
              onClick={() => setMobileOpen(true)}
              aria-label="Open navigation"
            >
              <MenuOutlinedIcon />
            </IconButton>
            <PlatformMark compact />
            <Typography
              variant="caption"
              sx={{ ml: "auto", color: "rgba(255,255,255,0.7)" }}
            >
              Review-only
            </Typography>
          </Toolbar>
        </AppBar>
        <Box
          component="main"
          sx={{
            px: { xs: 2, sm: 3, lg: 5 },
            py: { xs: 3, md: 5 },
            maxWidth: 1440,
            mx: "auto",
          }}
        >
          {installation.isError &&
            !pageOwnedInstallationPaths.has(location.pathname) && (
              <Alert severity="info" sx={{ mb: 3 }}>
                No installation is configured.{" "}
                <Button
                  component={RouterLink}
                  to="/setup"
                  size="small"
                  sx={{ ml: 1 }}
                >
                  Open setup
                </Button>
              </Alert>
            )}
          <Suspense
            fallback={
              <Stack
                alignItems="center"
                justifyContent="center"
                role="status"
                aria-live="polite"
                sx={{ minHeight: 320, textAlign: "center" }}
              >
                <CircularProgress
                  size={32}
                  thickness={4}
                  aria-label="Loading page"
                />
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mt: 2 }}
                >
                  Loading workspace…
                </Typography>
              </Stack>
            }
          >
            <Outlet />
          </Suspense>
        </Box>
      </Box>
    </Box>
  );
}
