# The actual Virtual Machine instance running Flatcar
resource "openstack_compute_instance_v2" "flatcar_master" {
    name = "master"
    # name = "CorPool"
    # how many vms
    #count = 3
    # OS
    image_id = openstack_images_image_v2.flatcar.id
    # RAM, CPU
    flavor_name = var.flavor_name
    security_groups = ["default", openstack_networking_secgroup_v2.basic.name]    
    user_data = data.ct_config.master.rendered
    network {
        uuid = openstack_networking_network_v2.internal.id
    }

}

resource "openstack_compute_instance_v2" "flatcar_worker" {
    name = "worker ${count.index}"
    # name = "CorPool"
    # how many vms
    count = 3
    # OS
    image_id = openstack_images_image_v2.flatcar.id
    # RAM, CPU
    flavor_name = var.flavor_name
    security_groups = ["default", openstack_networking_secgroup_v2.basic.name]
    
    user_data = data.ct_config.worker[count.index].rendered

    network {
        uuid = openstack_networking_network_v2.internal.id
    }

    depends_on = [openstack_compute_floatingip_associate_v2.fip_master]
}
