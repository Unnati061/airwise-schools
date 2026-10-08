# Sydney runtime smoke - 2026-10-08 IST

User confirmed AWS Settings assigns this project to ap-southeast-2 (Sydney), with
$100 credits remaining (user-reported, not independently checked). Corrects the
earlier us-east-1 assumption. No region probing, account switch, advanced feature
activation, SCP changes, public endpoints or paid AI calls occurred.

## Actual outcome

BLOCKED at S3 ZIP upload due to network/transport failures. Sydney Lambda access
preflight passed: GetFunction returned ResourceNotFoundException for the intended
unused name, rather than an SCP deny. Browser login refresh was unnecessary.
Profile airwise default region and every deployment client now use Sydney.

Created only: airwise-smoke-artifacts-a1f7411817. Verified location
ap-southeast-2, all four public access blocks true, AES256 encryption configured,
BucketOwnerEnforced ownership, and Project=AirWiseSchools, Packet=A,
Purpose=NativeRuntimeSmoke tags. Final inspection found zero incomplete uploads
and zero completed part bytes. HeadObject returned 404; ZIP not stored.

NOT created: airwise-smoke-role-a1f7411817,
airwise-runtime-smoke-a1f7411817, or its CloudWatch log group.
No AWS invocation, solver result or logs exist. No cleanup was executed against
the bucket. The SDK cancelled only incomplete uploads owned by its failed transfer.

## Preserved configuration

- Existing Linux ZIP: 61,637,194 bytes compressed; 190,107,573 bytes extracted.
- SHA-256: b78df0eae964653c3ee7f5a7230fab35d11f391d89716262f548fd21b4584e7a.
- Below 250 MiB extracted limit, above 50 MiB direct Lambda upload limit.
- Python 3.12/x86_64, 1024 MB, 30 seconds, no layers/VPC/provisioned concurrency.
- Existing tiny CP-SAT solver and version-reporting handler unchanged.
- S3 CreateBucketConfiguration.LocationConstraint explicitly ap-southeast-2.
- Future execution role permits only CreateLogStream/PutLogEvents on this
  function's Sydney log streams. Seven-day retention configured before Lambda.
- Same four-resource scope and tags; no unrelated resources overwritten.
- Lambda CodeSha256 will be checked against the local ZIP after deployment.

## Executed commands and diagnostics

```powershell
aws lambda get-function --function-name airwise-runtime-smoke-a1f7411817 --profile airwise --region ap-southeast-2 --no-cli-pager --cli-connect-timeout 5 --cli-read-timeout 10
aws configure set region ap-southeast-2 --profile airwise
aws configure get region --profile airwise
.venv\Scripts\python -m pytest backend/tests -q
.venv\Scripts\python scripts/aws_smoke.py deploy
aws s3api get-bucket-location --bucket airwise-smoke-artifacts-a1f7411817 --profile airwise --region ap-southeast-2
aws s3api get-public-access-block --bucket airwise-smoke-artifacts-a1f7411817 --profile airwise --region ap-southeast-2
.venv\Scripts\python scripts/aws_smoke.py resume-upload
```

Deploy passed collision checks and created/configured the bucket, then boto3's
default multipart upload failed with SSLEOFError while sending chunked data.
Read-only multipart inspection showed no completed parts. Retried with AWS's
documented when_required checksum mode and bounded connection/retry timeouts:
ReadTimeoutError, then ConnectionClosedError at the upload stage. TLS verification
remained enabled. No OR-Tools or other runtime dependencies were changed.

AWS CLI s3 cp with when_required checksums exited 0 without a transfer message,
but HeadObject returned 404 and list-objects showed no object; this was not counted
as success. Direct s3api put-object with a precomputed SHA256 checksum exited 255:
connection closed before receiving a valid response from the Sydney S3 endpoint.
Final bounded attempt used sequential 5 MiB multipart chunks, explicit checksum
headers, and the standard Sydney path-style endpoint: ConnectionClosedError again.
The common failure is transport during data upload. No HTTP IAM/SCP denial was
returned for those failures. Exact network cause is unknown; do not assume a
particular proxy, firewall or AWS account policy is responsible.
Final local suite: 10 passed, two existing dependency deprecation warnings.
Uploader checks verify intact part bytes/checksums and cancellation limited to
the failed call's own incomplete upload. Region guard rejects us-east-1.

Checksum reference: https://docs.aws.amazon.com/sdkref/latest/guide/feature-dataintegrity.html .
S3 location reference: https://docs.aws.amazon.com/AmazonS3/latest/API/API_CreateBucket.html .

## Resume without recreating the bucket

Resolve upload connectivity or upload work/airwise-runtime-smoke.zip through the
S3 console in Sydney to the existing bucket, key runtime-smoke.zip. Set user
metadata sha256 to the hexadecimal hash above. Keep public access blocked.
Do not alter the ZIP, expose a public object, or bypass TLS verification.

Then run `.venv\Scripts\python scripts/aws_smoke.py resume-upload`. This action
requires the manifest to contain only the bucket, validates its region and exact
project tags, and refuses a mismatched existing object. A matching object is reused
without overwrite; Lambda's computed code hash is then checked. If the object is
missing, the uploader retries using sequential checksummed parts. It cancels only
the incomplete transfer it created. Other existing resource names still block
creation. Do not run ordinary deploy again against a partial manifest.

After successful creation (NOT yet executed):

```powershell
aws lambda invoke --function-name airwise-runtime-smoke-a1f7411817 --profile airwise --region ap-southeast-2 --invocation-type RequestResponse --log-type Tail --payload '{}' --cli-binary-format raw-in-base64-out work/aws-smoke-response.json
Get-Content work/aws-smoke-response.json
aws logs filter-log-events --log-group-name /aws/lambda/airwise-runtime-smoke-a1f7411817 --profile airwise --region ap-southeast-2
```

Inspect FunctionError, actual solver result/versions and CloudWatch logs before
claiming compatibility. Expected tiny model result is OPTIMAL/objective 6 with
unique periods 1,2,3. That result has only been verified locally so far.

## Cleanup

Only the empty artifact bucket currently exists. Its explicit cleanup command,
NOT executed, is:

```powershell
aws s3api delete-bucket --bucket airwise-smoke-artifacts-a1f7411817 --profile airwise --region ap-southeast-2
```

If later deployed, inspect created[] in work/aws-smoke.json and use the targeted
Sydney cleanup commands in AWS_SMOKE.md. No recursive filesystem deletion or
blanket bucket cleanup is prescribed. The bucket remains for the authorized retry.
