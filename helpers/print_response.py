import requests


def print_response(resp: requests.Response):
    print(resp.status_code)
    print(resp.headers)
    print(resp.reason)
    print(resp.cookies)
    print(resp.raw)
    print(resp.encoding)
    print(resp.content)
    print(resp.elapsed)
    print(resp.history)
    print(resp.url)
    print(resp.links)
