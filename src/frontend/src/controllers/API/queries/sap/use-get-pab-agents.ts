import type { UseQueryResult } from "@tanstack/react-query";
import type { useQueryFunctionType } from "@/types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

interface PABAgent {
  ID: string;
  name: string;
  type: string;
  safetyCheck: boolean;
  expertIn: string;
  initialInstructions: string;
  iterations: number;
  baseModel: string;
  advancedModel: string;
  preprocessingEnabled: boolean;
  postprocessingEnabled: boolean;
  createdAt: string;
  modifiedAt: string;
}

export const useGetPABAgents: useQueryFunctionType<undefined, PABAgent[]> = (
  options?,
) => {
  const { query } = UseRequestProcessor();

  const getPABAgentsFunction = async (): Promise<PABAgent[]> => {
    const response = await api.get(`${getURL("SAP")}/ariba_agents`);
    return response.data;
  };

  const queryResult: UseQueryResult<PABAgent[]> = query(
    ["useGetPABAgents"],
    getPABAgentsFunction,
    {
      refetchOnWindowFocus: false,
      ...options,
    },
  );

  return queryResult;
};

// Also export as default for compatibility
export default useGetPABAgents;
