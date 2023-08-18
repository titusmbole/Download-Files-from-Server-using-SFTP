import os
import paramiko
import time
import zipfile

class SSHFileDownloader:
    def __init__(self, hostname, username, private_key_path):
        self.hostname = hostname
        self.username = username
        self.private_key_path = private_key_path
        self.sshcon = paramiko.SSHClient()
        self.sshcon.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    def connect(self):
        try:
            self.sshcon.connect(self.hostname, username=self.username, key_filename=self.private_key_path)
            if self.sshcon.get_transport().is_active():
                print(f"Connected to {self.hostname} successfully!")
        except paramiko.AuthenticationException:
            print("Authentication failed. Please check your private key and username.")
        except paramiko.SSHException as e:
            print("SSH connection failed:", str(e))

    def disconnect(self):
        self.sshcon.close()

    def download_recursive(self, sftp, remote_dir, local_dir):
        for item in sftp.listdir(remote_dir):
            remote_path = os.path.join(remote_dir, item)
            local_path = os.path.join(local_dir, item)
            
            if sftp.stat(remote_path).st_mode & 0o170000 == 0o040000:  # Check if it's a directory
                os.makedirs(local_path, exist_ok=True)
                self.download_recursive(sftp, remote_path, local_path)
            else:
                sftp.get(remote_path, local_path)

    def download_item(self, item_name):
        try:
            self.connect()
            time.sleep(1)
            print("Finding, please wait.....")
            stdin, stdout, stderr = self.sshcon.exec_command(f"find / -name '{item_name}'")
            paths = stdout.read().decode().splitlines()

            if paths:
                print("Items found:")
                for path in paths:
                    print(path)
                    time.sleep(1)
                    print("Downloading.............. "+ item_name)
                    sftp = self.sshcon.open_sftp()
                    remote_path = path
                    local_path = os.path.basename(path)
                    if sftp.stat(remote_path).st_mode & 0o170000 == 0o040000:  # Check if it's a directory
                        zip_filename = local_path + '.zip'
                        ssh_stdin, ssh_stdout, ssh_stderr = self.sshcon.exec_command(f"zip -r {zip_filename} {remote_path}")
                        ssh_stdout.channel.recv_exit_status()
                        sftp.get(zip_filename, zip_filename)

                        with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
                            zip_ref.extractall(local_path)
                        
                        os.remove(zip_filename)
                    else:
                        sftp.get(remote_path, local_path)
                    sftp.close()

                    print("Item downloaded to:", local_path)
            else:
                print("Item not found.")
        finally:
            self.disconnect()

if __name__ == "__main__":
    hostname = '' #your HostName
    myuser = '' #your Username
    mySSHK = '' #your SSH key

    downloader = SSHFileDownloader(hostname, myuser, mySSHK)
    item_name = input("Enter file/directory name to search for: ")
    time.sleep(1)
    downloader.download_item(item_name)
