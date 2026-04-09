from functions.machine import run_hostname, run_df, run_du, run_netstat, run_ifconfig, list_files, read_file, \
    get_current_user

from functions.web import search_web


def get_local_tools():
    return [search_web, read_file, list_files, run_ifconfig, run_netstat, run_du, run_df, run_hostname,
            get_current_user]
