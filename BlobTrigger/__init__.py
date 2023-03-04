import logging
import os
import smtplib
from email.message import EmailMessage
from azure.storage.blob import BlobServiceClient
import azure.functions as func


MIN_FILE_SIZE = int(os.environ.get("MIN_FILE_SIZE", 10))
SMTP_SERVER = os.environ.get("SMTP_SERVER", "intrado-com.mail.protection.outlook.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 25))
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "emptylakehousefilemonitoring@Intrado.com")
RECIPIENT_EMAILS = os.environ.get("RECIPIENT_EMAILS", "steveandrew.ramos@intrado.com,metrics.department@intrado.com").split(",")

def main(myblob: func.InputStream, message: func.Out[str]) -> None:
    try:
        connect_str = os.environ["proddlsintradolake001_STORAGE"]

        # Create the BlobServiceClient object
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        container_name = os.environ.get("CONTAINER_NAME", "archive")
        container_client = blob_service_client.get_container_client(container_name)
        # blob_list = container_client.list_blobs()
        blob_list = container_client.list_blobs(name_starts_with="inbound/aradtcc/dialog/2023/")
        # blob_list = [blob for blob in blob_list if blob.blob_type == "BlockBlob"]  # Filter out folders
        blob_list = sorted(blob_list, key=lambda x: x.last_modified, reverse=True)
        # latest_blob = blob_list[0]

        for myblob in blob_list:
            if len(myblob.name.split("/")) != 8:
                pass
                log_message = f"Pass {myblob.name}"
                logging.info(log_message)
            else:
                if myblob.size < MIN_FILE_SIZE:
                    send_email(myblob.name, myblob.size)
                    
                    log_message = f"New file {myblob.blob_type} {myblob.name} has been uploaded to the container with size {myblob.size} bytes."
                    logging.info(log_message)
                    message.set(log_message)
                    # send_email(blob_properties.name, blob_properties.size)
                    # message.set(log_message)
                else:
                    logging.info(f"File {myblob.name} is not less than {MIN_FILE_SIZE} KB in size.")

        # if not blob_list:
        #     log_message = "No new files found in the container."
        #     logging.info(log_message)
        #     message.set(log_message)
        #     return
        # latest_blob = blob_list[0]
        # blob_client = container_client.get_blob_client(latest_blob.name)
        # blob_properties = blob_client.get_blob_properties()
        # if blob_properties.size < MIN_FILE_SIZE:
        #     log_message = f"New file {blob_properties.name} has been uploaded to the container with size {blob_properties.size} bytes."
        #     logging.info(log_message)
        #     send_email(blob_properties.name, blob_properties.size)
        #     message.set(log_message)
    except Exception as ex:
        error_message = f"An error occurred while monitoring the blob storage container: {ex}"
        logging.error(error_message)
        send_error_email(error_message)


def send_email(filename, size):
    subject = f"File {filename} on proddlsintradolake001 is {size} KB size"
    content = f"The file {filename} on proddlsintradolake001 has been uploaded to the storage container but it is {size} KB in size."

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = SENDER_EMAIL
    message["To"] = RECIPIENT_EMAILS
    message.set_content(content)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.send_message(message)


def send_error_email(message):
    subject = "Error occurred while monitoring blob storage container"
    content = f"An error occurred while monitoring the blob storage container: {message}"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = SENDER_EMAIL
    message["To"] = RECIPIENT_EMAILS
    message.set_content(content)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.send_message(message)