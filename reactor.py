import json
import sys
from attrdict import AttrDict
from requests.exceptions import HTTPError

from reactors.runtime import Reactor, agaveutils
from datacatalog.managers.pipelinejobs import Manager, ManagedPipelineJob

def main():
    rx = Reactor()
    mes = AttrDict(rx.context.message_dict)

    mongodb_conn = rx.settings.mongodb

    # ! This code fixes an edge case in JSON serialization
    if mes == {}:
        try:
            jsonmsg = json.loads(rx.context.raw_message)
            mes = AttrDict(jsonmsg)
        except Exception as exc:
            rx.on_failure('Failed to load JSON from message', exc)

    # Check incoming message against the default JSON schema
    try:
        rx.validate_message(mes, permissive=False)
    except Exception as exc:
        rx.on_failure('Failed to validate message to schema', exc)

    # Verify appId is known to Agave apps API. Requires the invoking
    # user has a tenant admin role unless the appId is public
    agave_job = mes.get('job_definition')
    agave_appid = agave_job.get('appId')
    agave_app_details = None
    job_params = mes.get('parameters')
    instanced_archive_path = mes.get('instanced', True)
    rx.logger.info(
        'Received request to manage execution of {}'.format(agave_appid))
    try:
        agave_app_details = rx.client.apps.get(appId=agave_appid)
    except HTTPError as http_err:
        rx.on_failure(
            '{} is not a known Agave application'.format(
                agave_appid), http_err)
    except Exception as generic_exception:
        rx.on_failure(
            'Failed to look up Agave application', generic_exception)

    # Look up the Pipeline record for this Agave appId.
    #
    # Note that this requires a convention where the standalone Agave app is
    # registered in the Pipelines system with pipeline.id == agave.app.id
    pipeline_uuid = None
    try:
        manager_stores = Manager.init_stores(mongodb_conn)
        pipeline_rec = manager_stores['pipeline'].find_one_by_id(id=agave_appid)
        if pipeline_rec is None:
            raise ValueError("No 'pipelines' record found in database")
        else:
            pipeline_uuid = pipeline_rec.get('uuid')
    except Exception as generic_exception:
        rx.on_failure('Failed to resolve appId {} to a Pipeline record'.format(
            agave_appid), generic_exception)

    def cancel_job(message='an error occurred', exception=None):
        """Helper function to cancel a failed job
        """
        fmt_message = 'PipelineJob {} canceled because {}'.format(
            job_uuid, message)
        try:
            job.cancel()
        except Exception as job_cancel_exception:
            rx.logger.warning(
                'Failed to cancel PipelineJob {} because {}'.format(
                    job_uuid, job_cancel_exception))

        rx.on_failure(fmt_message, exception)

    def fail_job(message='an error occurred', exception=None):
        """Helper function to fail a job
        """
        fmt_message = 'PipelineJob {} failed because {}'.format(
            job_uuid, message)
        try:
            job.fail(data={'message': message})
        except Exception as job_fail_exception:
            rx.logger.warning(
                'Unable to update PipelineJob state for {} because {}'.format(
                    job_uuid, job_fail_exception))

        rx.on_failure(fmt_message, exception)

    # Initialize the ManagedPipelineJob. It will be in the jobs collection
    # with a status of CREATED.
    job = None
    job_uuid = None
    try:
        job = ManagedPipelineJob(rx.settings.mongodb,
                                 rx.settings.pipelines.job_manager_id,
                                 rx.settings.pipelines.updates_nonce,
                                 pipeline_uuid=pipeline_uuid,
                                 data=mes.get('data', {}),
                                 session=rx.nickname,
                                 agent=rx.uid,
                                 task=rx.execid,
                                 instanced=instanced_archive_path,
                                 **job_params
                                 )
        job.setup(data=agave_job)
        job_uuid = job.uuid
    except Exception as generic_exception:
        if job is not None:
            cancel_job(message='Failed to set up ManagedPipelineJob',
                       exception=generic_exception)
        else:
            rx.on_failure('Failed to set up ManagedPipelineJob', generic_exception)

    # Extend the incoming Agave job definition to update the PipelineJob.
    # Set the archivePath and archiveSystem from the ManagedPipelineJob
    #
    # The former is accomplished by adding custom notifications built from
    # the job's 'callback' property, which was initialized on job.setup(). Any
    # pre-existing notifications (email, other callbacks) are preserved.

    try:
        if 'notifications' not in agave_job:
            agave_job['notifications'] = list()
        # for event in ('SUBMITTING', 'STAGING_JOB', 'RUNNING', 'ARCHIVING', 'ARCHIVING_FINIS', 'FINISHED', 'FAILED'):
            # Capture all Agave job states
            notification = {'event': '*',
                            'persistent': True,
                            'url': job.callback + '&status=${STATUS}&note=${JOB_ERROR}'}
            agave_job['notifications'].append(notification)

        agave_job['archiveSystem'] = job.archive_system
        agave_job['archivePath'] = job.archive_path
        agave_job['archive'] = True

    except Exception as generic_exception:
        cancel_job(
            message='Failed to prepare Agave job definition',
            exception=generic_exception)

    if rx.local:
        print(json.dumps(agave_job, indent=4))
        sys.exit(0)

    # Launch the Agave job
    agave_job_id = None
    try:
        resp = rx.client.jobs.submit(body=agave_job)
        agave_job_id = None
        if 'id' in resp:
            agave_job_id = resp['id']
        else:
            raise KeyError('Invalid response received from jobs.submit()')
    except HTTPError as h:
        http_err_resp = agaveutils.process_agave_httperror(h)
        fail_job(
            message='Encountered API error: {}'.format(http_err_resp),
            exception=HTTPError)
    except Exception as job_submit_exception:
        fail_job(message='Failed to launch {}'.format(
            agave_appid), exception=job_submit_exception)

    # Update the PipelineJob status
    #
    # This will create an entry in its history with an explicit link to
    # the job asset. If this doesn't succeed, we don't fail the job since
    # the expensive part (the Agave job) has been submitted.
    try:
        job_uri = job.canonicalize_job(agave_job_id)
        job.run(data={'job_link': job_uri})
    except Exception as job_update_exception:
        rx.logger.warning(
            'Unable to update status of job {} because {}'.format(
                job_uuid, job_update_exception))

    # If no other exit state has been encountered, report success
    rx.on_success('ManagedPipelineJob {} is managing Agave job {} ({} usec)'.format(
        job_uuid, agave_job_id, rx.elapsed()))


if __name__ == '__main__':
    main()
