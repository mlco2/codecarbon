import { TrendingUp } from "lucide-react"
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Label } from 'recharts';

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

const chartData = [
  { runId: 1, emissions: 20 },
  { runId: 2, emissions: 35 },
  { runId: 3, emissions: 18 },
  { runId: 4, emissions: 42 },
  { runId: 5, emissions: 27 },
];

export function RunsScatterChart() {
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
          <CartesianGrid />
          <XAxis dataKey="runId" name="Run Id" type="string">
            <Label value="Run Id" offset={0} position="insideBottom" />
          </XAxis>
          <YAxis dataKey="emissions" name="Emissions" type="float">
            <Label value="Emissions" angle={-90} position="insideLeft" />
          </YAxis>
          <Tooltip cursor={{ strokeDasharray: '3 3' }} />
          <Scatter name="Emissions" data={chartData} fill="#8884d8" />
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
