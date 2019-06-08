variable "openstack_user_name" { }
variable "openstack_password" { }
variable "keypair" { }
variable "staff_password" { }

variable "volume-uuid" {
  default = "c4bba436-b4a2-4e08-8629-21ccad322276"
}

variable "boot-image-uuid" {
  default = "7966c914-5241-4509-9b31-aa3b62a476d1" # CSAIL-Ubuntu-18.04LTS+autofs
}

# CSAIL's OpenStack provider.
provider "openstack" {
  tenant_name = "mario"
  user_name = var.openstack_user_name
  password  = var.openstack_password
  auth_url  = "https://keystone.csail.mit.edu:35358/"
}

# This is the virtual machine.
resource "openstack_compute_instance_v2" "caesar" {
  name = "caesar"
  flavor_name = "ups.1c1g"
  image_id = var.boot-image-uuid

  block_device {
    uuid                  = var.boot-image-uuid
    source_type           = "image"
    destination_type      = "local"
    boot_index            = 0
    delete_on_termination = true
  }

  network {
    name = "inet"
    fixed_ip_v4 = "128.52.128.206"
  }

  # IMPORTANT: generate this keypair yourself with "ssh-keygen -t rsa",
  # then import it into OpenStack;
  # if instead you use the Create Keypair button in the OpenStack UI, it seems to
  # create a keypair that Terraform can't subsequently use for ssh provisioning 
  # (which needs to happen below).
  key_pair = var.keypair

  security_groups = [
    "allow ssh from mit only",
    "allow http and https"
  ]

}


# Provision the VM: upload application code, install necessary packages, configure, and
# launch the application.
#
# This provisioner is kept as a separate null resource, rather than
# being inlined in the instance resource, so that we can rerun it without
# having to recreate the instance.
#
#    terraform taint null_resource.provision
#
# will make terraform mark it dirty, so that it runs on the next terraform apply.
# The triggers map can also mark it dirty when certain files 
# change on disk (like setup.sh); this is commented out right now, but
# is useful for debugging.
#
resource "null_resource" "provision" {
  depends_on = [
    openstack_compute_instance_v2.caesar
  ]
  triggers = {
    instance_changed = openstack_compute_instance_v2.caesar.id
    files_changed = join("", [
      # filesha256("setup.sh"),
    ])
  }

  # IMPORTANT: the security setup above allows incoming ssh only from MIT network addresses.
  # So you can't run this provisioning unless you're on the MIT network.
  # When you're offcampus, use the MIT VPN (https://ist.mit.edu/vpn).
  connection {
      type     = "ssh"
      user     = "ubuntu"
      host     = openstack_compute_instance_v2.caesar.access_ip_v4
      private_key = file("/Users/rcm/.ssh/id2_rsa")
  }

  # upload the application code
  provisioner "local-exec" {
    # COPYFILE_DISABLE is for MacOS, prevents resource forks (._blahblah) from appearing in the tarball
    command = "COPYFILE_DISABLE=1 tar czf ./deployed-bundle.tgz --exclude=terraform --exclude=.DS_Store --exclude=.vagrant --exclude='__pycache__' --exclude='*.pyc' --exclude='preprocessor/6*' -C .. ."
  }

  provisioner "file" {
    source = "deployed-bundle.tgz"
    destination = "/home/ubuntu/deployed-bundle.tgz"
  }

  # make Caesar folder and unpack the code
  provisioner "remote-exec" {
    inline = [
      "sudo mkdir -p /var/django/caesar",
      "sudo chown ubuntu /var/django/caesar",
      "sudo chgrp ubuntu /var/django/caesar",
      "cd /var/django/caesar",
      "tar xzf $HOME/deployed-bundle.tgz",
    ]
  }

  # upload a few more files from the terraform/ folder to specific places
  provisioner "file" {
    source = "update-6.031.sh"
    destination = "/var/django/caesar/preprocessor/update-6.031.sh"
  }

  provisioner "file" {
    source = "settings_local.py"
    destination = "/var/django/caesar/settings_local.py"
  }

  provisioner "file" {
    source = "krb5.keytab"
    destination = "/home/ubuntu/krb5.keytab"
  }

  provisioner "remote-exec" {
    inline = [
      # set the staff password
      "echo '${var.staff_password}\n${var.staff_password}' | sudo /usr/bin/passwd ubuntu",

      # make the link to the 6.031 AFS locker
      "ln -sf /afs/athena.mit.edu/course/6/6.031 /var/django/caesar/preprocessor/6.031",

      # put the Kerberos host keytab in the right place
      "sudo mv /home/ubuntu/krb5.keytab /etc",
      "sudo chown ubuntu /etc/krb5.keytab",
      "sudo chgrp ubuntu /etc/krb5.keytab",
      "sudo chmod 600 /etc/krb5.keytab",

      # do all the remaining installation and setup
      "/var/django/caesar/setup.sh"
    ]
  }

}
