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

async function getPABCredentials(): Promise<PABCredentialsResponse> {
  const response = await api.get("/sap/pab/credentials");
  return response.data;
}

export function useGetPABCredentials() {
  return useQuery({
    queryKey: ["pab-credentials"],
    queryFn: getPABCredentials,
    retry: false, // Don't retry if credentials don't exist
    refetchOnWindowFocus: false,
  });
}
