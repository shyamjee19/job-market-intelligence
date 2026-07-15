import { AnimatePresence } from "framer-motion";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AppLayout } from "./components/AppLayout";
import { AdminRoute, GuestOnlyRoute, ProtectedRoute } from "./components/ProtectedRoute";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { AdminDashboardPage } from "./pages/AdminDashboardPage";
import { CareerAdvisorPage } from "./pages/ai/CareerAdvisorPage";
import { InterviewPrepPage } from "./pages/ai/InterviewPrepPage";
import { JobRecommendationsPage } from "./pages/ai/JobRecommendationsPage";
import { ResumeAnalyzerPage } from "./pages/ai/ResumeAnalyzerPage";
import { SalaryInsightsPage } from "./pages/ai/SalaryInsightsPage";
import { SkillGapPage } from "./pages/ai/SkillGapPage";
import { AssistantPage } from "./pages/AssistantPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ForgotPasswordPage } from "./pages/ForgotPasswordPage";
import { JobDetailPage } from "./pages/JobDetailPage";
import { JobsListPage } from "./pages/JobsListPage";
import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/LoginPage";
import { NotificationsPage } from "./pages/NotificationsPage";
import { OAuthCallbackPage } from "./pages/OAuthCallbackPage";
import { ProfilePage } from "./pages/ProfilePage";
import { RegisterPage } from "./pages/RegisterPage";
import { ResetPasswordPage } from "./pages/ResetPasswordPage";
import { SavedJobsPage } from "./pages/SavedJobsPage";
import { SettingsPage } from "./pages/SettingsPage";

// A logged-in visitor never sees the marketing landing page - straight
// to the dashboard instead, per the "skip login/landing when already
// authenticated" requirement.
function RootRoute() {
  const { user, isLoading } = useAuth();
  if (isLoading) return null;
  if (user) return <Navigate to="/dashboard" replace />;
  return <LandingPage />;
}

function AnimatedRoutes() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<RootRoute />} />

        <Route element={<AppLayout />}>
          <Route
            path="/jobs"
            element={
              <ProtectedRoute>
                <JobsListPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/jobs/:jobId"
            element={
              <ProtectedRoute>
                <JobDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/assistant"
            element={
              <ProtectedRoute>
                <AssistantPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/login"
            element={
              <GuestOnlyRoute>
                <LoginPage />
              </GuestOnlyRoute>
            }
          />
          <Route
            path="/register"
            element={
              <GuestOnlyRoute>
                <RegisterPage />
              </GuestOnlyRoute>
            }
          />
          <Route
            path="/forgot-password"
            element={
              <GuestOnlyRoute>
                <ForgotPasswordPage />
              </GuestOnlyRoute>
            }
          />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/oauth/callback" element={<OAuthCallbackPage />} />

          <Route
            path="/saved"
            element={
              <ProtectedRoute>
                <SavedJobsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <SettingsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/notifications"
            element={
              <ProtectedRoute>
                <NotificationsPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/ai/resume-analyzer"
            element={
              <ProtectedRoute>
                <ResumeAnalyzerPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/ai/career-advisor"
            element={
              <ProtectedRoute>
                <CareerAdvisorPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/ai/skill-gap"
            element={
              <ProtectedRoute>
                <SkillGapPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/ai/salary-insights"
            element={
              <ProtectedRoute>
                <SalaryInsightsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/ai/job-recommendations"
            element={
              <ProtectedRoute>
                <JobRecommendationsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/ai/interview-prep"
            element={
              <ProtectedRoute>
                <InterviewPrepPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin"
            element={
              <AdminRoute>
                <AdminDashboardPage />
              </AdminRoute>
            }
          />
        </Route>
      </Routes>
    </AnimatePresence>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AnimatedRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
