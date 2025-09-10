import type { UseMutationResult } from "@tanstack/react-query";
import type { AxiosResponse } from "axios";
import type { useMutationFunctionType } from "@/types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

interface PABCredentials {
  client_id: string;
  client_secret: string;
  token_url: string;
  service_url: string;
}

interface SavePABCredentialsResponse {
  success: boolean;
  message: string;
  agents?: any[];
}

export const useSavePABCredentials: useMutationFunctionType<
  undefined,
  PABCredentials
> = (options?) => {
  const { mutate, queryClient } = UseRequestProcessor();

  const savePABCredentialsFunction = async (
    credentials: PABCredentials,
  ): Promise<AxiosResponse<SavePABCredentialsResponse>> => {
    const res = await api.post(`${getURL("SAP")}/pab/credentials`, credentials);
    return res.data;
  };

  const mutation: UseMutationResult<any, any, PABCredentials> = mutate(
    ["useSavePABCredentials"],
    savePABCredentialsFunction,
    {
      onSettled: () => {
        queryClient.refetchQueries({ queryKey: ["useGetPABAgents"] });
      },
      ...options,
    },
  );

  return mutation;
};
