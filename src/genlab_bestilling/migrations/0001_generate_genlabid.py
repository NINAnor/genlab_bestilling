# Generated by Django 5.1.3 on 2024-12-03 07:43

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = []

    operations = [
        migrations.RunSQL(
            """
            CREATE or replace FUNCTION get_genlab_sequence_name(species_code varchar, year integer) RETURNS varchar
                LANGUAGE plpgsql
                AS $$
            declare seq_name varchar;
            begin
            seq_name = format('seq_G%s%s', year, species_code);
            execute format('create sequence if not exists %s', seq_name);
            return seq_name;
            end
            $$;

            CREATE or replace FUNCTION get_replica_sequence_name(genlab_id varchar) RETURNS varchar
                LANGUAGE plpgsql
                AS $$
            declare seq_name varchar;
            begin
            seq_name = format('rep_%s', genlab_id);
            execute format('create sequence if not exists %s', seq_name);
            return seq_name;
            end
            $$;

            CREATE or replace FUNCTION generate_genlab_id(species_code varchar, year integer) RETURNS varchar
                LANGUAGE plpgsql
                AS $$
            begin
            return 'G' || year % 100 || species_code || LPAD(nextval(get_genlab_sequence_name(species_code, year))::text, 5, '0');
            end
            $$;

            CREATE or replace FUNCTION generate_replica(genlab_id varchar) RETURNS varchar
                LANGUAGE plpgsql
                AS $$
            begin
            return genlab_id || CHR(64 + nextval(get_replica_sequence_name(genlab_id))::integer);
            end
            $$;
        """,
            """
            DROP FUNCTION IF EXISTS get_genlab_sequence_name(species_code varchar, year integer);
            DROP FUNCTION IF EXISTS get_replica_sequence_name(genlab_id varchar);
            DROP FUNCTION IF EXISTS generate_genlab_id(species_code varchar, year integer);
            DROP FUNCTION IF EXISTS generate_replica(genlab_id varchar);
        """,
        )
    ]