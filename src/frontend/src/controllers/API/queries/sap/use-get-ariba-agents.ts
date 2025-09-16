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

// Mock data for testing when API is not available
const mockAribaAgents: AribaAgent[] = [
  {
    ID: "0c1acd55-265e-4599-9057-b13cba5404c9",
    name: "Updated Test Agent",
    expertIn: "Advanced testing and quality assurance processes",
    initialInstructions: "You are an expert testing agent focused on comprehensive quality assurance, test automation, and validation processes. Help users create robust testing strategies.",
    description: "Specialized agent for testing and QA processes",
    advancedModel: "PAB_GPT4o",
    baseModel: "PAB_GPT4o_mini",
    iterations: 15,
    mode: "smart",
    safetyCheck: true,
    defaultOutputFormat: "markdown",
    createdAt: "2024-01-15T10:00:00Z",
    modifiedAt: "2024-01-20T15:30:00Z",
    postprocessingEnabled: true,
    preprocessingEnabled: true,
    type: "smart"
  },
  {
    ID: "4b5bddf6-a656-4a47-9f76-827aefbeec74",
    name: "BidAnalysis2",
    expertIn: "Advanced bid analysis and procurement evaluation",
    initialInstructions: "You are a specialized procurement agent focused on bid analysis, vendor evaluation, and contract optimization. Analyze bids comprehensively and provide strategic recommendations.",
    description: "Expert in bid analysis and procurement processes",
    advancedModel: "PAB_GPT4o",
    baseModel: "PAB_GPT4o_mini",
    iterations: 20,
    mode: "smart",
    safetyCheck: true,
    defaultOutputFormat: "structured",
    createdAt: "2024-01-10T08:00:00Z",
    modifiedAt: "2024-01-18T12:45:00Z",
    postprocessingEnabled: true,
    preprocessingEnabled: true,
    type: "smart"
  },
  {
    ID: "4ed3f502-4d52-49e4-a343-87ef272e48e7",
    name: "toUpper",
    expertIn: "Text transformation and string manipulation",
    initialInstructions: "You are a text processing specialist focused on string transformations, formatting, and text manipulation tasks. Convert text to uppercase and handle various text processing requirements.",
    description: "Specialized in text transformation operations",
    advancedModel: "PAB_GPT4o",
    baseModel: "PAB_GPT35_turbo",
    iterations: 10,
    mode: "smart",
    safetyCheck: true,
    defaultOutputFormat: "text",
    createdAt: "2024-01-12T14:20:00Z",
    modifiedAt: "2024-01-19T09:15:00Z",
    postprocessingEnabled: false,
    preprocessingEnabled: true,
    type: "smart"
  },
  {
    ID: "122af2fa-89ea-493f-9e4f-257a19aa6c71",
    name: "Test Procurement Assistant",
    expertIn: "Procurement processes and vendor management",
    initialInstructions: "You are a procurement assistant specializing in vendor management, purchase order processing, and supply chain optimization. Help streamline procurement workflows and vendor relationships.",
    description: "Assistant for procurement and vendor management",
    advancedModel: "PAB_GPT4o",
    baseModel: "PAB_GPT4o_mini",
    iterations: 25,
    mode: "smart",
    safetyCheck: true,
    defaultOutputFormat: "structured",
    createdAt: "2024-01-08T11:30:00Z",
    modifiedAt: "2024-01-22T16:20:00Z",
    postprocessingEnabled: true,
    preprocessingEnabled: true,
    type: "smart"
  },
  {
    ID: "42040d8d-9591-4146-840a-d97fc6527a27",
    name: "Initial Procurement Agent",
    expertIn: "Initial procurement setup and onboarding",
    initialInstructions: "You are an initial procurement setup specialist focused on onboarding new vendors, establishing procurement processes, and setting up initial contracts and agreements.",
    description: "Specialist in initial procurement setup",
    advancedModel: "PAB_Claude3_sonnet",
    baseModel: "PAB_GPT4o_mini",
    iterations: 18,
    mode: "smart",
    safetyCheck: true,
    defaultOutputFormat: "detailed",
    createdAt: "2024-01-05T09:45:00Z",
    modifiedAt: "2024-01-17T13:10:00Z",
    postprocessingEnabled: true,
    preprocessingEnabled: true,
    type: "smart"
  }
];

async function getAribaAgents(): Promise<AribaAgent[]> {
  console.log("DEBUG: Fetching Ariba agents from API...");
  try {
    const response = await api.get("/api/v1/sap/ariba_agents");
    console.log("DEBUG: Ariba agents API response", { 
      status: response.status, 
      dataLength: response.data?.length,
      data: response.data 
    });
    return response.data;
  } catch (error) {
    console.error("DEBUG: Error fetching Ariba agents, using mock data", error);
    console.log("DEBUG: Using mock Ariba agents data", { 
      mockDataLength: mockAribaAgents.length,
      mockData: mockAribaAgents 
    });
    // Return mock data when API is not available
    return mockAribaAgents;
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
    error: query.error?.message,
    dataLength: query.data?.length,
    enabled: options?.enabled ?? true,
    hasData: !!query.data,
    firstAgentName: query.data?.[0]?.name,
    firstAgentID: query.data?.[0]?.ID
  });
  
  if (query.isSuccess && query.data) {
    console.log("DEBUG: Ariba agents data received - type:", typeof query.data);
    console.log("DEBUG: Ariba agents data received - isArray:", Array.isArray(query.data));
    console.log("DEBUG: Ariba agents data received - raw:", query.data);
    
    if (Array.isArray(query.data)) {
      console.log("DEBUG: Ariba agents array data:", query.data.map(agent => ({
        name: agent.name,
        ID: agent.ID,
        expertIn: agent.expertIn
      })));
    }
  }

  return query;
}
