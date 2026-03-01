import BreadcrumbHeader from "@/components/breadcrumb";
import CustomRow from "@/components/custom-row";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody } from "@/components/ui/table";
import { Organization, User } from "@/api/schemas";
import { fetcher } from "@/api/swr";
import { useParams } from "react-router-dom";
import { useState } from "react";
import { z } from "zod";
import { toast } from "sonner";
import useSWR, { mutate } from "swr";
import Loader from "@/components/loader";
import ErrorMessage from "@/components/error-message";

export default function MembersPage() {
  const { organizationId } = useParams<{ organizationId: string }>();
  const [isDialogOpen, setDialogOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const { data: users, error: fetchError, isLoading: usersLoading } = useSWR<User[]>(
    `/organizations/${organizationId}/users`,
    fetcher,
  );

  const { data: organization } = useSWR<Organization>(
    `/organizations/${organizationId}`,
    fetcher,
  );

  const form = { email: undefined as string | undefined };

  const emailSchema = z.object({
    email: z.string().email("Please enter a valid email address"),
  });

  async function addUser() {
    try {
      setIsLoading(true);
      const email = (
        document.getElementById("emailInput") as HTMLInputElement
      ).value;

      emailSchema.parse({ email });
      setError(null);

      const body = JSON.stringify({ email });
      const API_BASE = import.meta.env.VITE_API_URL;

      await toast
        .promise(
          fetch(`${API_BASE}/organizations/${organizationId}/add-user`, {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body,
          }).then(async (res) => {
            if (!res.ok) throw new Error("Failed to add user");
            return res.json();
          }),
          {
            loading: `Adding user ${email}...`,
            success: `User ${email} added successfully`,
            error: (err) => `${err.message}`,
          },
        )
        .unwrap();

      mutate(`/organizations/${organizationId}/users`);
      setDialogOpen(false);
    } catch (err) {
      if (err instanceof z.ZodError) {
        setError(err.errors[0].message);
      } else {
        setError(
          err instanceof Error ? err.message : "An error occurred",
        );
      }
    } finally {
      setIsLoading(false);
    }
  }

  if (usersLoading) {
    return <Loader />;
  }

  if (fetchError || !users) {
    return <ErrorMessage />;
  }

  return (
    <>
      <BreadcrumbHeader
        pathSegments={[
          {
            title: organization?.name || organizationId!,
            href: `/${organizationId}`,
          },
          { title: "Members", href: null },
        ]}
      />
      <div>
        <div className="container mx-auto p-4 md:gap-8 md:p-8">
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-2xl font-semi-bold">Members</h1>
            <Button
              disabled={isDialogOpen}
              onClick={() => setDialogOpen(true)}
            >
              + Add a member
            </Button>
          </div>
          {isDialogOpen && (
            <div className="flex flex-col gap-2 mb-6 p-6 rounded-md border border-white/30">
              <h2>Add member</h2>
              <Label htmlFor="emailInput">Email address</Label>
              <Input
                id="emailInput"
                placeholder="email"
                value={form.email}
                aria-invalid={!!error}
                aria-describedby={error ? "email-error" : undefined}
              />
              {error && (
                <p id="email-error" role="alert" className="text-sm text-destructive">{error}</p>
              )}
              <div className="flex justify-end gap-6">
                <Button
                  disabled={isLoading}
                  variant="outline"
                  onClick={() => {
                    form.email = undefined;
                    setDialogOpen(false);
                  }}
                >
                  Cancel
                </Button>
                <Button
                  onClick={() => addUser()}
                  disabled={isLoading}
                >
                  {isLoading ? "Adding..." : "Ok"}
                </Button>
              </div>
            </div>
          )}
          <Card>
            <Table>
              <TableBody>
                {users
                  .sort((a, b) =>
                    a.name.toLowerCase().localeCompare(b.name.toLowerCase()),
                  )
                  .map((user) => (
                    <CustomRow
                      key={user.id}
                      rowKey={user.id}
                      firstColumn={user.name}
                      secondColumn={user.email}
                    />
                  ))}
              </TableBody>
            </Table>
          </Card>
        </div>
      </div>
    </>
  );
}
