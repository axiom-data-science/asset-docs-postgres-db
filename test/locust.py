#!python
# coding=utf-8
import os
from locust import HttpUser, task, between
import urllib
import pathlib
import json
import logging

this_dir = pathlib.Path( __file__ ).parent

single_pixel_path = this_dir / 'single_pixel.jpg'

single_pixel_bytes = single_pixel_path.read_bytes()

ACCESS_TOKEN = os.environ.get( 'ACCESS_TOKEN', None )
ASSET_DOCS_POSTGREST_URL = os.environ.get( 'ASSET_DOCS_HOST', 'http://postgrest:3000' )

if not ACCESS_TOKEN:
    raise Exception( "Must set ACCESS_TOKEN environment variable" )

if not ASSET_DOCS_POSTGREST_URL:
    raise Exception(
        "Must set ASSET_DOCS_POSTGREST_URL environment variable to non-empty value"
    )


yuge_document_set=[]

WAIT=1.0

for i in range( 1_000 ):

    yuge_document_set.append(
        {
            "type": "bulk_upserted_doc",
            "data": {
                "value": i
            }
        }
    )

class LocustUser(HttpUser):

    wait_time = between( (WAIT + 0.1), (WAIT + 0.2) )

    host = ASSET_DOCS_POSTGREST_URL
    # host = 'https://stage-asset-docs-postgrest.srv.axds.co'

    @task
    def test_create_new_document(self):

        object_type_get_resp = self.client.get(
            "/object_type"
        )

        try:
            object_type_get_resp.raise_for_status()
        except Exception as exc:
            logging.warning( json.dumps( object_type_get_resp.json(), indent=2 ) )
            raise exc

        object_types = object_type_get_resp.json()

        default_object_type = object_types[0]

        # We'll do it live
        # collab_schema_path = this_dir / 'COLLAB-metadata-schema.json'
        # collab_schema_dict = json.loads( collab_schema_path.read_text() )

        # collab_station_path = this_dir / 'COLLAB-station.json'
        # collab_station_dict = json.loads( collab_station_path.read_text() )

        post_resp = self.client.post(
            "/document_for_update",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {ACCESS_TOKEN}"
            },
            json={
                "label": 'testing testing',
                "data": {
                    "$ref": "http://homestarrunner.com"
                },
                # system type... document file?
                "object_type_uuid": default_object_type['uuid'],
                # "json_schema": collab_schema_dict
            }
        )

        try:
            post_resp.raise_for_status()
        except Exception as exc:
            logging.warning( json.dumps( post_resp.json(), indent=2 ) )
            raise exc

    @task
    def test_get_documents_for_upload(self):
        get_count_resp = self.client.get(
            "/document_for_update",
            headers={
                "Authorization": f"Bearer {ACCESS_TOKEN}"
            },
            params={
                "select": "count()"
            },
            name="document_for_update"
        )

        get_count_resp.raise_for_status()

    @task
    def test_upload_and_then_download(self):
        post_resp = self.client.post(
            "/rpc/upload_document_file",
            headers={
                "Content-Type": "application/octet-stream",
                "Content-Disposition": f'filename="{single_pixel_path.name}"',
                "Authorization": f"Bearer {ACCESS_TOKEN}"
            },
            data=single_pixel_bytes
        )

        try:
            post_resp.raise_for_status()
        except:
            logging.warning(
                f"ERROR: {json.dumps(post_resp.json(), indent=2)}"
            )

        return_uuid = post_resp.json()

        get_resp = self.client.get(
            "/rpc/get_document_file",
            headers={
                "Content-Type": "application/octet-stream",
                "Authorization": f"Bearer {ACCESS_TOKEN}"
            },
            params={
                "uuid": return_uuid,
            },
            name="/rpc/get_document_file",
        )

        get_resp.raise_for_status()

    # @task
    # def test_bulk_upsert(self):

    #     initial_post_resp = self.client.post(
    #         "/document",
    #         headers={
    #             "Content-Type": "application/json",
    #             "Authorization": f"Bearer {ACCESS_TOKEN}",
    #             "Prefer": "return=representation"
    #         },
    #         json=yuge_document_set,
    #         name="document_inital_insert_post"
    #     )

    #     initial_post_resp.raise_for_status()

    #     initial_post_resp_json = initial_post_resp.json()

    #     logging.warning(
    #         f"bulk insert return len: {len( initial_post_resp_json )}"
    #     )

    #     for x in initial_post_resp_json:
    #         x['data']['value'] = 999

    #     upsert_post_resp = self.client.post(
    #         "/document",
    #         headers={
    #             "Content-Type": "application/json",
    #             "Authorization": f"Bearer {ACCESS_TOKEN}",
    #             "Prefer": "return=minimal,resolution=merge-duplicates"
    #         },
    #         params={
    #             "columns": "uuid,data",
    #         },
    #         json=initial_post_resp_json,
    #         name="document_upsert_post"
    #     )

    #     upsert_post_resp.raise_for_status()


    @task
    def test_create_new_document_with_geometry(self):

        object_type_get_resp = self.client.get(
            "/object_type",
            params={
                "slug": "eq.dummy_object_type"
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Prefer": "return=representation"
            },
            name="get_object_type"
        )

        object_type_get_resp.raise_for_status()

        dummy_object_type = next( iter( object_type_get_resp.json() ), None )

        if dummy_object_type is None:

            new_object_type_get_resp = self.client.post(
                "/object_type",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {ACCESS_TOKEN}",
                    "Prefer": "return=representation,resolution=ignore-duplicates"
                },
                json={
                    "label": "dummy object description",
                    "slug": "dummy_object_type",
                },
                name="post_object_type"
            )

            try:
                new_object_type_get_resp.raise_for_status()
            except Exception as exc:
                logging.warning( new_object_type_get_resp.text )
                raise exc

            dummy_object_type = next( iter( new_object_type_get_resp.json() ), None )

        object_schema_get_resp = self.client.get(
            "/object_schema",
            params={
                "slug": "eq.dummy_object_schema"
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Prefer": "return=representation"
            },
            name="get_object_schema"
        )

        dummy_object_schema = None

        object_schema_get_resp.raise_for_status()

        dummy_object_schema = next( iter( object_schema_get_resp.json() ), None )

        if dummy_object_schema is None:
            new_object_schema_get_resp = self.client.post(
                "/object_schema",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {ACCESS_TOKEN}",
                    "Prefer": "return=representation,resolution=ignore-duplicates"
                },
                json={
                    "slug": "dummy_object_schema",
                    "label": "dummy object schema",
                    "object_type_uuid": dummy_object_type['uuid'],
                    "json_schema": {
                        "$schema": "http://json-schema.org/draft-07/schema#",
                        "title": "Dummy schema",
                        "type": "object",
                    }
                },
                name="post_object_schema"
            )

            try:
                new_object_schema_get_resp.raise_for_status()
            except Exception as exc:
                logging.warning( new_object_schema_get_resp.text )
                raise exc

            dummy_object_schema = next( iter( new_object_schema_get_resp.json() ), None )

        post_resp = self.client.post(
            "/document_for_update",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {ACCESS_TOKEN}"
            },
            json={
                "label": 'testing testing',
                "data": {
                    "hi": "there"
                },
                "object_type_uuid": dummy_object_type['uuid'],
                "geom": "SRID=4326;POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))"
            },
            name="post_new_document"
        )

        try:
            post_resp.raise_for_status()
        except Exception as exc:
            logging.warning( post_resp.text )
            raise exc

        buffered_intersect_resp = self.client.get(
            "/rpc/buffered_aoi_intersecting_docs",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {ACCESS_TOKEN}"
            },
            params={
                "aoi": 'SRID=4326;POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))',
            },
            name="get_buffered_aoi_intersecting_docs"
        )

        try:
            buffered_intersect_resp.raise_for_status()
        except Exception as exc:
            logging.warning( buffered_intersect_resp.text )
            raise exc

        ret = next( iter( buffered_intersect_resp.json() ), None )

        logging.warning(
            f"# intersecting documents:{len(ret['docs'])}"
        )

    @task
    def test_create_new_documents_with_relationship(self):

        object_type_get_resp = self.client.get(
            "/object_type",
            params={
                "slug": "eq.dummy_object_type"
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Prefer": "return=representation"
            },
            name="get_object_type"
        )

        object_type_get_resp.raise_for_status()

        dummy_object_type = next( iter( object_type_get_resp.json() ), None )

        if dummy_object_type is None:

            new_object_type_get_resp = self.client.post(
                "/object_type",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {ACCESS_TOKEN}",
                    "Prefer": "return=representation,resolution=ignore-duplicates"
                },
                json={
                    "label": "dummy object description",
                    "slug": "dummy_object_type",
                },
                name="post_object_type"
            )

            try:
                new_object_type_get_resp.raise_for_status()
            except Exception as exc:
                logging.warning( new_object_type_get_resp.text )
                raise exc

            dummy_object_type = next( iter( new_object_type_get_resp.json() ), None )

        object_schema_get_resp = self.client.get(
            "/object_schema",
            params={
                "slug": "eq.dummy_object_schema"
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Prefer": "return=representation"
            },
            name="get_object_schema"
        )

        dummy_object_schema = None

        object_schema_get_resp.raise_for_status()

        dummy_object_schema = next( iter( object_schema_get_resp.json() ), None )

        if dummy_object_schema is None:
            new_object_schema_get_resp = self.client.post(
                "/object_schema",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {ACCESS_TOKEN}",
                    "Prefer": "return=representation,resolution=ignore-duplicates"
                },
                json={
                    "slug": "dummy_object_schema",
                    "label": "dummy object schema",
                    "object_type_uuid": dummy_object_type['uuid'],
                    "json_schema": {
                        "$schema": "http://json-schema.org/draft-07/schema#",
                        "title": "Dummy schema",
                        "type": "object",
                    }
                },
                name="post_object_schema"
            )

            try:
                new_object_schema_get_resp.raise_for_status()
            except Exception as exc:
                logging.warning( new_object_schema_get_resp.text )
                raise exc

            dummy_object_schema = next( iter( new_object_schema_get_resp.json() ), None )

        first_post_resp = self.client.post(
            "/document_for_update",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Prefer": "return=representation,resolution=ignore-duplicates"
            },
            json={
                "label": 'related document 1',
                "data": {
                    "hi": "there"
                },
                "object_type_uuid": dummy_object_type['uuid'],
            },
            name="post_first_related_document"
        )

        try:
            first_post_resp.raise_for_status()
        except Exception as exc:
            logging.warning( first_post_resp.text )
            raise exc

        dummy_first_document = next( iter( first_post_resp.json() ), None )

        second_post_resp = self.client.post(
            "/document_for_update",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Prefer": "return=representation,resolution=ignore-duplicates"
            },
            json={
                "label": 'related document 2',
                "data": {
                    "hi": "there"
                },
                "object_type_uuid": dummy_object_type['uuid'],
            },
            name="post_second_related_document"
        )

        try:
            second_post_resp.raise_for_status()
        except Exception as exc:
            logging.warning( second_post_resp.text )
            raise exc

        dummy_second_document = next( iter( second_post_resp.json() ), None )

        predicate_get_resp = self.client.get(
            "/predicate",
            params={
                "predicate": "eq.has_parent"
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Prefer": "return=representation"
            },
            name="get_has_parent_predicate"
        )

        try:
            predicate_get_resp.raise_for_status()
        except Exception as exc:
            logging.warning( predicate_get_resp.text )
            raise exc


        dummy_has_parent_predicate = next( iter( predicate_get_resp.json() ), None )

        relate_post_resp = self.client.post(
            "/relationship",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {ACCESS_TOKEN}"
            },
            json={
                "from_document_uuid": dummy_first_document['uuid'],
                "to_document_uuid": dummy_second_document['uuid'],
                # Empty for now
                "data": {},
                "predicate_uuid": dummy_has_parent_predicate['uuid'],
            },
            name="post_relate_two_documents"
        )

        try:
            relate_post_resp.raise_for_status()
        except Exception as exc:
            logging.warning( relate_post_resp.text )
            raise exc


        with self.client.post(
            "/relationship",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {ACCESS_TOKEN}"
            },
            json={
                "from_document_uuid": dummy_second_document['uuid'],
                "to_document_uuid": dummy_first_document['uuid'],
                # Empty for now
                "data": {},
                "predicate_uuid": dummy_has_parent_predicate['uuid'],
            },
            name="post_inverse_relate_two_documents",
            catch_response=True
        ) as inverse_relate_post_resp:

            try:
                assert 400 == inverse_relate_post_resp.status_code, \
                    (
                        "Must return 400 Bad Request on inverse attempt, got "
                        f"{inverse_relate_post_resp.status_code} status instead"
                    )

                inverse_relate_post_resp.success()
            except Exception as exc:
                logging.warning( inverse_relate_post_resp.text )
                raise exc
