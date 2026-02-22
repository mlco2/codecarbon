import { createBrowserRouter } from "react-router-dom";
import { lazy, Suspense } from "react";
import DashboardLayout from "./layouts/DashboardLayout";
import AuthGuard from "./components/auth-guard";
import Loader from "./components/loader";

const LandingPage = lazy(() => import("./pages/LandingPage"));
const PrivacyPage = lazy(() => import("./pages/PrivacyPage"));
const PublicProjectPage = lazy(() => import("./pages/PublicProjectPage"));
const HomePage = lazy(() => import("./pages/HomePage"));
const OrgDashboardPage = lazy(() => import("./pages/OrgDashboardPage"));
const ProjectsPage = lazy(() => import("./pages/ProjectsPage"));
const ProjectDashboardPage = lazy(() => import("./pages/ProjectDashboardPage"));
const ProjectSettingsPage = lazy(() => import("./pages/ProjectSettingsPage"));
const MembersPage = lazy(() => import("./pages/MembersPage"));

function SuspenseWrapper({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<Loader />}>{children}</Suspense>;
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: (
      <SuspenseWrapper>
        <LandingPage />
      </SuspenseWrapper>
    ),
  },
  {
    path: "/privacy",
    element: (
      <SuspenseWrapper>
        <PrivacyPage />
      </SuspenseWrapper>
    ),
  },
  {
    path: "/public/projects/:projectId",
    element: (
      <SuspenseWrapper>
        <PublicProjectPage />
      </SuspenseWrapper>
    ),
  },
  {
    element: (
      <AuthGuard>
        <DashboardLayout />
      </AuthGuard>
    ),
    children: [
      {
        path: "/home",
        element: (
          <SuspenseWrapper>
            <HomePage />
          </SuspenseWrapper>
        ),
      },
      {
        path: "/:organizationId",
        element: (
          <SuspenseWrapper>
            <OrgDashboardPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: "/:organizationId/projects",
        element: (
          <SuspenseWrapper>
            <ProjectsPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: "/:organizationId/projects/:projectId",
        element: (
          <SuspenseWrapper>
            <ProjectDashboardPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: "/:organizationId/projects/:projectId/settings",
        element: (
          <SuspenseWrapper>
            <ProjectSettingsPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: "/:organizationId/members",
        element: (
          <SuspenseWrapper>
            <MembersPage />
          </SuspenseWrapper>
        ),
      },
    ],
  },
]);
