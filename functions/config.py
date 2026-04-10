from functions.bash import run_bash
from functions.machine import (
    get_current_user,
    list_files,
    read_file,
    run_df,
    run_du,
    run_hostname,
    run_ifconfig,
    run_netstat,
)
from functions.math import calculate_math_expression
from functions.web import search


def get_local_tools():
    return [
        run_bash,
        calculate_math_expression,
        search,
        read_file,
        list_files,
        run_ifconfig,
        run_netstat,
        run_du,
        run_df,
        run_hostname,
        get_current_user,
    ]
