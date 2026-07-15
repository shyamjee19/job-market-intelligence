import type { AIToolResponse } from "../types";
import { apiRequest } from "./httpClient";

export function analyzeResume(resumeText: string): Promise<AIToolResponse> {
  return apiRequest("/ai/tools/resume-analyzer", { method: "POST", body: { resume_text: resumeText } });
}

export function getCareerAdvice(currentSkills: string, goal: string): Promise<AIToolResponse> {
  return apiRequest("/ai/tools/career-advisor", { method: "POST", body: { current_skills: currentSkills, goal } });
}

export function getSkillGap(currentSkills: string, targetRole: string): Promise<AIToolResponse> {
  return apiRequest("/ai/tools/skill-gap", { method: "POST", body: { current_skills: currentSkills, target_role: targetRole } });
}

export function getSalaryInsights(role?: string, location?: string): Promise<AIToolResponse> {
  return apiRequest("/ai/tools/salary-insights", { method: "POST", body: { role: role || null, location: location || null } });
}

export function getJobRecommendations(): Promise<AIToolResponse> {
  return apiRequest("/ai/tools/job-recommendations");
}

export function getInterviewPrep(role: string, company?: string): Promise<AIToolResponse> {
  return apiRequest("/ai/tools/interview-prep", { method: "POST", body: { role, company: company || null } });
}
