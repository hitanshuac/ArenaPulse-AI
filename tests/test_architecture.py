from pytest_archon import archrule


def test_models_layer_independence():
    """Models layer should be pure data structures and not import business logic or state."""
    (
        archrule("models_independence")
        .match("src.domain.models")
        .should_not_import("src.domain.state", "src.domain.physics", "src.domain.agent", "src.routers")
        .check("src")
    )


def test_physics_engine_independence():
    """Physics engine should be pure functions and not import state manager or routers."""
    (
        archrule("physics_independence")
        .match("src.domain.physics")
        .should_not_import("src.domain.state", "src.domain.agent", "src.routers")
        .check("src")
    )


def test_state_manager_independence():
    """State manager should not import from agent or routers."""
    (
        archrule("state_independence")
        .match("src.domain.state")
        .should_not_import("src.domain.agent", "src.routers")
        .check("src")
    )


def test_router_boundary():
    """Domain layer should not import anything from the UI/Router layer."""
    (archrule("router_boundary").match("src.domain*").should_not_import("src.routers").check("src"))
