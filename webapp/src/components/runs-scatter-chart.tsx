import { TrendingUp } from "lucide-react"
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Label } from 'recharts';
import { RunReport } from "@/types/run-report";

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

type Params = {
    experimentId: string;
};
async function getRunEmissionsByExperiment(experimentId: string): Promise<RunReport[]> {
    console.log("From function: ", experimentId);
    const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/experiments/${experimentId}/runs/sums/`,
    );

    if (!res.ok) {
        // This will activate the closest `error.js` Error Boundary
        throw new Error("Failed to fetch data");
    }
    const result = await res.json();
    console.log("Runs from experiment: ", result)
    return result.map((runReport: RunReport) => {
        return {
            runId: runReport.run_id,
            emissions: runReport.emissions*1000,
            timestamp: runReport.timestamp,
            energy_consumed: runReport.energy_consumed*1000,
            duration: runReport.duration*10,
        };
    });
}

export default async function RunsScatterChart({
    params
  }: Readonly<{ params: Params }>) {
    const runsReportsData = await getRunEmissionsByExperiment(
        params.experimentId,
    );
      return (
        <Card>
          <CardHeader>
            <CardTitle>Scatter Chart - Emissions by Run Id</CardTitle>
            <CardDescription>January - June 2024</CardDescription>
          </CardHeader>
          <CardContent>
            <ScatterChart
              width={500}
              height={300}
              margin={{
                top: 20,
                right: 20,
                bottom: 20,
                left: 20,
              }}
            >
              <XAxis dataKey="timestamp" name="Timestamp" type="category">
                <Label value="Timestamp" offset={0} position="insideBottom" />
              </XAxis>
              <YAxis dataKey="emissions" name="Emissions" type="number">
                <Label value="Emissions" angle={-90} position="insideLeft" />
              </YAxis>
              <Scatter name="Emissions" data={runsReportsData} fill="#8884d8" />
            </ScatterChart>

          </CardContent>
        </Card>
      )
}
