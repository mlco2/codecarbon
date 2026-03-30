/** @type {import('next').NextConfig} */
const nextConfig = {
    output: "standalone",
    experimental: {
        optimizePackageImports: ["lucide-react", "recharts", "date-fns"],
    },
};

export default nextConfig;
