#!/bin/bash
echo "Testing /api/upload..."
UPLOAD_RES=$(curl -s -X POST http://localhost:8000/api/upload -F "file=@sample_data/TOI_270.npz")
echo "$UPLOAD_RES" | head -c 200
JOB_ID=$(echo "$UPLOAD_RES" | grep -o '"job_id":"[^"]*' | cut -d'"' -f4)
echo -e "\nGot job ID: $JOB_ID"

echo -e "\nTesting /api/process..."
PROCESS_RES=$(curl -s -X POST http://localhost:8000/api/process/$JOB_ID)
echo "$PROCESS_RES" | head -c 200

echo -e "\nTesting /api/sample-data..."
SAMPLE_RES=$(curl -s -X GET "http://localhost:8000/api/sample-data?target=TOI-270")
echo "$SAMPLE_RES" | head -c 200
SAMPLE_JOB_ID=$(echo "$SAMPLE_RES" | grep -o '"job_id":"[^"]*' | cut -d'"' -f4)
echo -e "\nGot sample job ID: $SAMPLE_JOB_ID"

echo -e "\nTesting /api/download..."
curl -s -D - http://localhost:8000/api/download/$JOB_ID -o /dev/null | head -n 5

