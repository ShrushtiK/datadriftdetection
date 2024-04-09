# Converting the user-readable Container Linux Configuration in flatcar_config.yaml
# into a machine-readable Ignition config file using the "Config Transpiler" ct.
#
# Also performs some template magic on this file to import the ssh keys to use.
data "ct_config" "master" {
  strict = true
  pretty_print = false
  content = templatefile("${path.module}/flatcar_config_master.yaml", {
    sshkey = file("${path.module}/id_rsa.pub")
    ip = openstack_networking_floatingip_v2.float_ip_master.address
  })
}
data "ct_config" "worker" {
  strict = true
  pretty_print = false
  count = 1
  content = templatefile("${path.module}/flatcar_config_worker.yaml", {
    sshkey = file("${path.module}/id_rsa.pub")
    master_ip = openstack_compute_instance_v2.flatcar_master.network.0.fixed_ip_v4
  })
}


