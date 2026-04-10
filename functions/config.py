from functions.machine import (
    run_hostname,
    run_df,
    run_du,
    run_netstat,
    run_ifconfig,
    list_files,
    read_file,
    get_current_user,
)

from functions.bash import run_bash
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
