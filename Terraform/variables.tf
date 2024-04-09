# OpenStack auth settings
variable "openstack_url" {
    type = string
    description = "OpenStack Auth URL"
    default = "https://hb-openstack.hpc.rug.nl:5000"
}

variable "openstack_domainid" {
    type = string
    description = "OpenStack Domain ID"
    default = null
}

variable "openstack_domainname" {
    type = string
    description = "OpenStack Domain Name"
    default = null
}

variable "openstack_credentialid" {
    type = string
    description = "OpenStack Application Credential ID"
    sensitive = true
}

variable "openstack_credentialsecret" {
    type = string
    description = "OpenStack Application Credential Secret"
    sensitive = true
}

variable "openstack_projectid" {
    type = string
    description = "OpenStack Project ID"
    sensitive = true
}

variable "openstack_region" {
    type = string
    description = "OpenStack Region"
    default = ""
}


variable "flavor_name" {
    type = string
    description = "Flavor to use for the instance"
    #default = "general.v1.tiny"
    default = "digi.v1.vm.4-8-20"
}

variable "public_network" {
    type = string
    description = "Name of the public network to connect to"
    default = "external"
}



