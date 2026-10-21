"""Derived SQLite index only; original job rows are never rewritten."""
from django.db import migrations

CREATE = [
    """CREATE VIRTUAL TABLE jobs_job_search USING fts5(
        title, company_name, location, description, requirements,
        content='jobs_job', content_rowid='id',
        tokenize='unicode61 remove_diacritics 2', prefix='2 3 4')""",
    """CREATE TRIGGER jobs_search_insert AFTER INSERT ON jobs_job BEGIN
        INSERT INTO jobs_job_search(rowid,title,company_name,location,description,requirements)
        VALUES(new.id,new.title,new.company_name,new.location,new.description,new.requirements);
    END""",
    """CREATE TRIGGER jobs_search_delete AFTER DELETE ON jobs_job BEGIN
        INSERT INTO jobs_job_search(jobs_job_search,rowid,title,company_name,location,description,requirements)
        VALUES('delete',old.id,old.title,old.company_name,old.location,old.description,old.requirements);
    END""",
    """CREATE TRIGGER jobs_search_update AFTER UPDATE OF title,company_name,location,description,requirements ON jobs_job BEGIN
        INSERT INTO jobs_job_search(jobs_job_search,rowid,title,company_name,location,description,requirements)
        VALUES('delete',old.id,old.title,old.company_name,old.location,old.description,old.requirements);
        INSERT INTO jobs_job_search(rowid,title,company_name,location,description,requirements)
        VALUES(new.id,new.title,new.company_name,new.location,new.description,new.requirements);
    END""",
    "INSERT INTO jobs_job_search(jobs_job_search) VALUES('rebuild')",
]


def create_index(apps, schema_editor):
    # see docs/CONCEPTS.md#job-full-text-search
    if schema_editor.connection.vendor != 'sqlite':
        raise RuntimeError('This search migration requires the reviewed SQLite deployment.')
    for statement in CREATE:
        schema_editor.execute(statement)


def drop_index(apps, schema_editor):
    for name in ('jobs_search_insert', 'jobs_search_delete', 'jobs_search_update'):
        schema_editor.execute('DROP TRIGGER IF EXISTS ' + name)
    schema_editor.execute('DROP TABLE IF EXISTS jobs_job_search')


class Migration(migrations.Migration):
    dependencies = [('jobs', '0010_application_send_authorization_schema')]
    operations = [migrations.RunPython(create_index, drop_index)]
