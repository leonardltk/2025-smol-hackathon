from django.shortcuts import render
from django.http import HttpRequest
from datachat.helper import (
    prompt_1_inject_raw_sql,
    prompt_2_django_orm,
    prompt_2_inject_raw_sql
)

# Create your views here.
def home(request: HttpRequest):
    result_from_llm_sql = prompt_1_inject_raw_sql()
    column_headers = ["", "Outlet 1", "Outlet 2", "Outlet 3"]
    row_data = [("D0001", "200", "400", "1200"), ("R0001", "200", "1000", "600")]
    return render(request, "home.html", {
        "col_headers": column_headers,
        "row_data": row_data
    })

def prompt_2(request: HttpRequest):
    sql_result = prompt_2_inject_raw_sql()
    return render(request, "p2.html", {
        "result": sql_result
    })

def prompt_3(request: HttpRequest):
    return render(request, "p3.html", {
    })