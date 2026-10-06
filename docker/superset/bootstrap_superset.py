"""Idempotently create the SmartCRM database, datasets, charts and dashboard."""

import json
import os
import sys
import time
import http.cookiejar
import urllib.error
import urllib.parse
import urllib.request


BASE_URL = os.getenv("SUPERSET_INTERNAL_URL", "http://superset:8088").rstrip("/")
USERNAME = os.getenv("SUPERSET_ADMIN_USERNAME", "admin")
PASSWORD = os.environ["SUPERSET_ADMIN_PASSWORD"]
DATABASE_URI = os.environ["SMARTCRM_ANALYTICS_URI"]
TOKEN = None
CSRF_TOKEN = None
OPENER = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
)


def request(method, path, payload=None, authenticated=True):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if authenticated and TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    if authenticated and CSRF_TOKEN and method not in {"GET", "HEAD", "OPTIONS"}:
        headers["X-CSRFToken"] = CSRF_TOKEN
        headers["Referer"] = f"{BASE_URL}/"
    req = urllib.request.Request(BASE_URL + path, data=data, headers=headers, method=method)
    try:
        with OPENER.open(req, timeout=30) as response:
            body = response.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} trả về HTTP {exc.code}: {detail}") from exc


def login():
    global TOKEN, CSRF_TOKEN
    response = request(
        "POST",
        "/api/v1/security/login",
        {
            "username": USERNAME,
            "password": PASSWORD,
            "provider": "db",
            "refresh": True,
        },
        authenticated=False,
    )
    TOKEN = response["access_token"]
    CSRF_TOKEN = request("GET", "/api/v1/security/csrf_token/")["result"]


def list_resource(resource):
    query = urllib.parse.urlencode({"q": "(page:0,page_size:100)"})
    return request("GET", f"/api/v1/{resource}/?{query}").get("result", [])


def result_id(response):
    if response.get("id") is not None:
        return response["id"]
    result = response.get("result") or {}
    return result["id"]


def ensure_database():
    name = "SmartCRM PostgreSQL (read-only)"
    for item in list_resource("database"):
        if item.get("database_name") == name:
            return item["id"]
    return result_id(
        request(
            "POST",
            "/api/v1/database/",
            {
                "database_name": name,
                "sqlalchemy_uri": DATABASE_URI,
                "expose_in_sqllab": True,
                "allow_ctas": False,
                "allow_cvas": False,
                "allow_dml": False,
                "extra": json.dumps({"metadata_params": {}, "engine_params": {}}),
            },
        )
    )


def ensure_dataset(database_id, table_name):
    for item in list_resource("dataset"):
        if item.get("schema") == "analytics" and item.get("table_name") == table_name:
            return item["id"]
    return result_id(
        request(
            "POST",
            "/api/v1/dataset/",
            {"database": database_id, "schema": "analytics", "table_name": table_name},
        )
    )


def sql_metric(expression, label):
    return {
        "expressionType": "SQL",
        "sqlExpression": expression,
        "label": label,
    }


def ensure_dashboard():
    for item in list_resource("dashboard"):
        if item.get("slug") == "smartcrm-overview":
            return item["id"]
    return result_id(
        request(
            "POST",
            "/api/v1/dashboard/",
            {
                "dashboard_title": "SmartCRM — Tổng quan kinh doanh",
                "slug": "smartcrm-overview",
                "published": True,
                "json_metadata": json.dumps(
                    {"refresh_frequency": 0, "timed_refresh_immune_slices": []}
                ),
                "position_json": "{}",
            },
        )
    )


def ensure_chart(name, viz_type, dataset_id, dashboard_id, params):
    chart_id = None
    chart_uuid = None
    for item in list_resource("chart"):
        if item.get("slice_name") == name:
            chart_id = item["id"]
            break

    payload = {
        "slice_name": name,
        "viz_type": viz_type,
        "datasource_id": dataset_id,
        "datasource_type": "table",
        "dashboards": [dashboard_id],
        "params": json.dumps(params),
    }
    if chart_id is None:
        response = request("POST", "/api/v1/chart/", payload)
        chart_id = result_id(response)
        chart_uuid = response.get("uuid") or (response.get("result") or {}).get("uuid")
    else:
        request("PUT", f"/api/v1/chart/{chart_id}", payload)

    if not chart_uuid:
        detail = request("GET", f"/api/v1/chart/{chart_id}").get("result", {})
        chart_uuid = detail.get("uuid")
    if not chart_uuid:
        raise RuntimeError(f"Không lấy được UUID cho chart '{name}'.")
    return {"id": chart_id, "uuid": str(chart_uuid), "name": name}


def build_layout(charts):
    layout = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"id": "ROOT_ID", "type": "ROOT", "children": ["GRID_ID"]},
        "GRID_ID": {
            "id": "GRID_ID",
            "type": "GRID",
            "parents": ["ROOT_ID"],
            "children": [],
        },
        "HEADER_ID": {
            "id": "HEADER_ID",
            "type": "HEADER",
            "meta": {"text": "SmartCRM — Tổng quan kinh doanh"},
        },
    }
    row_groups = [charts[:2], charts[2:4], charts[4:]]
    for row_index, group in enumerate(row_groups, start=1):
        if not group:
            continue
        row_id = f"ROW-SMARTCRM-{row_index}"
        layout["GRID_ID"]["children"].append(row_id)
        layout[row_id] = {
            "id": row_id,
            "type": "ROW",
            "parents": ["ROOT_ID", "GRID_ID"],
            "children": [],
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
        }
        width = 12 // len(group)
        for chart in group:
            component_id = f"CHART-{chart['id']}"
            layout[row_id]["children"].append(component_id)
            layout[component_id] = {
                "id": component_id,
                "type": "CHART",
                "parents": ["ROOT_ID", "GRID_ID", row_id],
                "children": [],
                "meta": {
                    "chartId": chart["id"],
                    "height": 36,
                    "width": width,
                    "sliceName": chart["name"],
                    "uuid": chart["uuid"],
                },
            }
    return layout


def main():
    for attempt in range(30):
        try:
            login()
            break
        except Exception:
            if attempt == 29:
                raise
            time.sleep(2)

    database_id = ensure_database()
    customer_dataset = ensure_dataset(database_id, "customer_360")
    sales_dataset = ensure_dataset(database_id, "sales_daily")
    ensure_dataset(database_id, "order_detail")
    dashboard_id = ensure_dashboard()

    charts = [
        ensure_chart(
            "Tổng doanh thu",
            "big_number_total",
            customer_dataset,
            dashboard_id,
            {
                "viz_type": "big_number_total",
                "datasource": f"{customer_dataset}__table",
                "metric": sql_metric("SUM(revenue)", "Tổng doanh thu"),
                "subheader": "VNĐ — đơn hoàn thành",
                "time_range": "No filter",
                "y_axis_format": ",d",
            },
        ),
        ensure_chart(
            "Tổng khách hàng",
            "big_number_total",
            customer_dataset,
            dashboard_id,
            {
                "viz_type": "big_number_total",
                "datasource": f"{customer_dataset}__table",
                "metric": sql_metric("COUNT(*)", "Tổng khách hàng"),
                "subheader": "khách hàng trong CRM",
                "time_range": "No filter",
                "y_axis_format": ",d",
            },
        ),
        ensure_chart(
            "Xu hướng doanh thu theo ngày",
            "echarts_timeseries_line",
            sales_dataset,
            dashboard_id,
            {
                "viz_type": "echarts_timeseries_line",
                "datasource": f"{sales_dataset}__table",
                "x_axis": "order_date",
                "granularity_sqla": "order_date",
                "metrics": [sql_metric("SUM(revenue)", "Doanh thu")],
                "time_grain_sqla": "P1D",
                "time_range": "No filter",
                "show_legend": True,
                "y_axis_format": ",d",
            },
        ),
        ensure_chart(
            "Phân bố phân khúc AI",
            "pie",
            customer_dataset,
            dashboard_id,
            {
                "viz_type": "pie",
                "datasource": f"{customer_dataset}__table",
                "groupby": ["segment_label"],
                "metric": sql_metric("COUNT(*)", "Số khách hàng"),
                "time_range": "No filter",
                "show_legend": True,
                "show_labels": True,
                "label_type": "key_percent",
            },
        ),
        ensure_chart(
            "Khách hàng theo doanh thu",
            "table",
            customer_dataset,
            dashboard_id,
            {
                "viz_type": "table",
                "datasource": f"{customer_dataset}__table",
                "all_columns": [
                    "full_name",
                    "company",
                    "segment_label",
                    "order_count",
                    "revenue",
                ],
                "order_by_cols": ['["revenue", false]'],
                "row_limit": 20,
                "time_range": "No filter",
                "include_search": True,
            },
        ),
    ]

    request(
        "PUT",
        f"/api/v1/dashboard/{dashboard_id}",
        {
            "dashboard_title": "SmartCRM — Tổng quan kinh doanh",
            "slug": "smartcrm-overview",
            "published": True,
            "position_json": json.dumps(build_layout(charts)),
            "json_metadata": json.dumps(
                {"refresh_frequency": 0, "timed_refresh_immune_slices": []}
            ),
        },
    )
    print("Đã cấu hình database, 3 datasets, 5 charts và dashboard SmartCRM.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Khởi tạo Superset thất bại: {exc}", file=sys.stderr)
        raise
