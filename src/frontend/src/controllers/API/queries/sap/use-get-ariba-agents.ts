import { useQuery } from "@tanstack/react-query";
import { api } from "../../api";

export interface AribaAgent {
  ID: string;
  name: string;
  expertIn: string;
  initialInstructions: string;
  description?: string;
  advancedModel: string;
  baseModel: string;
  iterations: number;
  mode: string;
  safetyCheck: boolean;
  defaultOutputFormat: string;
  defaultOutputFormatOptions?: any;
  orchestrationModuleConfig?: any;
  createdAt: string;
  modifiedAt: string;
  postprocessingEnabled: boolean;
  preprocessingEnabled: boolean;
  type: string;
}

async function getAribaAgents(): Promise<AribaAgent[]> {
  console.log("DEBUG: Fetching Ariba agents from API...");
  try {
    const response = await api.get("/sap/ariba_agents");
    console.log("DEBUG: Ariba agents API response", { 
      status: response.status, 
      dataLength: response.data?.length,
      data: response.data 
    });
    return response.data;
  } catch (error) {
    console.error("DEBUG: Error fetching Ariba agents", error);
    throw error;
  }
}

export function useGetAribaAgents(options?: { enabled?: boolean }) {
  const query = useQuery({
    queryKey: ["ariba-agents"],
    queryFn: getAribaAgents,
    enabled: options?.enabled ?? true,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (renamed from cacheTime in newer versions)
  });

  console.log("DEBUG: useGetAribaAgents hook state", {
    isLoading: query.isLoading,
    isSuccess: query.isSuccess,
    isError: query.isError,
    error: query.error,
    dataLength: query.data?.length,
    enabled: options?.enabled ?? true,
    actualData: query.data
  });

  return query;
}
