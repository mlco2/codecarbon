export async function GET(): Promise<Response> {
  try {
    const res = await fetch(`${process.env.API_URL}/organizations`, {
      next: { revalidate: 60 }, // Revalidate every minute
    });

    if (!res.ok) {
      // This will activate the closest `error.js` Error Boundary
      throw new Error(res.statusText);
    }

    return Response.json(await res.json());
  } catch (error) {
    console.error("API Error:", error);

    if (error instanceof Error) {
      return Response.json({ error: error.message });
    }
    return Response.json({ error: "An unknown error occurred" });
  }
}
