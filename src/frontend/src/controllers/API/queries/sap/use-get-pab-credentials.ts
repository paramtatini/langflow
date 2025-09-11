import { useQuery } from "@tanstack/react-query";
import { api } from "../../api";

export interface PABCredentialsResponse {
  service_urls: {
    agent_api_url: string;
  };
  uaa: {
    clientid: string;
    clientsecret: string;
    url: string;
  };
}

async function getPABCredentials(): Promise<PABCredentialsResponse | null> {
  try {
    const response = await api.get("/sap/pab/credentials");
    return response.data;
  } catch (error: any) {
    // If credentials don't exist (404), return null instead of throwing
    if (error.response?.status === 404) {
      return null;
    }
    // Re-throw other errors
    throw error;
  }
}

export function useGetPABCredentials() {
  return useQuery({
    queryKey: ["pab-credentials"],
    queryFn: getPABCredentials,
    retry: false, // Don't retry if credentials don't exist
    refetchOnWindowFocus: false,
    staleTime: 0, // Always consider data stale
    gcTime: 0, // Don't cache the data
  });
}
