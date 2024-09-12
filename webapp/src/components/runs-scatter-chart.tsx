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
    return result.map((runReport: RunReport) => {
        return {
            runId: runReport.run_id,
            emissions: runReport.emissions,
            timestamp: runReport.timestamp,
            energy_consumed: runReport.energy_consumed,
            duration: runReport.duration,
        };
    });
}

export default async function RunsScatterChart() {
  const runsReportsData = await getRunEmissionsByExperiment(
    "bc1637d4-2066-412d-9ac8-0cb060402f22"
  )
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
          <XAxis dataKey="runId" name="Run Id" type="number">
            <Label value="Run Id" offset={0} position="insideBottom" />
          </XAxis>
          <YAxis dataKey="emissions" name="Emissions" type="number">
            <Label value="Emissions" angle={-90} position="insideLeft" />
          </YAxis>
            <Tooltip cursor={{ strokeDasharray: '3 3' }} formatter={(value, name, props) => {
                console.log(props.payload);
                const data = props.payload[0].payload;
                console.log(data)
                return [
                  `Run Id: ${data.runId}`,
                  `Emissions: ${data.emissions}`,
                  `Timestamp: ${data.timestamp}`,
                  `Energy Consumed: ${data.energy_consumed}`,
                  `Duration: ${data.duration}`,
                ];
              }} />
          <Scatter name="Emissions" data={runsReportsData} fill="#8884d8" />
        </ScatterChart>

      </CardContent>
      <CardFooter className="flex-col items-start gap-2 text-sm">
        <div className="flex gap-2 font-medium leading-none">
          Trending up by 5.2% this month <TrendingUp className="h-4 w-4" />
        </div>
        <div className="leading-none text-muted-foreground">
          Showing total emissions for the last 6 months
        </div>
      </CardFooter>
    </Card>
  )
}
