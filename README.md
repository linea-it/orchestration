# Orchestration

Orchestration tool for the Brazilian IDAC applications.  

## Setup Enviroment

Clone the repository and access the directory:

```bash
git clone https://github.com/linea-it/orchestration.git  
cd orchestration
```

Create the directory for the database and the file that lists the available pipelines:
(currently we only have one test pipeline: **cross_lsdb_dev**)

```bash
mkdir db
cp pipelines/pipelines.yaml.template pipelines/pipelines.yaml 
```

Copy the file `docker-compose-development.yml` and rename to `docker-compose.yml`

```bash
cp docker-compose-development.yml docker-compose.yml
```

Create the environment variables file based on `env.template`.

```bash
cp env.template .env
```

Edit the files and change the variables according to your environment, in this first moment pay attention to the variables referring to the django database and connection (optional).

Check your linux user id with:

```bash
echo $UID
```

and update it in the `docker-compose.yml` file if necessary (if it is not the usual 1000).

Now start the backend service. As this is the first time, the base image will be pulled and the container will be built, this may take a while.

```bash
docker-compose up backend
```

If everything goes normally the last message will be something like `... spawned uWSGI worker x (pid: xx, cores: x)`

Shut down the backend service to change one of the Django variables.

To terminate use `CTRL + C` or `docker-compose stop`.

With the services turned off, let's run a command in the backend container to generate a SECRET for Django.

```bash
docker-compose run backend python -c "import secrets; print(secrets.token_urlsafe())"
```

This is the output of the command:

```bash
$ docker-compose run backend python -c "import secrets; print(secrets.token_urlsafe())"
[+] Running 1/0
 ✔ Container orchestration_test-rabbitmq-1  Running
6klbHhaeA6J2imKt9AVVgS5yl9mCWoiQqrfUV469DLA
```

Copy the generated key, replace the `SECRET_KEY` variable value in the `.env` file and uncomment it by removing the "#".


Create the Django superuser.

Enter in container:

```bash
docker-compose run backend /bin/bash
```

Insider container:

```bash
python manage.py migrate
python manage.py createsuperuser
```

After creating the administrator user, you can exit the container:

```bash
exit
```

Once this is done, the development environment setup process is complete.

Finally, to start the whole application:

``` bash
docker-compose up 
```

### How to use using Client Credential

The Client Credential grant is suitable for machine-to-machine authentication. You authorize your own service or worker to change a bank account transaction status to accepted.

Point your browser to <http://localhost/admin/oauth2_provider/application/add/> lets create an application.

- `client_id` and `client_secret` should be left unchanged.
- `user` should be your superuser numeric ID (if you are the only user, it should be = 1)
- `redirect_uris` should be left blank
- `client_type` should be set to confidential
- `authorization_grant_type` should be set to **'Client credentials'**
- `name` can be set to whatever you'd like
- checkbox for `Skip authorization` should remain unchecked
- `Algorithm`: keep the default option (No OIDC support)


WARNING!!!
Fill the form as show in the screenshot below, and before saving take note of **Client id** and **Client secret** we will use it in a minute.


![Adding new application](images/new_app.png)


With the container running, open a new terminal and export **Client id** and **Client secret** values as environment variable:

```bash
export ID=<your Client id >
export SECRET=<your Client secret>
```
For example: 

```bash
-export ID=axXSSBVuvOyGVzh4PurvKaq5MHXMm7FtrHgDMi4u
-export SECRET=1fuv5WVfR7A5BlF0o155H7s5bLgXlwWLhi3Y7pdJ9aJuCdl0XV5Cxgd0tri7nSzC80qyrovh8qFXFHgFAAc0ldPNn5ZYLanxSm1SI1rxlRrWUP591wpHDGa3pSpB6dCZ
```

The Client Credential flow is simpler than the Authorization Code flow.

We need to encode client_id and client_secret as HTTP base authentication encoded in base64 I use the following code to do that.

Open a Python prompt and execute: 
 
```python
import os
import base64
client_id=os.environ.get('ID') 
secret=os.environ.get('SECRET') 
credential="{0}:{1}".format(client_id, secret)
base64.b64encode(credential.encode("utf-8"))
``` 
The credential output should look like this: 

``` 
b'YXhYU1NCVnV2T3lHVnpoNFB1cnZLYXE1TUhYTW03RnRySGdETWk0dToxZnV2NVdWZlI3QTVCbEYwbzE1NUg3czViTGdYbHdXTGhpM1k3cGRKOWFKdUNkbDBYVjVDeGdkMHRyaTduU3pDODBxeXJvdmg4cUZYRkhnRkFBYzBsZFBObjVaWUxhbnhTbTFTSTFyeGxScldVUDU5MXdwSERHYTNwU3BCNmRDWg=='
```
Exit Python prompt and export the credential as an environment variable (just the string contents), for instance:

```bash
export CREDENTIAL=YXhYU1NCVnV2T3lHVnpoNFB1cnZLYXE1TUhYTW03RnRySGdETWk0dToxZnV2NVdWZlI3QTVCbEYwbzE1NUg3czViTGdYbHdXTGhpM1k3cGRKOWFKdUNkbDBYVjVDeGdkMHRyaTduU3pDODBxeXJvdmg4cUZYRkhnRkFBYzBsZFBObjVaWUxhbnhTbTFTSTFyeGxScldVUDU5MXdwSERHYTNwU3BCNmRDWg==
```

To start the Client Credential flow you call /token/ endpoint directly:

```bash
curl -X POST -H "Authorization: Basic ${CREDENTIAL}" -H "Cache-Control: no-cache" -H "Content-Type: application/x-www-form-urlencoded" http://localhost/o/token/ -d "grant_type=client_credentials"
```

To be easier to visualize:

```bash
curl -X POST \
    -H "Authorization: Basic ${CREDENTIAL}" \
    -H "Cache-Control: no-cache" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    http://localhost/o/token/ \
    -d "grant_type=client_credentials"
```

The OAuth2 provider will return the following response:

```bash
{
    "access_token": "PaZDOD5UwzbGOFsQr34LQ7JUYOj3yK",
    "expires_in": 36000,
    "token_type": "Bearer",
    "scope": "read write"
}
```

And with the access token you will be able to access the endpoints.

To trigger a 'Cross LSDB' test pipeline processing using the default configuration:

```bash
curl -X POST \
    -H "Authorization: Bearer <your access_token above>" \
    http://localhost/api/processes/ \
    -d "pipeline=cross_lsdb_dev&used_config="
```

For instance: 
```bash
curl -X POST \
    -H "Authorization: Bearer PaZDOD5UwzbGOFsQr34LQ7JUYOj3yK" \
    http://localhost/api/processes/ \
    -d "pipeline=cross_lsdb_dev&used_config="
```


To check the processing status, you must pass the process ID:

```bash
curl -X GET \
    -H "Authorization: Bearer PaZDOD5UwzbGOFsQr34LQ7JUYOj3yK" \
    http://localhost/api/processes/1/status/ 
```

To stop processing:

```bash
curl -X GET \
    -H "Authorization: Bearer PaZDOD5UwzbGOFsQr34LQ7JUYOj3yK" \
    http://localhost/api/processes/1/stop/ 
```


### Some example commands

Turn on background environment (if you have the application already running on the terminal, stop it with `CTRL + C` keys and up ir again, but in the background using `-d` argument):

```bash
docker-compose up -d
```

Access in the browser:
    - Django Admin: <http://localhost/admin/>
    - Django REST: <http://localhost/api>

Turn off all environment:

```bash
docker-compose stop
```

Restart all environment:

```bash
docker-compose stop && docker-compose up -d
```

Run a terminate on one of the services

```bash
# with the service turned on
docker-compose exec backend bash
# with the service turned off
docker-compose run backend bash
```

## Setup Slurm Enviroment

### What is it?

Internal application that interacts with the Slurm cluster and must be installed on a submission node. The application is a consumer of rabbitmq, and with each pipeline submission, a Slurm submission file is created and the process is finally submitted.

*note: This installation requires an orchestration running on the same submission node.*

Clone the repository and create a directory that will serve as the base for the application:
```bash
git clone https://github.com/linea-it/orchestration.git
mkdir slurm-worker
```

Copy the `slurm_env.sh` file and edit the environment variables as needed:
```bash
cp orchestration/backend/sh/slurm_env.sh slurm-worker/env.sh
vi slurm-worker/env.sh    # edit file
```

With Conda loaded, run:
```bash
source slurm-worker/env.sh
```

And start the application:
```bash
slurm_worker_manager start
```