import { Button } from "@/components/ui/button";
import { LogIn } from "lucide-react";

export default async function Home() {
    return (
        <>
            <main className="flex min-h-[100dvh] flex-col items-center justify-center bg-background px-4 py-12 sm:px-6 lg:px-8">
                <div className="mx-auto text-center">
                    <h1 className="text-4xl font-semi-bold tracking-tight text-foreground sm:text-5xl">
                        Welcome to Code Carbon!
                    </h1>
                    <p className="mt-4 text-lg text-muted-foreground">
                        Get started by signing in with your preferred service.
                    </p>
                    <div className="mt-6">
                        <a
                            href={`${process.env.NEXT_PUBLIC_API_URL}/auth/login?redirect=${process.env.NEXT_PUBLIC_BASE_URL}/home?auth=true`}
                        >
                            <Button className="w-full max-w-[300px]">
                                <LogIn className="mr-2 h-5 w-5" />
                                Sign in or create an account
                            </Button>
                        </a>
                    </div>
                </div>
            </main>
            <footer className="mx-auto text-center mb-4 text-sm text-muted-foreground space-y-2">
                <p>
                    New to Code Carbon? Learn more at{" "}
                    <a
                        href="https://codecarbon.io"
                        className="text-primary underline"
                    >
                        codecarbon.io
                    </a>
                    .
                </p>
                <p>
                    Want to contribute? Visit our{" "}
                    <a
                        href="https://github.com/mlco2/codecarbon"
                        className="text-primary underline"
                    >
                        GitHub repository
                    </a>
                    .
                </p>
            </footer>
        </>
    );
}
