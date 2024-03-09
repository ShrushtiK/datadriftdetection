# Adds the Flatcar image to OpenStack. Unfortunately, since the image is bz2-compressed,
# we can't instruct the server to download the file from the URL directly. Instead,
# Terraform will download the file to your machine, decompress it, and then upload
# it to OpenStack. This can be a costly operation depending on your internet speeds,
# so we mark this resource to not be randomly destroyed.
resource "openstack_images_image_v2" "flatcar" {
    name = "Flatcar"
    container_format = "bare"
    disk_format = "qcow2"

    image_source_url = "https://stable.release.flatcar-linux.net/amd64-usr/current/flatcar_production_openstack_image.img.bz2"
    decompress = true


    timeouts {
      create = "2h"
    }
}
