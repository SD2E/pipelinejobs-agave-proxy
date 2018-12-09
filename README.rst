=========================
PIPELINE JOBS AGAVE PROXY
=========================

This Abaco actor is part of the PipelineJobs system. Its role is to provide a
generalized interface for running managed Agave jobs so that their outputs are
integrated with, and thus discoverable from, the Data Catalog.

Prequisites
-----------

Some external dependencies must be satisfied before jobs can be run:

# The Agave app itself must be architected to fit the PipelineJobs workflow
# The Agave-based application must be registered as a Data Catalog ``Pipeline``,
where the ``pipeline.id`` is identical to the Agave ``app.id``. The Agave app
must either be **public** or shared with the administrative user **sd2eadm**.
# The user who will request jobs needs special API key, which is different
from the TACC.cloud Oauth2 Bearer token that most users are accustomed to.

Launching a Managed Job
-----------------------

Start with an Agave job definition. Here's an example for a fictional app
``tacobot9000-0.1.0u1``.

.. code-block:: json

    {
      "appId": "tacobot9000-0.1.0u1",
      "name": "TACObot job",
      "inputs": {"file1": "agave://data.tacc.cloud/examples/tacobot/test1.txt"},
      "parameters": {"salsa": true, "avocado": false, "cheese": true},
      "maxRunTime": "01:00:00"
    }

This JSON structure is moved to a ``job_definition`` key in an enclosing JSON
document.

.. code-block:: json

    {
        "job_definition":
            {
                "appId": "tacobot9000-0.1.0u1",
                "name": "TACObot job",
                "inputs": {"file1": "agave://data.tacc.cloud/examples/tacobot/test1.txt"},
                "parameters": {"salsa": true, "avocado": false, "cheese": true},
                "maxRunTime": "01:00:00"
            }
        }
    }

.. note::  ``archive``,  ``archiveSystem``, ``archivePath`` keys will be ignored

Now, establish linkage to Data Catalog with a ``parameters`` key, which must
contain a valid value for one of the following:

- ``experiment_design_id``
- ``experiment_id``
- ``sample_id``
- ``measurement_id``

.. code-block:: json

    {
        "parameters": {
            "sample_id": "sample.black_mesa.incident123"
        },
        "job_definition":
            {
                "appId": "tacobot9000-0.1.0u1",
                "name": "TACObot job",
                "inputs": {"file1": "agave://data.tacc.cloud/examples/tacobot/test1.txt"},
                "parameters": {"salsa": true, "avocado": false, "cheese": true},
                "maxRunTime": "01:00:00"
            }
        }
    }

The contents of ``parameters`` combined with the ``uuid`` of for
``tacobot9000-0.1.0u1`` are used to create an distinct ``archivePath``. The
resulting path is extended by default with an instancing directory of the from
``adjective-animal-YYYYMMDDTHHmmssZ`` to prevent files from different jobs from
being overrwritten. To avoid the instancing directory being appended, pass
``"instanced": false`` in the job request message.

.. note:: The strictness of archivePath naming is needed to ensure that the job
    outputs can be indexed and registered with the Data Catalog.

.. note:: The JSONschema for a **Pipeline Jobs
Agave Proxy** job request is found in `message.jsonschema </message.jsonschema>`_.

Example Agave Job Definition
-----------------------------

Here is a example of the Agave job definition synthesized by **Pipeline Jobs
Agave Proxy**. Note the instanced archivePath and how the Agave notifications
system is configured to interact with the PipelineJobs system by messaging
its Job Manager reactor (``G46vjoAVzGkkz``) on key Agave job status changes.

.. code-block:: json

    {
        "appId": "tacobot9000-0.1.0u1",
        "inputs": {"file1": "agave://data.tacc.cloud/examples/tacobot/test1.txt"},
        "parameters": {"salsa": true, "avocado": false, "cheese": true},
        "maxRunTime": "01:00:00",
        "archive": true,
        "archiveSystem": "data.tacc.cloud",
        "archivePath": "/products/v2/103f877a7ab857d182807b75af4eab6e/106bd127e2d257acb9be11ed06042e68/eligible-awk-20181127T173243Z",
        "notifications": [
            {
                "event": "RUNNING",
                "persistent": true,
                "url": "https://api.tacc.cloud/actors/v2/G46vjoAVzGkkz/messages?x-nonce=TACC_60v1xkJzwQOgN&token=b81e44ed4815aa3c&uuid=10715620-ae90-5b92-bf4e-fbd491c21e03&status=${STATUS}"
            },
            {
                "event": "FINISHED",
                "persistent": true,
                "url": "https://api.tacc.cloud/actors/v2/G46vjoAVzGkkz/messages?x-nonce=TACC_60v1xkJzwQOgN&token=b81e44ed4815aa3c&uuid=10715620-ae90-5b92-bf4e-fbd491c21e03&status=${STATUS}"
            },
            {
                "event": "FAILED",
                "persistent": true,
                "url": "https://api.tacc.cloud/actors/v2/G46vjoAVzGkkz/messages?x-nonce=TACC_60v1xkJzwQOgN&token=b81e44ed4815aa3c&uuid=10715620-ae90-5b92-bf4e-fbd491c21e03&status=${STATUS}"
            }
        ]
    }

Job Life Cycle
--------------

Here is complete record from the Pipelines system showing how the information
from job creation and subsequent events is stored and discoverable. A few key
highlights:

- The top-level ``data`` field holds the original parameterization of the job
- Three events are noted in the ``history``: create, run, finish
- The actor and execution for the managing instance of **Pipeline Jobs
Agave Proxy** are available under ``agent`` and ``task``, respectively

.. code-block::json

    {
        "agent": "https://api.tacc.cloud/actors/v2/G46vjoAVzGkkz",
        "archive_path": "/products/v2/103f877a7ab857d182807b75af4eab6e/106bd127e2d257acb9be11ed06042e68/eligible-awk-20181127T173243Z",
        "archive_system": "data-sd2e-community",
        "data": {
            "appId": "urrutia-novel_chassis_app-0.1.0",
            "archivePath": "",
            "inputs": {
                "file1": "agave://data.tacc.cloud/examples/tacobot/test1.txt"
            },
            "maxRunTime": "01:00:00",
            "name": "TACObot job",
            "parameters": {
                "avocado": false,
                "cheese": true,
                "salsa": true
            }
        },
        "derived_from": [
            "1022efa3-4480-538f-a581-f1810fb4e0c3"
        ],
        "generated_by": [
            "106bd127-e2d2-57ac-b9be-11ed06042e68"
        ],
        "history": [
            {
                "data": {
                    "appId": "tacobot9000-0.1.0u1",
                    "inputs": {
                        "file1": "agave://data.tacc.cloud/examples/tacobot/test1.txt"
                    },
                    "maxRunTime": "01:00:00",
                    "name": "TACObot job",
                    "parameters": {
                        "avocado": false,
                        "cheese": true,
                        "salsa": true
                    }
                },
                "date": "2018-12-08T00:08:32.000+0000",
                "name": "create"
            },
            {
                "data": {
                    "appId": "tacobot9000-0.1.0u1",
                    "archive": true,
                    "archivePath": "/products/v2/103f877a7ab857d182807b75af4eab6e/106bd127e2d257acb9be11ed06042e68/eligible-awk-20181127T173243Z",
                    "archiveSystem": "data-tacc-cloud",
                    "batchQueue": "normal",
                    "created": "2018-12-07T18:08:37.000-06:00",
                    "endTime": null,
                    "executionSystem": "hpc-tacc-stampede2",
                    "id": "7381691026605150696-242ac11b-0001-007",
                    "inputs": {
                        "file1": "agave://data.tacc.cloud/examples/tacobot/test1.txt"
                    },
                    "lastUpdated": "2018-12-07T18:09:40.000-06:00",
                    "maxRunTime": "01:00:00",
                    "memoryPerNode": 1,
                    "name": "TACObot job",
                    "nodeCount": 1,
                    "outputPath": "tacobot/job-7381691026605150696-242ac11b-0001-007-TACObot-job",
                    "owner": "tacobot",
                    "parameters": {
                        "avocado": false,
                        "cheese": true,
                        "salsa": true
                    },
                    "processorsPerNode": 1,
                    "startTime": null,
                    "status": "RUNNING",
                    "submitTime": "2018-12-07T18:09:40.000-06:00"
                },
                "date": "2018-12-08T00:10:12.000+0000",
                "name": "run"
            },
            {
                "data": {
                    "appId": "tacobot9000-0.1.0u1",
                    "archive": true,
                    "archivePath": "/products/v2/103f877a7ab857d182807b75af4eab6e/106bd127e2d257acb9be11ed06042e68/eligible-awk-20181127T173243Z",
                    "archiveSystem": "data-tacc-cloud",
                    "batchQueue": "normal",
                    "created": "2018-12-07T18:08:37.000-06:00",
                    "endTime": null,
                    "executionSystem": "hpc-tacc-stampede2",
                    "id": "7381691026605150696-242ac11b-0001-007",
                    "inputs": {
                        "file1": "agave://data.tacc.cloud/examples/tacobot/test1.txt"
                    },
                    "lastUpdated": "2018-12-07T18:53:20.000-06:00",
                    "maxRunTime": "01:00:00",
                    "memoryPerNode": 1,
                    "name": "TACObot job",
                    "nodeCount": 1,
                    "outputPath": "tacobot/job-7381691026605150696-242ac11b-0001-007-TACObot-job",
                    "owner": "tacobot",
                    "parameters": {
                        "avocado": false,
                        "cheese": true,
                        "salsa": true
                    },
                    "processorsPerNode": 1,
                    "startTime": "2018-12-07T18:09:49.000-06:00",
                    "status": "FINISHED",
                    "submitTime": "2018-12-07T18:09:40.000-06:00"
                },
                "date": "2018-12-08T00:53:45.000+0000",
                "name": "finish"
            }
        ],
        "last_event": "finish",
        "pipeline_uuid": "106bd127-e2d2-57ac-b9be-11ed06042e68",
        "session": "casual-bass",
        "state": "FINISHED",
        "task": "https://api.tacc.cloud/actors/v2/G46vjoAVzGkkz/executions/Myp6wvklV0zgQ",
        "updated": "2018-12-08T00:53:45.000+0000",
        "uuid": "10743f9e-f5ae-5b4c-859e-6774ef4ab08b"
    }
