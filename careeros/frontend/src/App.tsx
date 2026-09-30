import { Navigate, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { RequireAuth } from "./components/auth/RequireAuth";
import { AppLayout } from "./components/layout/AppLayout";
import { JobsPage } from "./pages/JobsPage";
import { ResumesPage } from "./pages/ResumesPage";
import { ResumeEditorPage } from "./pages/ResumeEditorPage";
import { CRMDashboardPage } from "./pages/CRMDashboardPage";
import { ApplicationsPage } from "./pages/ApplicationsPage";
import { ApplicationDetailPage } from "./pages/ApplicationDetailPage";
import { PipelinePage } from "./pages/PipelinePage";
import { ProfilePage } from "./pages/ProfilePage";
import { CareerBrainPage } from "./pages/CareerBrainPage";
import { MatchesPage } from "./pages/MatchesPage";
import { SettingsPage } from "./pages/SettingsPage";
import { CareerDataPage } from "./pages/CareerDataPage";
import { CRMWorkspacePage } from "./pages/CRMWorkspacePage";
import { MatchDetailPage } from "./pages/MatchDetailPage";
import { JobDiscoveryPage } from "./pages/JobDiscoveryPage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { JobDetailPage } from "./pages/JobDetailPage";

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route element={<RequireAuth />}>
          <Route element={<AppLayout />}>
            <Route path="/jobs" element={<JobsPage />} />
            <Route path="/jobs/:id" element={<JobDetailPage />} />
            <Route path="/job-discovery" element={<JobDiscoveryPage />} />
            <Route path="/resumes" element={<ResumesPage />} />
            <Route path="/resumes/:id" element={<ResumeEditorPage />} />
            <Route path="/dashboard" element={<CRMDashboardPage />} />
            <Route path="/applications" element={<ApplicationsPage />} />
            <Route path="/applications/:id" element={<ApplicationDetailPage />} />
            <Route path="/pipeline" element={<PipelinePage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/career-brain" element={<CareerBrainPage />} />
            <Route path="/matches" element={<MatchesPage />} />
            <Route path="/matches/:jobId" element={<MatchDetailPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/career-data" element={<CareerDataPage />} />
            <Route path="/crm" element={<CRMWorkspacePage />} />
          </Route>
        </Route>
      </Routes>
    </AuthProvider>
  );
}
