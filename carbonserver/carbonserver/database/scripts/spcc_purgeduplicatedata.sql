/*  
   spname        : spcc_purgedata
   goal          : create a tempory table to display records where there are any information on runs and emissions
                   delete all records linked by their key referenced  uuid  from an organizations unused.
   date          : 20240222
   version      : 01 
   comment       : 01 : initialize procedure spcc_purgeduplicatedata 
   created by    : MARC ALENCON 
   modified by   : MARC ALENCON      
*/ 

/* Comments & Comments :  
   	        sample for camille organization to delete :  
			Delete from public.experiments
			where project_id in ('6a121901-5fa6-4e37-9ad8-8ec86941feb5');

			delete from public.projects
			where team_id='d8e80b93-50f8-42fc-9280-650954415dbb';

			delete from teams 
			where organization_id='92570ce9-1f90-4904-b9e6-80471963b740'; 					 

			delete from organizations 
			where id ='92570ce9-1f90-4904-b9e6-80471963b740';
*/

CREATE OR REPLACE PROCEDURE public.spcc_purgeduplicatedata()
LANGUAGE 'plpgsql'
AS $BODY$

BEGIN -- Start of  transaction 

-- Création de la table temporaire
CREATE TEMP TABLE temp_table (
    nb int , 
	orga_id uuid ,
    team_id uuid , 
	project_id uuid ,
	experiment_id uuid , 
	run_id uuid , 
	emission_id uuid
);


-- get distinct id from tables experiments ,  projects , teams , organizations 
-- Insertion des données de la table source vers la table temporaire
INSERT INTO temp_table (nb, orga_id,team_id,project_id,experiment_id,run_id,emission_id )
SELECT count(*) as nb , o.id as orga_id,t.id as team_id, p.id as project_id, e.id as experiment_id ,  r.id as run_id , em.id as emission_id 
from public.organizations o
left outer join public.teams t on o.id=t.organization_id
left outer join public.projects p on t.id = p.team_id
left outer join public.experiments e on p.id = e.project_id
left outer join public.runs r on e.id = r.experiment_id
left outer join public.emissions em on r.id = em.run_id 
where  r.id is null and em.id is null 
group by  o.id,t.id, p.id,e.id,r.id ,em.id;


/*
select count(*) from temp_table -- 752
select count(*) from  experiments -- 1376  / 653
select count(*) from  projects  -- 41 /21 
select count(*) from  teams    -- 26 /15
select count(*) from  organizations --25 /12 
*/

DO $$
DECLARE
    row_data RECORD;
	-- variables techniques .
	a_count integer;
	v_state TEXT;
	v_msg   TEXT;
	v_detail TEXT; 
	v_hint   TEXT;
	v_context TEXT; 
	
	
BEGIN
    GET DIAGNOSTICS a_count = ROW_COUNT;
	RAISE NOTICE '------- START -------';
    FOR row_data IN SELECT orga_id, team_id,project_id,experiment_id,run_id,emission_id  FROM temp_table LOOP
	    
         a_count = a_count +1;
		 
         --RAISE NOTICE '------- START -------';
		 RAISE NOTICE 'The rows affected by A=%',a_count;
		 RAISE NOTICE 'Delete experiments which contains any runs affected'		 
		 delete FROM public.experiments e 
                  where e.id not in ( select r.experiment_id
				                       from	runs r 
			        )
	     and e.project_id =row_data.project_id;
		 
		 
		 RAISE NOTICE '--------------';
		 RAISE NOTICE 'Delete projects which contains any experiments affected'
		 
		 delete FROM public.projects p 
                 where p.id not in ( select e.project_id
				                       from	experiments e 
			        )
	     and p.team_id =row_data.team_id;
		 
         
		 RAISE NOTICE '--------------';
		 RAISE NOTICE 'Delete teams which contains any project affected '
		 DELETE from teams t    
         where t.id not in (select p.team_id from projects p)
		 and t.organization_id =row_data.orga_id;
		  
 
		 
		 RAISE NOTICE '--------------';
		 RAISE NOTICE 'Delete organizations which contains any teams affected'
		 DELETE from organizations o    
         where o.id not in (select t.organization_id from teams t )
		 and o.id = row_data.orga_id;
		 
    END LOOP;
	RAISE NOTICE '-------- END ------';
EXCEPTION
    WHEN others THEN
	  
        -- Handling error:Cancelled transaction when error produced
        ROLLBACK;
		get stacked diagnostics
		  v_state = returned_sqlstate,
		  v_msg   = message_text,
		  v_detail = pg_exception_detail,
		  v_hint   = pg_exception_hint,
          v_context = pg_exception_context;
        RAISE NOTICE E'Got exception : 
		state : % 
		message : % 
		detail : % 
		hint  : % 
		context : % ', v_state, v_msg, v_detail, v_hint, v_context ;		
END $$;

DROP TABLE temp_table;

COMMIT; -- end of transaction 
END;
$BODY$;




