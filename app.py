from flask import Flask, request, jsonify
import boto3, json, requests, os
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

app = Flask(__name__)

AWS_REGION = 'us-east-2'
SERVICE = 'textract'
session = boto3.Session()

@app.route("/textract-proxy", methods=["POST"])
def textract_proxy():
    data = request.get_json()
    target = data.get("target")
    payload = json.dumps(data.get("payload", {}))

    aws_headers = {
        "Content-Type": "application/x-amz-json-1.1",
        "X-Amz-Target": target
    }

    aws_req = AWSRequest(
        method="POST",
        url=f"https://textract.{AWS_REGION}.amazonaws.com/",
        data=payload,
        headers=aws_headers
    )

    creds = session.get_credentials().get_frozen_credentials()
    SigV4Auth(creds, SERVICE, AWS_REGION).add_auth(aws_req)

    resp = requests.post(aws_req.url, headers=dict(aws_req.headers), data=payload)
    print("=== Target ===", target)
    print("=== Payload ===", payload)
    print("=== Headers ===", dict(aws_req.headers))
    print("=== Response ===", resp.status_code, resp.text)
    try:
        return jsonify(resp.json()), resp.status_code
    except Exception:
        return resp.text, resp.status_code


@app.route("/textract-proxy-get", methods=["GET"])
def textract_proxy_get():
    target = request.args.get("target")
    job_id = request.args.get("jobId")

    if not target or not job_id:
        return jsonify({"error": "Missing required query parameters: target and jobId"}), 400

    # Textract expects POST requests, even for job results, so this is a POST disguised as a GET
    payload = json.dumps({"JobId": job_id})

    aws_headers = {
        "Content-Type": "application/x-amz-json-1.1",
        "X-Amz-Target": target
    }

    aws_req = AWSRequest(
        method="POST",
        url=f"https://textract.{AWS_REGION}.amazonaws.com/",
        data=payload,
        headers=aws_headers
    )

    creds = session.get_credentials().get_frozen_credentials()
    SigV4Auth(creds, SERVICE, AWS_REGION).add_auth(aws_req)

    resp = requests.post(aws_req.url, headers=dict(aws_req.headers), data=payload)
    print("=== Target (GET) ===", target)
    print("=== JobId ===", job_id)
    print("=== Response ===", resp.status_code, resp.text)
    try:
        return jsonify(resp.json()), resp.status_code
    except Exception:
        return resp.text, resp.status_code


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
