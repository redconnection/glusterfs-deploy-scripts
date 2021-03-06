#!/usr/bin/python

import os, sys
import re
import run_helper



def pre_create_cleanup(nodes, export_dir):
    for node in nodes:
        cmd = 'pgrep gluster | xargs kill -9'
        run_helper.run_command(node, cmd, False)

        cmd = 'mkdir -p ' + export_dir
        run_helper.run_command(node, cmd, False)

        cmd = 'rm -rf ' + export_dir + '/*'
        run_helper.run_command(node, cmd, False)

        cmd = 'rm -rf /etc/glusterd'
        run_helper.run_command(node, cmd, False)

        cmd = 'rm -rf /usr/local/var/log/glusterfs/*'
        run_helper.run_command(node, cmd, False)

        cmd = 'rm -f /usr/local/var/log/glusterfs/.c*'
        run_helper.run_command(node, cmd, False)

        cmd = 'rm -rf /var/log/glusterfs/*'
        run_helper.run_command(node, cmd, False)

        cmd = 'rm -f /var/log/glusterfs/.c*'
        run_helper.run_command(node, cmd, False)

    return 0

def create_gluster_partition
    mgmt_node = run_helper.get_mgmt_node()
    nodes = run_helper.get_nodes_ip()


    for node in nodes:
        cmd = 'pvcreate GLUSTERPV --force; vgcreate $GLUSTERVG $GLUSTERPV'
        run_helper.run_command(node, cmd, False)

	cmd = 'lvcreate -n $GLUSTERLV -L 2GB $GLUSTERVG'
        run_helper.run_command(node, cmd, False)

	cmd = 'mkfs -t xfs -i size=512 /dev/$GLUSTERVG/$GLUSTERLV'
        run_helper.run_command(node, cmd, False)

	cmd = 'echo `xfs_admin -u /dev/$GLUSTERVG/$GLUSTERLV` $GLUSTEREXPORT  xfs  allocsize=4096,inode64 0 0 >> /etc/fstab'
	run_helper.run_command(node, cmd, False)

    return 0




def create_gluster_volume():
    mgmt_node = run_helper.get_mgmt_node()
    nodes = run_helper.get_nodes_ip()
    if mgmt_node not in nodes:
        print 'WARNING: management is not part of the server nodes. While this is not usual, Still proceeding with it.'

    export_dir = run_helper.get_server_export_dir()
    vol_type = run_helper.get_volume_type()
    trans_type = run_helper.get_trans_type()
    volname = run_helper.get_vol_name()
    bricks_number = run_helper.get_number_of_bricks()

    pre_create_cleanup(nodes, export_dir)

    brick_list = []
    last_server_index = len(nodes) -1
    server_index = 0
    for i in range(1, (int(bricks_number) + 1)):
        brick = nodes[server_index] + ':' + export_dir + '/' + volname + '_brick' + str(i)
        brick_list.append(brick)
        if server_index == last_server_index:
            server_index = 0
        else:
            server_index = server_index + 1

    replica_count = ''
    if vol_type in ('dist-rep', 'stripe-rep', 'rep', 'dist-stripe-rep'):
        replica_count = 'replica ' + run_helper.get_replica_count()

    stripe_count = ''
    if vol_type in ('stripe', 'stripe-rep', 'dist-stripe-rep', 'dist-stripe'):
        stripe_count = 'stripe ' + run_helper.get_stripe_count()

    vol_create_cmd = 'gluster volume create ' + volname + ' ' + replica_count + ' ' + stripe_count + ' ' + 'transport ' + trans_type + ' ' + ' '.join(brick_list) + ' --mode=script'

    flag = 0
    for node in nodes:
        status = run_helper.run_command(node, 'glusterd', False)
        if status:
            print 'glusterd can not be started in node: ' + node
            flag = 1

    if flag:
        print 'glusterd can not be started successfully in all nodes. Exiting...'
        sys.exit(1)

    flag = 0
    for node in nodes:
        if node != mgmt_node:
            status = run_helper.run_command(mgmt_node, 'gluster peer probe ' + node, False)
            if status:
                print 'peer probe went wrong in ' + node
                flag = 1

    if flag:
        print 'Peer probe went wrong in some machines. Exiting...'
        sys.exit(1)

    status = run_helper.run_command(mgmt_node, vol_create_cmd, True)
    if status:
        print 'volume creation failed.'

    return status




def start_gluster_volume():
    volname = run_helper.get_vol_name()
    mgmt_node = run_helper.get_mgmt_node();
    vol_start_cmd = 'gluster volume start ' + volname
    status = run_helper.run_command(mgmt_node, vol_start_cmd, True)
    if status:
        print 'volume starting failed. Deleting the volume created...'
        run_helper.run_command(mgmt_node, 'gluster volume delete ' + volname + ' --mode=script', True)

    return status




def main():

    start = True
    args = sys.argv[1:]
    if not args:
        start = False
    else:
        if args[0] != '--start-vol':
            start = False

    status = create_gluster_volume()
    if status:
        print 'Exiting...'
        sys.exit(1)
    
    if start:
        status = start_gluster_volume()
        if status:
            print 'Exiting...'
            sys.exit(1)

    return status

if __name__ == '__main__':
    main()
