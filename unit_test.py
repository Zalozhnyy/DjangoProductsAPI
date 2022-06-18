# encoding=utf8

import json
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

from yandexProducts.importGenerator import Generator as DataGenerator
import time
import asyncio
import aiohttp

API_BASEURL = "http://localhost:8000"

ROOT_ID = "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1"

UPDATE_BATCH = [

    {
        "items": [
            {
                "type": "OFFER",
                "name": "ITEM2",
                "id": "73bc3b36-02d1-4245-ab35-3106c9ee1c68",
                "parentId": "73bc3b36-02d1-4245-ab35-3106c9ee1c66",
                "price": 150
            },

        ],
        "updateDate": "2022-02-16T12:00:00.000Z"
    }

]

CUSTOM_BATCH = [
    {
        "items": [
            {
                "type": "CATEGORY",
                "name": 'Layer0',
                "id": "73bc3b36-02d1-4245-ab35-3106c9ee1c00",
                "parentId": None,

            },
            {
                "type": "CATEGORY",
                "name": 'Layer1',
                "id": "73bc3b36-02d1-4245-ab35-3106c9ee1c10",
                "parentId": "73bc3b36-02d1-4245-ab35-3106c9ee1c00",

            },
            {
                "type": "OFFER",
                "name": "ITEM1",
                "id": "73bc3b36-02d1-4245-ab35-3106c9ee1c20",
                "parentId": "73bc3b36-02d1-4245-ab35-3106c9ee1c10",
                "price": 100
            },
            {
                "type": "OFFER",
                "name": "ITEM2",
                "id": "73bc3b36-02d1-4245-ab35-3106c9ee1c21",
                "parentId": "773bc3b36-02d1-4245-ab35-3106c9ee1c10",
                "price": 200
            },
            {
                "type": "CATEGORY",
                "name": 'Layer1',
                "id": "73bc3b36-02d1-4245-ab35-3106c9ee1c11",
                "parentId": "73bc3b36-02d1-4245-ab35-3106c9ee1c00",

            },
            {
                "type": "OFFER",
                "name": "ITEM2",
                "id": "73bc3b36-02d1-4245-ab35-3106c9ee1c22",
                "parentId": "73bc3b36-02d1-4245-ab35-3106c9ee1c11",
                "price": 300
            },

        ],
        "updateDate": "2022-02-01T12:00:00.000Z"
    }

]

IMPORT_BATCHES = [
    {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Товары",
                "id": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
                "parentId": None
            }
        ],
        "updateDate": "2022-02-01T12:00:00.000Z"
    },
    {
        "items": [
            {
                "type": "OFFER",
                "name": "jPhone 13",
                "id": "863e1a7a-1304-42ae-943b-179184c077e3",
                "parentId": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
                "price": 79999
            },
            {
                "type": "OFFER",
                "name": "Xomiа Readme 10",
                "id": "b1d8fd7d-2ae3-47d5-b2f9-0f094af800d4",
                "parentId": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
                "price": 59999
            },
            {
                "type": "CATEGORY",
                "name": "Смартфоны",
                "id": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
                "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1"
            },

        ],
        "updateDate": "2022-02-02T12:00:00.000Z"
    },
    {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Телевизоры",
                "id": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1"
            },
            {
                "type": "OFFER",
                "name": "Samson 70\" LED UHD Smart",
                "id": "98883e8f-0507-482f-bce2-2fb306cf6483",
                "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                "price": 32999
            },
            {
                "type": "OFFER",
                "name": "Phyllis 50\" LED UHD Smarter",
                "id": "74b81fda-9cdc-4b63-8927-c978afed5cf4",
                "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                "price": 49999
            }
        ],
        "updateDate": "2022-02-03T12:00:00.000Z"
    },
    {
        "items": [
            {
                "type": "OFFER",
                "name": "Goldstar 65\" LED UHD LOL Very Smart",
                "id": "73bc3b36-02d1-4245-ab35-3106c9ee1c65",
                "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                "price": 69999
            }
        ],
        "updateDate": "2022-02-03T15:00:00.000Z"
    }
]

EXPECTED_TREE = {
    "type": "CATEGORY",
    "name": "Товары",
    "id": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
    "price": 58599,
    "parentId": None,
    "date": "2022-02-03T15:00:00.000Z",
    "children": [
        {
            "type": "CATEGORY",
            "name": "Телевизоры",
            "id": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
            "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
            "price": 50999,
            "date": "2022-02-03T15:00:00.000Z",
            "children": [
                {
                    "type": "OFFER",
                    "name": "Samson 70\" LED UHD Smart",
                    "id": "98883e8f-0507-482f-bce2-2fb306cf6483",
                    "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                    "price": 32999,
                    "date": "2022-02-03T12:00:00.000Z",
                    "children": None,
                },
                {
                    "type": "OFFER",
                    "name": "Phyllis 50\" LED UHD Smarter",
                    "id": "74b81fda-9cdc-4b63-8927-c978afed5cf4",
                    "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                    "price": 49999,
                    "date": "2022-02-03T12:00:00.000Z",
                    "children": None
                },
                {
                    "type": "OFFER",
                    "name": "Goldstar 65\" LED UHD LOL Very Smart",
                    "id": "73bc3b36-02d1-4245-ab35-3106c9ee1c65",
                    "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                    "price": 69999,
                    "date": "2022-02-03T15:00:00.000Z",
                    "children": None
                }
            ]
        },
        {
            "type": "CATEGORY",
            "name": "Смартфоны",
            "id": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
            "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
            "price": 69999,
            "date": "2022-02-02T12:00:00.000Z",
            "children": [
                {
                    "type": "OFFER",
                    "name": "jPhone 13",
                    "id": "863e1a7a-1304-42ae-943b-179184c077e3",
                    "parentId": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
                    "price": 79999,
                    "date": "2022-02-02T12:00:00.000Z",
                    "children": None
                },
                {
                    "type": "OFFER",
                    "name": "Xomiа Readme 10",
                    "id": "b1d8fd7d-2ae3-47d5-b2f9-0f094af800d4",
                    "parentId": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
                    "price": 59999,
                    "date": "2022-02-02T12:00:00.000Z",
                    "children": None
                }
            ]
        },
    ]
}


def request(path, method="GET", data=None, json_response=False):
    try:
        params = {
            "url": f"{API_BASEURL}{path}",
            "method": method,
            "headers": {},
        }

        if data:
            params["data"] = json.dumps(
                data, ensure_ascii=False).encode("utf-8")
            params["headers"]["Content-Length"] = len(params["data"])
            params["headers"]["Content-Type"] = "application/json"

        req = urllib.request.Request(**params)

        with urllib.request.urlopen(req) as res:
            res_data = res.read().decode("utf-8")
            if json_response:
                res_data = json.loads(res_data)
            return (res.getcode(), res_data)
    except urllib.error.HTTPError as e:
        return (e.getcode(), None)


async def req(path, method="GET", data=None, json_response=False):
    params = {
        "url": f"{API_BASEURL}{path}",
        "method": method,
        "headers": {},
    }

    if data:
        params["data"] = json.dumps(
            data, ensure_ascii=False).encode("utf-8")
        params["headers"]["Content-Length"] = len(params["data"])
        params["headers"]["Content-Type"] = "application/json"

    async with aiohttp.ClientSession(API_BASEURL) as session:
        if params['method'] == "POST":
            async with session.post(path, json=data) as resp:
                return resp.status, "s"


def deep_sort_children(node):
    if node.get("children"):
        node["children"].sort(key=lambda x: x["id"])

        for child in node["children"]:
            deep_sort_children(child)


def print_diff(expected, response):
    with open("expected.json", "w") as f:
        json.dump(expected, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")

    with open("response.json", "w") as f:
        json.dump(response, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")

    subprocess.run(["git", "--no-pager", "diff", "--no-index",
                    "expected.json", "response.json"])


def test_import():
    for index, batch in enumerate(IMPORT_BATCHES):
        # for index, batch in enumerate(CUSTOM_BATCH):
        print(f"Importing batch {index}")
        status, _ = request("/imports", method="POST", data=batch)

        assert status == 200, f"Expected HTTP status code 200, got {status}"

    print("Test import passed.")


def test_update():
    for index, batch in enumerate(UPDATE_BATCH):
        print(f"Importing batch {index}")
        status, _ = request("/imports", method="POST", data=batch)

        assert status == 200, f"Expected HTTP status code 200, got {status}"

    print("Test update passed.")


def test_nodes():
    status, response = request(f"/nodes/{ROOT_ID}", json_response=True)
    # print(json.dumps(response, indent=2, ensure_ascii=False))

    assert status == 200, f"Expected HTTP status code 200, got {status}"

    deep_sort_children(response)
    deep_sort_children(EXPECTED_TREE)
    if response != EXPECTED_TREE:
        print_diff(EXPECTED_TREE, response)
        print("Response tree doesn't match expected tree.")
        sys.exit(1)

    print("Test nodes passed.")


def test_sales():
    params = urllib.parse.urlencode({
        "date": "2022-02-04T00:00:00.000Z"
    })
    status, response = request(f"/sales?{params}", json_response=True)
    assert status == 200, f"Expected HTTP status code 200, got {status}"
    print("Test sales passed.")


def test_stats():
    params = urllib.parse.urlencode({
        "dateStart": "2022-02-01T00:00:00.000Z",
        "dateEnd": "2022-02-03T00:00:00.000Z"
    })
    status, response = request(
        f"/node/{ROOT_ID}/statistic?{params}", json_response=True)

    assert status == 200, f"Expected HTTP status code 200, got {status}"
    print("Test stats passed.")


def test_delete():
    status, _ = request(f"/delete/{ROOT_ID}", method="DELETE")
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    status, _ = request(f"/nodes/{ROOT_ID}", json_response=True)
    assert status == 404, f"Expected HTTP status code 404, got {status}"

    print("Test delete passed.")


def test_all():
    test_import()
    test_nodes()
    test_sales()
    test_stats()
    test_delete()


def test_stress():
    async def task(task_id, data):
        requests_count = 0
        tic_avg = time.perf_counter()

        for index, batch in enumerate(data):
            status, _ = await req("/imports", method="POST", data=batch)
            requests_count += 1

            assert status == 200, f"Expected HTTP status code 200, got {status}"
        toc_avg = time.perf_counter()
        return f'{task_id} BATCH SIZE: {len(data[0]["items"])} TASK DONE IN: {(toc_avg - tic_avg):.2f}  {len(data[0]["items"]) / (toc_avg - tic_avg):.2f} rps'

    async def asynchronous():
        tasks = 30
        data = [DataGenerator().generate() for _ in range(tasks)]
        futures = [task(i, data[i]) for i in range(tasks)]
        t = time.perf_counter()
        for i, future in enumerate(asyncio.as_completed(futures)):
            result = await future
            print(result)

        print(f'{10 * 100 / (time.perf_counter() - t)}:.2f rps')

    ioloop = asyncio.get_event_loop()
    ioloop.run_until_complete(asynchronous())
    ioloop.close()


def main():
    global API_BASEURL
    test_name = [

        # 'stress',
        # "update",
        # "import",
        # 'nodes',
        # 'sales',
        # "stats",
        # 'delete',
        'all'
    ]

    for arg in sys.argv[1:]:
        if re.match(r"^https?://", arg):
            API_BASEURL = arg
        elif test_name is None:
            test_name = arg

    if API_BASEURL.endswith('/'):
        API_BASEURL = API_BASEURL[:-1]

    if test_name is None:
        test_all()
    else:
        for tn in test_name:
            test_func = globals().get(f"test_{tn}")
            if not test_func:
                print(f"Unknown test: {tn}")
                sys.exit(1)
            test_func()


if __name__ == "__main__":
    main()
