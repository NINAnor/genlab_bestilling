# Technical Notes

## Database
Postgres is used as database

### GenlabID
The generation of the GenlabID is pretty complex, the requirements are the following:
- The code should be partitioned by (Year, Species) + a running number
- The code should be short
- Each sample can be cloned, leading to a sub-sequence

This is achived using:
- a postgres function (see genlab_bestilling/migrations/0001) that creates a sequence specific for that partition if not exists (using the species and year as name of the sequence) and retrieves the name of such sequence, and a function that generates the code invoking `nextval` on the appropriate sequence.
- only samples that are confirmed will get a GenlabID
- ids are generated in a queue, by a worker with concurrency 1 to allow the manual rollback of the sequence in case of error

## Frontend
Frontend is implemented in React, the frontend scripts are loaded by django templates and communicate with the backend using a REST API.
