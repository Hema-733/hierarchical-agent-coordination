// src/api/client.js — Centralized axios instance and API methods for FastAPI backend
import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8001",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000,
});

// ---------------------------------------------------------------------------
// Health Check
// ---------------------------------------------------------------------------
export async function checkBackendHealth() {
  const response = await apiClient.get("/health");
  return response.data;
}

// ---------------------------------------------------------------------------
// Onboarding & Employees
// ---------------------------------------------------------------------------
export async function submitOnboarding(employeeData) {
  const response = await apiClient.post("/onboarding/", employeeData);
  return response.data;
}

export async function getEmployees(skip = 0, limit = 50) {
  const response = await apiClient.get("/onboarding/employees", {
    params: { skip, limit },
  });
  return response.data;
}

export async function getEmployeeById(employeeId) {
  const response = await apiClient.get(`/onboarding/employees/${employeeId}`);
  return response.data;
}

export async function updateEmployeeDocuments(employeeId, documentsUpdate) {
  const response = await apiClient.patch(
    `/onboarding/employees/${employeeId}/documents`,
    documentsUpdate
  );
  return response.data;
}

// ---------------------------------------------------------------------------
// Workflows
// ---------------------------------------------------------------------------
export async function getWorkflows(statusFilter = null, skip = 0, limit = 50) {
  const params = { skip, limit };
  if (statusFilter && statusFilter !== "ALL") {
    params.status = statusFilter;
  }
  const response = await apiClient.get("/workflow/", { params });
  return response.data;
}

export async function getWorkflowById(workflowId) {
  const response = await apiClient.get(`/workflow/${workflowId}`);
  return response.data;
}

export async function executeWorkflow(workflowId) {
  const response = await apiClient.post(`/workflow/${workflowId}/execute`);
  return response.data;
}

export async function pauseWorkflow(workflowId, reason = null) {
  const response = await apiClient.post(`/workflow/${workflowId}/pause`, { reason });
  return response.data;
}

export async function resumeWorkflow(workflowId) {
  const response = await apiClient.post(`/workflow/${workflowId}/resume`);
  return response.data;
}

export async function getWorkflowSummary(workflowId) {
  const response = await apiClient.get(`/workflow/${workflowId}/summary`);
  return response.data;
}

export async function getAIWorkflowSummary(workflowId) {
  const response = await apiClient.get(`/workflow/${workflowId}/ai-summary`);
  return response.data;
}

// ---------------------------------------------------------------------------
// Tasks
// ---------------------------------------------------------------------------
export async function getWorkflowTasks(workflowId) {
  const response = await apiClient.get(`/task/workflow/${workflowId}`);
  return response.data;
}

export async function getTaskById(taskId) {
  const response = await apiClient.get(`/task/${taskId}`);
  return response.data;
}

export async function retryTask(taskId) {
  const response = await apiClient.post(`/task/${taskId}/retry`);
  return response.data;
}

// ---------------------------------------------------------------------------
// Agents
// ---------------------------------------------------------------------------
export async function getAgents() {
  const response = await apiClient.get("/agent/");
  return response.data;
}

export default apiClient;
