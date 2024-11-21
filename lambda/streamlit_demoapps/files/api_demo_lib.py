from typing import Callable

import requests
import streamlit as st


class BadApiCall(RuntimeError):
    """Raised for any bad api response"""

    def __init__(self, msg):
        self.msg = msg


class ApiCaller:
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url

    def api_call(
        self,
        method,
        url,
        headers=None,
        data=None,
        json=None,
        params=None,
        annotation="",
        auth_header_name="Authorization",
        auth_token_prefix="Bearer ",
        spinner_container=None,
    ):
        """Wrapper around requests to log API calls and responses."""
        if headers is None:
            headers = {}

        display_headers = {**headers}
        # Include the bearer token from session state
        if this_auth_token := st.session_state.get("auth_token"):
            if not this_auth_token == "unused":
                headers[auth_header_name] = f"{auth_token_prefix}{this_auth_token}"
                display_headers[auth_header_name] = f"{auth_token_prefix}************"

        if not url.startswith("http"):
            final_url = (
                self.api_base_url.removesuffix("/") + "/" + url.removeprefix("/")
            )
        else:
            final_url = url

        # Make the API request
        if spinner_container:
            with spinner_container.spinner(
                f"Calling API: {method.upper()} {final_url}"
            ):
                response = requests.request(
                    method,
                    final_url,
                    headers=headers,
                    data=data,
                    json=json,
                    params=params,
                )
        else:
            response = requests.request(
                method, final_url, headers=headers, data=data, json=json, params=params
            )

        # Log the API call and response
        st.session_state["api_calls"].append(
            {
                "annotation": annotation,
                "request": {
                    "method": method,
                    "url": final_url,
                    "headers": display_headers,
                    "data": data,
                    "json": json,
                    "params": params,
                },
                "response": {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.json()
                    if "application/json" in response.headers.get("Content-Type", "")
                    else response.text,
                },
            }
        )
        if not response.ok:
            if response.status_code == 401:
                st.error("Bad Auth Token")
                st.stop()
            print(response)
            raise BadApiCall(msg=response.text)

        return response


@st.cache_resource()
def get_api_caller(dev_api_url) -> ApiCaller:
    try:
        import js
    except ImportError:
        base_url = dev_api_url
    else:
        # running in pyodide; set to browser url
        proto, remainder = str(js.location).removeprefix("blob:").split("//")
        hostname_with_port: str = remainder.split("/")[0]
        if hostname_with_port.startswith("localhost"):
            # testing locally with pyodide, so use the dev endpoint
            base_url = dev_api_url
        else:
            base_url = f"{proto}//{hostname_with_port}"
    return ApiCaller(base_url)


def run_demo_app(
    app_title,
    app_description,
    dev_api_url: str,
    main_app_handler: Callable[[ApiCaller], None],
    require_api_key: bool = True,
    api_key_label: str = "Auth Token",
):
    # Initialize session state for API calls

    # APP_TITLE = "ReportTool Interactive API Documentation"
    # APP_DESCRIPTION = "Demonstrating a minimal UI built for interfacing with the Report Tool API"
    if "api_calls" not in st.session_state:
        st.session_state["api_calls"] = []
    api_caller = get_api_caller(dev_api_url)
    st.sidebar.write("API BASE URL")
    st.sidebar.write(api_caller.api_base_url)

    if "last_displayed_step_idx" not in st.session_state:
        st.session_state.last_displayed_step_idx = 0

    if not require_api_key:
        st.session_state.auth_token = "unused"

    if "auth_token" not in st.session_state:
        st.title(app_title)
        st.write(app_description)

        # Bearer token input
        auth_token = st.text_input(f"Enter your {api_key_label}:", type="password")
        if auth_token:
            st.session_state["auth_token"] = auth_token
            st.rerun()
    else:
        main_app_handler(api_caller)

    # Display API interactions in sidebar
    with st.sidebar:
        st.write("## API Interactions")
        for idx, call in enumerate(reversed(st.session_state["api_calls"])):
            # Show annotation and response status code
            call_num = len(st.session_state["api_calls"]) - idx
            session_idx = call_num - 1

            container = st.container(border=True)
            with container:
                st.write(f"### Call {call_num}: {call['annotation']}")
                if session_idx > st.session_state.last_displayed_step_idx:
                    st.info("New call made")
                st.write(
                    f'**{call["request"]["method"].upper()}** {call["request"]["url"].replace(api_caller.api_base_url, "")}'
                )
                if st.button("View", key=f"view_{session_idx}"):
                    view_interaction(session_idx)
                st.write(f"Response Status Code: {call['response']['status_code']}")

                # Popovers for request and response
                col1, col2 = st.columns(2)
                with col1:
                    with st.popover("Request", use_container_width=True):
                        if (
                            request_body := call["request"]["data"]
                            or call["request"]["json"]
                        ):
                            st.write(request_body)
                        if p := call["request"]["params"]:
                            st.write(p)
                with col2:
                    with st.popover("Response", use_container_width=True):
                        response_body = call["response"].get("body")
                        if len(response_body) < 10000:
                            st.write(response_body)
                        else:
                            st.write("Response body too large to show")
        st.session_state.last_displayed_step_idx = (
            len(st.session_state["api_calls"]) - 1
        )


@st.dialog("API Interaction", width="large")
def view_interaction(session_idx: int):
    call = st.session_state["api_calls"][session_idx]
    call_response_body = call["response"].get("body")
    if call_response_body and len(call_response_body) > 10000:
        call["response"]["body"] = f"{call_response_body[:10000]}<body truncated>"
    st.write(call)
