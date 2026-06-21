from fastapi import APIRouter
from fastapi.routing import APIRoute


def tao_router_ke_thua(router: APIRouter, prefix_cu: str, tags: list[str] | None = None) -> APIRouter:
    legacy_router = APIRouter(prefix=prefix_cu, tags=tags or router.tags)
    for route in router.routes:
        if not isinstance(route, APIRoute):
            continue
        path = route.path
        if router.prefix and path.startswith(router.prefix):
            path = path[len(router.prefix) :] or ""
        legacy_router.add_api_route(
            path,
            route.endpoint,
            response_model=route.response_model,
            status_code=route.status_code,
            tags=route.tags,
            dependencies=route.dependencies,
            summary=route.summary,
            description=route.description,
            response_description=route.response_description,
            responses=route.responses,
            deprecated=True,
            methods=route.methods,
            operation_id=route.operation_id,
            response_model_include=route.response_model_include,
            response_model_exclude=route.response_model_exclude,
            response_model_by_alias=route.response_model_by_alias,
            response_model_exclude_unset=route.response_model_exclude_unset,
            response_model_exclude_defaults=route.response_model_exclude_defaults,
            response_model_exclude_none=route.response_model_exclude_none,
            include_in_schema=False,
        )
    return legacy_router
