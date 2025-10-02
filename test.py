#!/usr/bin/env -S uv run

import boto3
import pytest
import subprocess
from datetime import datetime


def get_terraform_output(output_name):
    """Get Terraform output value"""
    try:
        result = subprocess.run(
            ["terraform", "output", "-raw", output_name],
            cwd="terraform",
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error getting Terraform output {output_name}: {e}")
        raise


@pytest.fixture(scope="session")
def admin_s3_client(bucket_name):
    """Create S3 client with admin credentials from current environment"""
    client = boto3.client("s3", region_name="us-east-2")
    yield client
    # Cleanup: Delete all objects in the test bucket after tests
    objects = client.list_objects_v2(Bucket=bucket_name)
    for obj in objects.get("Contents", []):
        client.delete_object(Bucket=bucket_name, Key=obj["Key"])


@pytest.fixture(scope="session")
def heroku_user_s3_client():
    access_key_id = get_terraform_output("aws_access_key_id")
    secret_access_key = get_terraform_output("aws_secret_access_key")

    return boto3.client(
        "s3",
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name="us-east-2",
    )


@pytest.fixture(scope="session")
def bucket_name():
    """S3 bucket name for testing"""
    return get_terraform_output("s3_bucket_name")


def test_legal_hold(admin_s3_client, heroku_user_s3_client, bucket_name):
    # Upload a test object with the "published" tag using admin credentials
    heroku_user_s3_client.put_object(
        Bucket=bucket_name,
        Key="test-object-key",
        Body="test-content",
        Tagging="legalHold=true",
    )

    heroku_user_s3_client.put_object_legal_hold(
        Bucket=bucket_name,
        Key="test-object-key",
        LegalHold={
            'Status': 'ON',
        },
    )

    # Attempt to delete the object using heroku user credentials
    with pytest.raises(heroku_user_s3_client.exceptions.ClientError) as exc_info:
        heroku_user_s3_client.delete_object(Bucket=bucket_name, Key="test-object-key")

        # Delete the object versions too
        versions = heroku_user_s3_client.list_object_versions(
            Bucket=bucket_name, Prefix="test-object-key"
        )
        for version in versions["Versions"]:
            # # Remove legal hold before deletion
            # heroku_user_s3_client.put_object_legal_hold(
            #     Bucket=bucket_name,
            #     Key=version["Key"],
            #     VersionId=version["VersionId"],
            #     LegalHold={'Status': 'OFF'},
            # )

            heroku_user_s3_client.delete_object(
                Bucket=bucket_name, Key=version["Key"], VersionId=version["VersionId"]
            )
