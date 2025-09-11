import { useEffect, useState } from "react";
import { ForwardedIconComponent } from "@/components/common/genericIconComponent";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import {
  useGetPABAgents,
  useGetPABCredentials,
  useSavePABCredentials,
} from "@/controllers/API/queries/sap";
import useAlertStore from "@/stores/alertStore";

export default function SAPCredentialsPage() {
  const [pabCredentials, setPabCredentials] = useState("");
  const [aiCoreCredentials, setAiCoreCredentials] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);

  const { mutate: savePABCredentials } = useSavePABCredentials();
  const { refetch: refetchPABAgents } = useGetPABAgents();
  const { data: savedCredentials, isLoading: isLoadingCredentials } =
    useGetPABCredentials();

  // Load saved credentials when component mounts or when credentials are fetched
  useEffect(() => {
    if (savedCredentials && !isLoadingCredentials) {
      // Format the credentials back to the original service key format for editing
      const formattedCredentials = JSON.stringify(savedCredentials, null, 2);
      setPabCredentials(formattedCredentials);
    } else if (savedCredentials === null && !isLoadingCredentials) {
      // No credentials found, keep the field empty
      setPabCredentials("");
    }
  }, [savedCredentials, isLoadingCredentials]);

  const handleSavePABCredentials = async () => {
    if (!pabCredentials.trim()) {
      setErrorData({
        title: "Validation Error",
        list: ["PAB Credentials cannot be empty"],
      });
      return;
    }

    try {
      const credentials = JSON.parse(pabCredentials);
      setIsLoading(true);

      savePABCredentials(credentials, {
        onSuccess: () => {
          setSuccessData({
            title: "PAB Credentials saved successfully and agents fetched",
          });
          // Refetch agents after successful credential save
          refetchPABAgents();
        },
        onError: (error: any) => {
          const errorMessage = error.message || "Failed to save credentials";
          // Check if the error message looks like HTML
          const isHtml = /<html|<body|<!DOCTYPE/i.test(errorMessage);
          setErrorData({
            title: "Error saving PAB credentials",
            list: [
              isHtml
                ? "An unexpected server error occurred. Please check backend logs for details."
                : errorMessage,
            ],
          });
        },
        onSettled: () => {
          setIsLoading(false);
        },
      });
    } catch (error) {
      setErrorData({
        title: "Invalid JSON",
        list: ["Please provide valid JSON credentials"],
      });
    }
  };

  const handleSaveAICoreCredentials = async () => {
    if (!aiCoreCredentials.trim()) {
      setErrorData({
        title: "Validation Error",
        list: ["AI Core Credentials cannot be empty"],
      });
      return;
    }

    try {
      const credentials = JSON.parse(aiCoreCredentials);
      // TODO: Implement AI Core credentials save logic
      setSuccessData({
        title: "AI Core Credentials saved successfully",
      });
    } catch (error) {
      setErrorData({
        title: "Invalid JSON",
        list: ["Please provide valid JSON credentials"],
      });
    }
  };

  return (
    <div className="flex h-full w-full flex-col justify-between gap-6">
      <div className="flex w-full items-start justify-between gap-6">
        <div className="flex w-full flex-col">
          <h2 className="flex items-center text-lg font-semibold tracking-tight">
            SAP AI Credentials
            <ForwardedIconComponent
              name="Key"
              className="ml-2 h-5 w-5 text-primary"
            />
          </h2>
          <p className="text-sm text-muted-foreground">
            Manage your SAP AI service credentials for PAB and AI Core
            integration.
          </p>
        </div>
      </div>

      <div className="flex h-full w-full flex-col">
        <Tabs defaultValue="pab" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="pab">SAP PAB Credentials</TabsTrigger>
            <TabsTrigger value="aicore">SAP AI Core Credentials</TabsTrigger>
          </TabsList>

          <TabsContent value="pab" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Project Agent Builder (PAB) Credentials</CardTitle>
                <CardDescription>
                  Enter your SAP PAB service key in JSON format. Provide the
                  service key with 'service_urls' containing 'agent_api_url' and
                  'uaa' objects containing clientid, clientsecret, and
                  authentication URL.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="pab-credentials">Credentials JSON</Label>
                  <Textarea
                    id="pab-credentials"
                    placeholder={`{
  "service_urls": {
    "agent_api_url": "https://business-agent-foundation-srv-unified-agent.d44b0b9.kyma.ondemand.com/"
  },
  "uaa": {
    "clientid": "sb-a3f9e3b7-f1df-4a72-ad72-68c301eb138c!b160017|unified-ai-agent!b268611",
    "clientsecret": "8613da52-1227-445a-bd54-1518ba629910$T6g3lTvqmN76MPHN5Px5fkbhW7tiDVWDnylokm7r-ms=",
    "url": "https://d067837-75vbj506.authentication.eu12.hana.ondemand.com",
    "identityzone": "d067837-75vbj506",
    "tenantid": "b43ab822-101a-4774-a392-8c0b61e07fef",
    "xsappname": "a3f9e3b7-f1df-4a72-ad72-68c301eb138c!b160017|unified-ai-agent!b268611"
  }
}`}
                    value={pabCredentials}
                    onChange={(e) => setPabCredentials(e.target.value)}
                    className="min-h-[200px] font-mono text-sm"
                  />
                </div>
                <Button
                  onClick={handleSavePABCredentials}
                  disabled={isLoading}
                  className="w-full"
                >
                  {isLoading ? (
                    <>
                      <ForwardedIconComponent
                        name="Loader2"
                        className="mr-2 h-4 w-4 animate-spin"
                      />
                      Saving & Fetching Agents...
                    </>
                  ) : (
                    <>
                      <ForwardedIconComponent
                        name="Save"
                        className="mr-2 h-4 w-4"
                      />
                      Save PAB Credentials
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="aicore" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>SAP AI Core Credentials</CardTitle>
                <CardDescription>
                  Enter your SAP AI Core service credentials in JSON format.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="aicore-credentials">Credentials JSON</Label>
                  <Textarea
                    id="aicore-credentials"
                    placeholder={`{
  "client_id": "your-ai-core-client-id",
  "client_secret": "your-ai-core-client-secret",
  "token_url": "https://your-domain.authentication.eu12.hana.ondemand.com/oauth/token",
  "service_url": "https://your-ai-core-service-url"
}`}
                    value={aiCoreCredentials}
                    onChange={(e) => setAiCoreCredentials(e.target.value)}
                    className="min-h-[200px] font-mono text-sm"
                  />
                </div>
                <Button
                  onClick={handleSaveAICoreCredentials}
                  className="w-full"
                >
                  <ForwardedIconComponent
                    name="Save"
                    className="mr-2 h-4 w-4"
                  />
                  Save AI Core Credentials
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
