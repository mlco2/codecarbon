import { Terminal } from "lucide-react";
import { Alert, AlertTitle, AlertDescription } from "./ui/alert";

export default function ErrorMessage() {
  return (
    <Alert className="border-none">
      <Terminal className="h-4 w-4" />
      <AlertTitle>An error occurred </AlertTitle>
      <AlertDescription>
        Please try again later or contact support.
      </AlertDescription>
    </Alert>
  );
}
