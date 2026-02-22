import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import Loader from "@/components/loader";
import { Organization } from "@/api/schemas";
import { fetcher } from "@/api/swr";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import useSWR from "swr";

export default function HomePage() {
  const navigate = useNavigate();
  const [redirecting, setRedirecting] = useState(true);

  const { data: organizations, error } = useSWR<Organization[]>(
    "/organizations",
    fetcher,
    { revalidateOnFocus: false },
  );

  useEffect(() => {
    if (organizations && organizations.length > 0) {
      const defaultOrgId = organizations[0].id;
      try {
        localStorage.setItem("organizationId", defaultOrgId);
        localStorage.setItem("organizationName", organizations[0].name || "");
      } catch (error) {
        console.error("Error writing to localStorage:", error);
      }
      navigate(`/${defaultOrgId}`);
    } else if ((organizations && organizations.length === 0) || error) {
      setRedirecting(false);
    }
  }, [organizations, navigate, error]);

  if (redirecting) {
    return <Loader />;
  }

  return (
    <div className="container mx-auto p-4">
      <Card className="mx-auto">
        <CardHeader>
          <CardTitle>Get Started</CardTitle>
          <CardDescription>
            You can do that by installing the command line tool and running:
            <span className="block whitespace-pre-wrap border-l-2 border-primary break-words pl-4 m-4">
              codecarbon login <br />
              codecarbon config <br />
              codecarbon monitor
            </span>
            You&apos;ll then need to get the project id from the config file
            before generating the token.
            <br />
            You can then write the token in the config file and start
            monitoring. <br />
            <br />
            For more information, please refer to the documentation:
            <br />
            <a
              href="https://mlco2.github.io/codecarbon/usage.html"
              target="_blank"
            >
              https://mlco2.github.io/codecarbon/usage.html
            </a>
          </CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}
