# EncryptionBox

### Description
The purpose of this desktop standalone application is to enable users to share text files on DropBox in a safe way using encryption.

This application integrates with a DropBox account by downloading a DropBox token and authorizing the application with it.
Such token should be kept somewhere safe (for example in a password protected file) as obtaining this token allows access to the
account associated with this particular token.

#### Flow
This app uses a dedicated folder in which the content of a DropBox account is mirrored.
After placing a text file in this folder, the file is automatically encrypted using an AES key and then, is uploaded to the DropBox
on the same path.
Any file being put in this folder will be downloaded and decrypted by the app automatically for the any other users sharing 
this dedicated folder.

Every folder has its own dedicated AES key.
Every user has their own encrypted version of aforementioned AES key, which is being used to encrypt/decrypt files and RSA key 
(private part of this key is referred as private RSA key and respectively for the public part).
The AES key is encrypted with the user's public RSA key. The private RSA key is used to decrypt the encrypted AES key; 
this private key should be stored somewhere safe (the application does not offer such functionality).
Encrypted AES keys are stored in the folder so there is no need to pass them constantly between the users.
If a user A wants to gain access to a user B folder, A has to send their public RSA key to B.
B uses it to encrypt the folder AES key and then, sends it back along with calculated checksum of the AES key to A.
A can place their encrypted AES key in the folder on their machine and from now on they are able to encrypt/decrypt files in/from this 
particular folder.

![Workflow Image](https://github.com/b4ry/EncryptionBox/blob/master/Workflow.jpg)

### Functionalities
- integrating the application with a DropBox account using generated tokens allowing the application to communicate with DropBox via its API,
- generating AES and RSA keys,
- encrypting AES keys using public RSA keys,
- allowing users to send keys via GMAIL using SMTP protocol over secure SSL/TSL layers,
- decrypting encrypted AES keys using private RSA keys,
- encrypting text files using AES keys by placing the file in a shared folder,
- decrypting encrypted text files using AES keys,
- filtering files based on their types in a folder which is being used by the app and shared with other users (.aes - encrypted AES keys, .enc - encrypted text files),
- user notification about the shared folder state changes (via a watcher)

### Techs
- Python 3.3,
- PyQt 5.2.1 (GUI),
- PyCrypto library,
- Dropbox Core Api (all integration with DropBox and catching changes in DropBox folders using Delta system),
- Win32 Api (used by the watcher)

### Roadmap
- implementing secure storage of private RSA key and DropBox token within the application,
- association of AES keys and the folders in the application instead of putting the keys physically in the dedicated folder,
- supporting multiple accounts and multiple top level folders,
- synchronisation deletion support,
- file modification support,
- multiple format encryption/decryption support,
- create a web plugin
