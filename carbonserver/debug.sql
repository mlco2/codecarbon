SELECT * FROM public.projects

select * from emissions where run_id='3ef0a8d4-fec8-433b-b483-93d6f054561f'
order by TIMESTAMP

select p.name as "Project Name", e.id as "Experiment ID", e.name as "Experiment Name", r.id as "Run ID", r.timestamp, count(em.id) as "Emissions count", max(em.duration) as "Max duration", avg(em.duration) as "Mean duration", max(em.duration)/3600 as "Durée en H", max(em.emissions_sum),avg(em.emissions_sum), sum(em.emissions_sum)
from public.projects as p inner join public.experiments as e ON e.project_id = p.id
	INNER JOIN public.runs as r ON r.experiment_id = e.id
	INNER JOIN public.emissions as em ON em.run_id = r.id
where team_id = '01d31604-025d-4f0d-88e3-f3c2fa1e8aac'
GROUP BY p.name, e.id, e.name, r.id
ORDER BY count(em.id) DESC

/*
project_id 5ff9a6f1-b8f7-43ae-b17f-1f85ee1b2dde => Ben Computers

project_id LexImpact 225904ca-f741-477c-83f5-d61587d6286c

experiment_id 0bfa2432-efda-4656-bdb4-f72d15866b0b => DC5
experiment_id ea060644-5303-4a68-8fb2-d0902b269022 => DC2

*/
SELECT * FROM public.experiments
WHERE project_id='5ff9a6f1-b8f7-43ae-b17f-1f85ee1b2dde'
ORDER BY id ASC LIMIT 100

SELECT * FROM public.runs
WHERE experiment_id IN (SELECT id FROM public.experiments WHERE project_id='225904ca-f741-477c-83f5-d61587d6286c')
ORDER BY id ASC LIMIT 100

SELECT * FROM public.emissions
WHERE run_id IN (SELECT id FROM public.runs
				 	WHERE experiment_id IN (SELECT id FROM public.experiments
											WHERE project_id='225904ca-f741-477c-83f5-d61587d6286c'))
ORDER BY id ASC LIMIT 100

SELECT * FROM public.emissions
WHERE run_id IN (SELECT id FROM public.runs
				 	WHERE experiment_id IN (SELECT id FROM public.experiments
											WHERE project_id='5ff9a6f1-b8f7-43ae-b17f-1f85ee1b2dde'))
	AND timestamp < '2022-09-01'
ORDER BY timestamp ASC LIMIT 100

/*
DELETE FROM public.emissions
WHERE run_id IN (SELECT id FROM public.runs
				 	WHERE experiment_id IN (SELECT id FROM public.experiments
											WHERE project_id='5ff9a6f1-b8f7-43ae-b17f-1f85ee1b2dde'))
	AND timestamp < '2022-09-01'
*/




