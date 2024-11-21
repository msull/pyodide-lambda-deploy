from dataclasses import dataclass
from typing import Any, Dict, List

import streamlit as st

from api_demo_lib import ApiCaller, BadApiCall, run_demo_app


def main(api_caller: "ApiCaller"):
    if st.sidebar.button("Clear Cached Data"):
        get_user_posts.clear()
        get_post_content.clear()
        get_available_posts.clear()
        get_post.clear()
    if st.sidebar.button("Reset Session"):
        st.cache_resource.clear()
        st.cache_data.clear()
        st.session_state.clear()
        st.rerun()

    actions = ["View", "Delete"]
    # posts = get_available_posts(api_caller)

    if "post_select_box_cnt" not in st.session_state:
        st.session_state.post_select_box_cnt = 1

    with st.expander("Create a new post", expanded=False):
        with st.form("submit_post_request", clear_on_submit=True, border=False):
            title = st.text_input("Title")
            body = st.text_area("Body")

            if st.form_submit_button("Submit"):
                try:
                    create_post(
                        api_caller=api_caller,
                        title=title,
                        body=body,
                        userId=1,  # Assume user ID 1 for simplicity
                    )
                    st.session_state.post_select_box_cnt += 1
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating post: {e}")

    st.write("Existing Posts")
    st.button("🔄", on_click=get_user_posts.clear, help="Refresh posts")
    action_placeholder = st.empty()
    with action_placeholder.container():
        cols = st.columns(len(actions))
        for col, action in zip(cols, actions):
            with col:
                st.button(
                    action,
                    key=f"disabled-{action}",
                    disabled=True,
                    help="Select a post to enable",
                    use_container_width=True,
                )

    table_data = []
    posts_for_user = get_user_posts(api_caller)
    for item in posts_for_user:
        this_table_item = {
            "id": item.id,
            "title": item.title,
            "body": item.body,
            "userId": item.userId,
        }
        table_data.append(this_table_item)

    def _handle(handle_action: str, idx: int):
        post = posts_for_user[idx]
        if handle_action == "View":
            dialog_view_post_content(api_caller, post)
        elif handle_action == "Delete":
            dialog_delete_post(api_caller, post)
        else:
            raise ValueError(handle_action)

    if table_data:
        selected = st.dataframe(
            table_data,
            selection_mode="single-row",
            on_select="rerun",
            use_container_width=True,
        )
    else:
        st.write("No current posts")
        selected = {"selection": {}}

    if selected_rows := selected["selection"].get("rows"):
        selected_row_idx = selected_rows[0]
        with action_placeholder.container():
            cols = st.columns(len(actions))
            for col, action in zip(cols, actions):
                with col:
                    st.button(
                        action,
                        key=f"handle-{action}",
                        on_click=_handle,
                        args=(action, selected_row_idx),
                        use_container_width=True,
                    )
            selected_post = posts_for_user[selected_row_idx]
        with st.expander("Selected post object", expanded=True):
            st.json(selected_post.__dict__)


@dataclass
class PostInList:
    id: int
    title: str
    body: str


@dataclass
class Post:
    id: int
    title: str
    body: str
    userId: int


@st.cache_data(show_spinner=False)
def get_user_posts(_api_caller: "ApiCaller") -> List["Post"]:
    response = _api_caller.api_call(
        annotation="List posts by the user",
        method="get",
        url="https://jsonplaceholder.typicode.com/posts?userId=1",
    )
    data = response.json()
    return [parse_post(item) for item in data]


def delete_post(api_caller: "ApiCaller", post_id) -> bytes:
    response = api_caller.api_call(
        annotation="Delete a specific post",
        method="delete",
        url=f"https://jsonplaceholder.typicode.com/posts/{post_id}",
    )
    return response.content


@st.cache_data(show_spinner=False)
def get_post_content(_api_caller: "ApiCaller", post_id) -> Post:
    response = _api_caller.api_call(
        annotation="Get the content of a post",
        method="get",
        url=f"https://jsonplaceholder.typicode.com/posts/{post_id}",
    )
    data = response.json()
    return parse_post(data)


@st.cache_data(show_spinner=False)
def get_available_posts(_api_caller: "ApiCaller") -> List["PostInList"]:
    response = _api_caller.api_call(
        annotation="Get list of posts",
        method="get",
        url="https://jsonplaceholder.typicode.com/posts",
    )
    data = response.json()
    posts = [parse_post_in_list(item) for item in data]
    return posts


@st.cache_data(show_spinner=False)
def get_post(_api_caller: "ApiCaller", post_id) -> "Post":
    response = _api_caller.api_call(
        annotation="Get the details of a specific post",
        method="get",
        url=f"https://jsonplaceholder.typicode.com/posts/{post_id}",
    )
    data = response.json()
    return parse_post(data)


def create_post(api_caller: "ApiCaller", title, body, userId) -> "Post":
    payload = {"title": title, "body": body, "userId": userId}

    response = api_caller.api_call(
        annotation="Creating a new post",
        method="post",
        url="https://jsonplaceholder.typicode.com/posts",
        json=payload,
    )
    get_user_posts.clear()
    data = response.json()
    return parse_post(data)


def parse_post_in_list(data: Dict[str, Any]) -> PostInList:
    return PostInList(
        id=data.get("id", 0),
        title=data.get("title", ""),
        body=data.get("body", ""),
    )


def parse_post(data: Dict[str, Any]) -> Post:
    return Post(
        id=data.get("id", 0),
        title=data.get("title", ""),
        body=data.get("body", ""),
        userId=data.get("userId", 0),
    )


@st.dialog("Post Content", width="large")
def dialog_view_post_content(api_caller: "ApiCaller", post):
    st.write("Post Details")
    st.write(f"Title: {post.title}")
    st.write(f"Body: {post.body}")


@st.dialog("Delete Post", width="large")
def dialog_delete_post(api_caller: "ApiCaller", post):
    st.warning("Would you like to delete the following post?")
    st.write(post.__dict__)

    if st.button("Confirm Delete", type="primary", use_container_width=True):
        try:
            get_user_posts.clear()
            delete_post(api_caller, post.id)
            st.rerun()
        except BadApiCall as e:
            st.error(e.msg)


if __name__ == "__main__":
    run_demo_app(
        app_title="JSONPlaceholder Interactive API Demo",
        app_description="Demonstrating a minimal UI built for interfacing with the JSONPlaceholder API",
        main_app_handler=main,
        dev_api_url="https://jsonplaceholder.typicode.com/",
        require_api_key=False,
    )
