# OCF API

An authenticated API for the OCF.

# Developing locally

## Setup

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pre-commit install
```

## Running

```
python -m uvicorn app.main:app --reload
```

# Testing

## FastAPI endpoints

The deployed (master) version can be accessed at 
<https://api.ocf.berkeley.edu/docs>. Accordingly, if you are running 
this locally using the command above, you can access a similarly fancy 
dashboard at `localhost:8000/docs`.

You can even test authenticated
endpoints by logging in on that page with OCF Keycloak SSO. Use a `client_id` of
`ocfapi` and a blank client secret, and it should log you in.

## Test setup with ocfstatic (and perhaps other projects too)

Since this API is being used increasingly in the 
[ocfstatic](https://github.com/ocf/ocfstatic) project, here's how to 
get them working together:

1. Follow the steps to setup and run
2. It's quite likely that you'll need to access mysql.ocf.berkeley.edu 
from your local machine to grab the data for your endpoints.
This won't work immediately, so do the following:
	1. Go into the file 
	`./venv/lib/python3.9/site-packages/ocflib/infra/mysql.py` and change `host`
	to `'127.0.0.1'`
	2. Open an ssh tunnel to Supernova (staff server) so that these requests can 
	actually go through on port 3306. Use the command:  
	`ssh bentref@supernova.ocf.berkeley.edu -L 3306:mysql:3306`

	At this point you should be able to locally access custom endpoints that 
	use mysql.ocf.berkeley.edu.
3. To test integration with ocfstatic, you have to point requests at 
the API, most likely `http://127.0.0.1:8000`, or the port specified by 
uvicorn. You can do this by, on `ocfstatic`, going into 
`gridsome.server.js` and changing the URL specified for `apiUrl`.  
**Important: For deployment, you must change this back. Changing it 
to `http://127.0.0.1:8000` is only for testing.**


