from core.runtime.dispatcher import build_dispatcher


async def test_dispatcher_build_isolation(ctx):
    """Building a dispatcher twice yields independent instances (routers are created fresh each time)."""
    dp1 = build_dispatcher(ctx)
    dp2 = build_dispatcher(ctx)
    assert dp1 is not dp2
    names1 = {r.name for r in dp1.sub_routers}
    names2 = {r.name for r in dp2.sub_routers}
    assert names1 == names2 and "sd_link" in names1
    assert not ({id(r) for r in dp1.sub_routers} & {id(r) for r in dp2.sub_routers})
