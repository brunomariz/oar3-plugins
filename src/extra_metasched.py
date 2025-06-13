# coding: utf-8
"""Extra metascheduling functions which can be called between each queue handling"""

from oar.lib.globals import init_config, get_logger
from oar.lib.models import Resource
from oar.lib.job_handling import set_job_state

config = init_config()
logger = get_logger("oar-plugins.custom_extra_metasched")


def extra_metasched_default(
    db_session,
    prev_queue,
    plt,
    scheduled_jobs,
    all_slot_sets,
    job_security_time,
    queue,
    initial_time_sec,
    extra_metasched_config,
):
    logger.info("plugin successfully called ;)")
    pass


def extra_metasched_logger(
    db_session,
    prev_queue,
    plt,
    scheduled_jobs,
    all_slot_sets,
    job_security_time,
    queue,
    initial_time_sec,
    extra_metasched_config,
):
    logger.info("plugin successfully called ;)")


def extra_metasched_foo(
    db_session,
    prev_queue,
    plt,
    scheduled_jobs,
    all_slot_sets,
    job_security_time,
    queue,
    initial_time_sec,
    extra_metasched_config,
):

    if prev_queue is None:
        # set first resource deployable
        first_id = db_session.query(Resource).first().id
        db_session.query(Resource).filter(Resource.id == first_id).update(
            {Resource.deploy: "YES"}, synchronize_session=False
        )
        db_session.commit()


def extra_metasched_load_balancer(
    db_session,
    prev_queue,
    plt,
    scheduled_jobs,
    all_slot_sets,
    job_security_time,
    queue,
    initial_time_sec,
    extra_metasched_config,
):
    # - For all jobs in the queue
    #   - Check which resource has the least ammount of jobs already assigned to it (using scheduled_jobs)
    #   - Assign the job to this resource with least jobs

    # Imported inside of function because there may be a better way to do things, in which case this import should be removed

    from procset import ProcSet
    # Temporary solution to get list of resources from procset.
    # Use _flatten generator
    def procset2list(procset):

        procset_lower_bound = procset._itvs[0][0]
        procset_upper_bound = procset._itvs[-1][-1]

        procset_list = []
        for i in range(procset_lower_bound, procset_upper_bound + 1):
            aux = ProcSet(i)
            if aux.intersection(procset):
                procset_list.append(i)

        return procset_list

    # Jobs in queue
    waiting_jobs, waiting_jids, nb_waiting_jobs = plt.get_waiting_jobs(
        ["default"], session=db_session
    )
    # Resources
    resource_set = plt.resource_set(db_session, config)

    resource_set_ids = resource_set.hierarchy["resource_id"]

    # job_security_time = int(config["SCHEDULER_JOB_SECURITY_TIME"])
    # plt.get_data_jobs(
    #     db_session, waiting_jobs, waiting_jids, resource_set, job_security_time
    # )

    assigned_jobs = {}

    # Initialize resource_usage_count
    resource_usage_count = {}
    for resource_id in resource_set_ids:
        resources = procset2list(resource_id)
        for resource in resources:
            resource_usage_count[resource] = 0
    
    for waiting_job in waiting_jobs.values():
        # For every job in scheduled_jobs, check which resource it's assigned to, and increase a counter
        for job in scheduled_jobs:
            job_resources = procset2list(job.res_set)
            for job_resource in job_resources:
                resource_usage_count[job_resource] += 1

        # Get the resource with the smallest counter
        resources_sorted_by_usage = sorted(
            resource_usage_count, key=lambda i: resource_usage_count[i]
        )

        if len(resources_sorted_by_usage) > 0:
            smallest_usage_resource_id = resources_sorted_by_usage[0]
            smallest_usage_resource = [
                    resource
                    for resource in resource_set.hierarchy["resource_id"]
                    if str(resource) == str(smallest_usage_resource_id)
            ][0]
        else:
            smallest_usage_resource = resource_set.hierarchy["resource_id"][-1]


        # Assign the first job in waiting jobs to this resource
        # (mld_id, _, hy_res_rqts) = waiting_job.mld_res_rqts[0]
        # import pdb

        # pdb.set_trace()
        waiting_job.moldable_id = waiting_job.id
        waiting_job.start_time = initial_time_sec
        waiting_job.res_set = smallest_usage_resource
        assigned_jobs[waiting_job.id] = waiting_job
        set_job_state(db_session, config, waiting_job.id, "toLaunch")


        smallest_usage_resource_id = int(str(smallest_usage_resource))
        if smallest_usage_resource_id in resource_usage_count:
            resource_usage_count[smallest_usage_resource_id] += 1
        else:
            resource_usage_count[smallest_usage_resource_id] = 1
        



    plt.save_assigns(db_session, assigned_jobs, resource_set)

    print("WATING JOBS:")
    print(waiting_jobs)
    print("SCHEDULED JOBS:")
    print(scheduled_jobs)
    print("RESOURCE SET")
    print(resource_set.hierarchy)
    print("RESOURCE USAGE COUNT")
    print(resource_usage_count)

