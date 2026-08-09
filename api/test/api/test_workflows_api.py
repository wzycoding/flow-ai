#!/usr/bin/env python
# -*- coding: utf-8 -*-
from copy import deepcopy
from uuid import UUID, uuid4

from internal.model import Workflow
from pkg.response import HttpCode


def _build_start_end_graph():
    start_id = str(uuid4())
    end_id = str(uuid4())
    return {
        "nodes": [
            {
                "id": start_id,
                "node_type": "start",
                "title": "开始节点",
                "description": "开始节点",
                "position": {"x": 0, "y": 0},
                "inputs": [
                    {
                        "name": "query",
                        "description": "测试输入",
                        "required": True,
                        "type": "string",
                        "value": {"type": "generated", "content": ""},
                    }
                ],
            },
            {
                "id": end_id,
                "node_type": "end",
                "title": "结束节点",
                "description": "结束节点",
                "position": {"x": 320, "y": 0},
                "outputs": [
                    {
                        "name": "output",
                        "description": "测试输出",
                        "required": True,
                        "type": "string",
                        "value": {
                            "type": "ref",
                            "content": {
                                "ref_node_id": start_id,
                                "ref_var_name": "query",
                            },
                        },
                    }
                ],
            },
        ],
        "edges": [
            {
                "id": str(uuid4()),
                "source": start_id,
                "source_type": "start",
                "source_handle_id": None,
                "target": end_id,
                "target_type": "end",
            }
        ],
    }


def test_workflow_crud_basic_flow(client):
    suffix = uuid4().hex[:8]
    workflow_name = f"pytest_workflow_{suffix}"
    tool_call_name = f"pytest_workflow_{suffix}"
    payload = {
        "name": workflow_name,
        "tool_call_name": tool_call_name,
        "icon": "https://img.aiflowline.cn/blog/20260806162348866.png?imageSlim",
        "description": "pytest创建的工作流",
    }

    create_resp = client.post("/workflows", json=payload)
    assert create_resp.status_code == 200
    assert create_resp.json["code"] == HttpCode.SUCCESS
    workflow_id = create_resp.json["data"]["id"]

    get_resp = client.get(f"/workflows/{workflow_id}")
    assert get_resp.status_code == 200
    assert get_resp.json["code"] == HttpCode.SUCCESS
    assert get_resp.json["data"]["tool_call_name"] == tool_call_name

    graph_resp = client.get(f"/workflows/{workflow_id}/draft-graph")
    assert graph_resp.status_code == 200
    assert graph_resp.json["code"] == HttpCode.SUCCESS
    assert set(graph_resp.json["data"].keys()) >= {"nodes", "edges"}

    delete_resp = client.post(f"/workflows/{workflow_id}/delete")
    assert delete_resp.status_code == 200
    assert delete_resp.json["code"] == HttpCode.SUCCESS


def test_position_only_draft_update_keeps_debug_passed_and_publishable(client, db):
    suffix = uuid4().hex[:8]
    create_resp = client.post("/workflows", json={
        "name": f"pytest_workflow_{suffix}",
        "tool_call_name": f"pytest_workflow_{suffix}",
        "icon": "https://img.aiflowline.cn/blog/20260806162348866.png?imageSlim",
        "description": "pytest创建的工作流",
    })
    assert create_resp.status_code == 200
    workflow_id = create_resp.json["data"]["id"]

    graph = _build_start_end_graph()
    graph_resp = client.post(f"/workflows/{workflow_id}/draft-graph", json=graph)
    assert graph_resp.status_code == 200
    assert graph_resp.json["code"] == HttpCode.SUCCESS

    workflow = db.session.get(Workflow, UUID(workflow_id))
    workflow.is_debug_passed = True
    db.session.flush()

    moved_graph = deepcopy(graph)
    moved_graph["nodes"][0]["position"] = {"x": 120, "y": 80}
    moved_graph["nodes"][1]["position"] = {"x": 520, "y": 80}
    moved_resp = client.post(f"/workflows/{workflow_id}/draft-graph", json=moved_graph)
    assert moved_resp.status_code == 200
    assert moved_resp.json["code"] == HttpCode.SUCCESS

    get_resp = client.get(f"/workflows/{workflow_id}")
    assert get_resp.status_code == 200
    assert get_resp.json["data"]["is_debug_passed"] is True

    publish_resp = client.post(f"/workflows/{workflow_id}/publish")
    assert publish_resp.status_code == 200
    assert publish_resp.json["code"] == HttpCode.SUCCESS


def test_debug_workflow_marks_workflow_as_debug_passed(client):
    suffix = uuid4().hex[:8]
    create_resp = client.post("/workflows", json={
        "name": f"pytest_workflow_{suffix}",
        "tool_call_name": f"pytest_workflow_{suffix}",
        "icon": "https://img.aiflowline.cn/blog/20260806162348866.png?imageSlim",
        "description": "pytest创建的工作流",
    })
    assert create_resp.status_code == 200
    workflow_id = create_resp.json["data"]["id"]

    graph = _build_start_end_graph()
    graph_resp = client.post(f"/workflows/{workflow_id}/draft-graph", json=graph)
    assert graph_resp.status_code == 200
    assert graph_resp.json["code"] == HttpCode.SUCCESS

    debug_resp = client.post(f"/workflows/{workflow_id}/debug", json={"query": "hello"})
    assert debug_resp.status_code == 200
    stream_body = b"".join(debug_resp.response).decode()
    assert "event: workflow" in stream_body
    assert "event: error" not in stream_body

    get_resp = client.get(f"/workflows/{workflow_id}")
    assert get_resp.status_code == 200
    assert get_resp.json["data"]["is_debug_passed"] is True


def test_debug_workflow_streams_failed_node_error(client):
    suffix = uuid4().hex[:8]
    create_resp = client.post("/workflows", json={
        "name": f"pytest_workflow_{suffix}",
        "tool_call_name": f"pytest_workflow_{suffix}",
        "icon": "https://img.aiflowline.cn/blog/20260806162348866.png?imageSlim",
        "description": "pytest创建的工作流",
    })
    assert create_resp.status_code == 200
    workflow_id = create_resp.json["data"]["id"]

    graph = _build_start_end_graph()
    graph_resp = client.post(f"/workflows/{workflow_id}/draft-graph", json=graph)
    assert graph_resp.status_code == 200
    assert graph_resp.json["code"] == HttpCode.SUCCESS

    debug_resp = client.post(f"/workflows/{workflow_id}/debug", json={})
    assert debug_resp.status_code == 200
    stream_body = b"".join(debug_resp.response).decode()
    assert "event: workflow" in stream_body
    assert '"status": "failed"' in stream_body
    assert "query" in stream_body
    assert "event: error" in stream_body

    get_resp = client.get(f"/workflows/{workflow_id}")
    assert get_resp.status_code == 200
    assert get_resp.json["data"]["is_debug_passed"] is False


def test_runtime_draft_update_resets_debug_passed(client, db):
    suffix = uuid4().hex[:8]
    create_resp = client.post("/workflows", json={
        "name": f"pytest_workflow_{suffix}",
        "tool_call_name": f"pytest_workflow_{suffix}",
        "icon": "https://img.aiflowline.cn/blog/20260806162348866.png?imageSlim",
        "description": "pytest创建的工作流",
    })
    assert create_resp.status_code == 200
    workflow_id = create_resp.json["data"]["id"]

    graph = _build_start_end_graph()
    graph_resp = client.post(f"/workflows/{workflow_id}/draft-graph", json=graph)
    assert graph_resp.status_code == 200
    assert graph_resp.json["code"] == HttpCode.SUCCESS

    workflow = db.session.get(Workflow, UUID(workflow_id))
    workflow.is_debug_passed = True
    db.session.flush()

    changed_graph = deepcopy(graph)
    changed_graph["nodes"][1]["title"] = "结束节点_已修改"
    changed_resp = client.post(f"/workflows/{workflow_id}/draft-graph", json=changed_graph)
    assert changed_resp.status_code == 200
    assert changed_resp.json["code"] == HttpCode.SUCCESS

    get_resp = client.get(f"/workflows/{workflow_id}")
    assert get_resp.status_code == 200
    assert get_resp.json["data"]["is_debug_passed"] is False

    publish_resp = client.post(f"/workflows/{workflow_id}/publish")
    assert publish_resp.status_code == 200
    assert publish_resp.json["code"] == HttpCode.FAIL
