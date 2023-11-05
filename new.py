""" Python flask app for s3 Management """
from flask import Flask, render_template, request
import boto3
import botocore
from botocore.exceptions import ClientError

client = boto3.client('s3')

app = Flask(__name__)

@app.route("/")
def home():
    """
    Home page for displaying application
    """
    return render_template('index.html')

@app.route('/listing')
def listing():
    """
    Listing S3 buckets
    """
    list_buckets = client.list_buckets()
    buckets = list_buckets["Buckets"]
    return render_template('result.html', buckets=buckets)

@app.route('/create_bucket', methods=['POST'])
def create_bucket():
    """
    Create a new S3 bucket
    """
    bucket_name = request.form['bucket_name']# Retrieve the value of bucket_name from the HTML form
    try:
        client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': 'ap-south-1'}
        )
        return render_template('status.html', message='Bucket created successfully')
    except client.exceptions.BucketAlreadyExists:
        return render_template('status.html', message=f"S3 bucket {bucket_name} already exists")
    except client.exceptions.BucketAlreadyOwnedByYou:
        return render_template('status.html',
                               message=f"S3 bucket {bucket_name} already owned by you")
    except botocore.exceptions.ClientError as error:
        return render_template('status.html', message=error)

@app.route('/upload_file', methods=['POST'])
def upload_file():
    """
    Upload file to S3 bucket
    """
    bucket_name = request.form['bucket_name']# Retrieve the value of bucket_name from the HTML form
    try:
        file = request.files['file']
        file_name = file.filename
        client.upload_fileobj(file, bucket_name, file_name)
    except botocore.exceptions.ClientError as error:
        return render_template('status.html', message=error)
    return render_template('status.html', message='File uploaded successfully')

@app.route('/create_folder', methods=['POST'])
def create_folder():
    """
    Create a folder inside a bucket
    """
    try:
        bucket_name = request.form['bucket_name']
        directory_name = request.form['directory_name']
        client.put_object(Bucket=bucket_name, Key=(directory_name + '/'))
        return render_template('status.html', message='Folder created successfully')
    except ClientError as error:
        message = error.response["Error"]['Code']
        return render_template('status.html', message=message)

@app.route('/delete_bucket', methods=['POST'])
def delete_bucket():
    """
    Delete S3 bucket
    """
    del_buck = request.form['del_buck']# Retrieve the value of del_buck from the HTML form
    try:
        s3 = boto3.resource("s3") # pylint: disable=invalid-name
        bucket = s3.Bucket(del_buck)
        bucket.objects.all().delete()
        bucket.delete()
        return render_template('status.html', message='Bucket deleted successfully')
    except ClientError as error:
        if error.response['Error']['Code'] == 'NoSuchBucket':
            return render_template('status.html', message=f'The bucket {del_buck} does not exist.')
        return render_template('status.html', message=f'An error occurred: {error}')

@app.route('/del_file', methods=['POST'])
def del_file(): # pylint: disable=inconsistent-return-statements
    """
    Delete files in a bucket
    """
    bucket_name = request.form['bucket_name']
    file_name = request.form['file_name']
    try:
        response = client.delete_object( # pylint: disable=unused-variable
            Bucket=bucket_name,
            Key=file_name)
        return render_template('status.html', message="File deleted successfully")
    except ClientError as error:
        if error.response['Error']['Code'] == 'NoSuchBucket':
            return render_template('status.html',
                                   message=f'The bucket {bucket_name} does not exist.')
        if error.response['Error']['Code'] == 'NoSuchKey':
            return render_template('status.html',
                        message=f'The file {file_name} does not exist in the bucket {bucket_name}.')

@app.route('/copy', methods=['POST'])
def copy(): # pylint: disable=inconsistent-return-statements
    """
    Copy files from one bucket to another
    """
    src_bucket = request.form['src_bucket']
    src_file = request.form['src_file']
    des_bucket = request.form['des_bucket']
    des_file = request.form['des_file']

    copy_source = {
        'Bucket': src_bucket,
        'Key': src_file
    }
    try:
        response = client.copy_object( # pylint: disable=unused-variable
            Bucket=des_bucket,
            CopySource=copy_source,
            Key=des_file
        )
        return render_template('status.html', message="Object copied")
    except ClientError as error:
        if error.response['Error']['Code'] == 'NoSuchBucket':
            return render_template('status.html',
                        message=f'The bucket {src_bucket} or {des_bucket} does not exist.')
        if error.response['Error']['Code'] == 'NoSuchKey':
            return render_template('status.html',
                        message=f'The file {src_file} does not exist in the bucket {src_bucket}.')

@app.route('/move', methods=['POST'])
def move(): # pylint: disable=inconsistent-return-statements
    """
    Move files within an S3 bucket
    """
    src_bucket = request.form['src_bucket']
    src_file = request.form['src_file']
    des_bucket = request.form['des_bucket']
    des_file = request.form['des_file']

    copy_source = {
        'Bucket': src_bucket,
        'Key': src_file
    }
    try:
        response = client.copy_object( # pylint: disable=unused-variable
            Bucket=des_bucket,
            CopySource=copy_source,
            Key=des_file
        )
        client.delete_object(Bucket=src_bucket, Key=src_file)
        return render_template('status.html',
                               message="Object moved successfully")
    except ClientError as error:
        if error.response['Error']['Code'] == 'NoSuchBucket':
            return render_template('status.html',
                        message=f'The bucket {src_bucket} or {des_bucket} does not exist.')
        if error.response['Error']['Code'] == 'NoSuchKey':
            return render_template('status.html',
                        message=f'The file {src_file} does not exist in the bucket {src_bucket}.')

@app.route('/get_Objects', methods=['POST'])
def get_objects():
    """
    List objects in a bucket
    """
    bucket_name = request.form['bucket_name']
    s3 = boto3.resource('s3') # pylint: disable=invalid-name
    my_bucket = s3.Bucket(bucket_name)
    obj = []
    try:
        for my_bucket_object in my_bucket.objects.all():
            obj.append(my_bucket_object.key)
        return render_template('objlist.html', obj=obj)
    except ClientError as error:
        if error.response['Error']['Code'] == 'NoSuchBucket':
            return render_template('status.html',
                                   message=f'The bucket {bucket_name} does not exist.')
        return render_template('status.html',
                                   message=f'An error occurred: {error}')


if __name__ == "__main__":
    app.run(host="0.0.0.0",port=("5000"), debug=True)


# if __name__ == "__main__":
#    app.run(debug=True)

# if __name__ == "__main__":
#    app.run(port=("5000"), debug=True)


# End
