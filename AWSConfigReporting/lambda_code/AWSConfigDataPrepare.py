import boto3
import gzip
import json
import sys
import os
import logging

s3c = boto3.client('s3')
logger = logging.getLogger()
#logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)


# Glue job parameters
bucket = "config-bucket-512718074009"
configReportingBucket="mfj-config-resources"




def read_config_object(bucket, Key, outputBucket):
    logging.info(f"start processing {bucket}  {Key}")
    obj = s3c.get_object(Bucket=bucket, Key=Key)
    key_elements = Key.split("/")

    base_name = key_elements[8].split(".")[0]
    fName = base_name.split("_")
    logging.info(fName[4])
    new_path = f"{key_elements[1]}/{key_elements[3]}/year={key_elements[4]}/month={key_elements[5]}/day={key_elements[6]}/resource={fName[4]}/{base_name}"
    contentRows = []
    fileCounter = 0
    with gzip.GzipFile(fileobj=obj["Body"]) as gzipfile:
        content = json.loads(gzipfile.read())
        for c in content['configurationItems']:
            # NOTE: For this version the configuration options are not included in the new_content records
            new_content = {
                "resourceType": c['resourceType'],
                "resourceId": c['resourceId'],
                "resourceName": c.get('resourceName'),
                "resourceARN": c.get('ARN'),
                "region":c['awsRegion'],
                "instanceType": c.get('instanceType'),
                "availabilityZone": c.get('availabilityZone'),
                "resourceCreationTime": c.get('resourceCreationTime'),
                "configurationCaptureTime": c['configurationItemCaptureTime'],
                "configurationStateId": c['configurationStateId'],
                "configurationItemStatus": c['configurationItemStatus'],
                "Product": c.get("tags").get('Product'),
                "Name": c.get("tags").get('Name')
            }
            fileCounter = fileCounter + 1
            contentRows.append(new_content)
        logging.debug(f"Found {fileCounter} configuration items")
        s3_path = f"{new_path}.json"

        s3c.put_object(
            Bucket=outputBucket,
            Key=s3_path,
            Body=json.dumps(contentRows)
        )
    return

def main():
    bucket = os.environ.get("SOURCE_BUCKET")
    configReportingBucket = os.environ.get("DESTINATION_BUCKET")
    bucket_list = s3c.list_objects_v2(Bucket=bucket)['Contents']
    sc_bucket_list = []
    for o in bucket_list:
        if "ConfigHistory" in o['Key']:
            read_config_object(bucket=bucket, Key=o['Key'], outputBucket=configReportingBucket)




def lambda_handler(event, context):
    # Get parameters
    main()



# s3 = boto3.resource('s3')
if __name__ == "__main__":
    main()




