# Terraform provisioning

This folder contains the files necessary to deploy a virtual machine running Flatcar on OpenStack with a basic network configuration.

- Update secrets.auto.tfvars.json.example with the needed values (create credentials on Openstack: Identity > Application Credentials)
- Run `init.sh` to initialise your local copy of the repository (also for generating keys, important)
- Run `terraform init`
- Run `terraform plan` 
- Run `terraform apply`
