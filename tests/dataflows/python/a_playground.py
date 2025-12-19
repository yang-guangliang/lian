# def func1():
#     a = source()
#     c = a.b.h
#     m = prop(c)
#     sink(a)
# func1()
# latents_ubyte = (
#     a.mul(0xFF)  # change scale from -1..1 to 0..1  # to 0..255
# ).to(device="cpu", dtype=torch.uint8)
a = s()
b + c


@app.head("/file={path_or_url:path}", dependencies=[Depends(login_check)])
@app.get("/file={path_or_url:path}", dependencies=[Depends(login_check)])
async def file(path_or_url: str, request: fastapi.Request):
    blocks = app.get_blocks()
    if client_utils.is_http_url_like(path_or_url):
        return RedirectResponse(
            url=path_or_url, status_code=status.HTTP_302_FOUND
        )
    abs_path = utils.abspath(path_or_url)

    in_blocklist = any(
        utils.is_in_or_equal(abs_path, blocked_path)
        for blocked_path in blocks.blocked_paths
    )
    is_dir = abs_path.is_dir()

    if in_blocklist or is_dir:
        raise HTTPException(403, f"File not allowed: {path_or_url}.")

    created_by_app = str(abs_path) in set().union(*blocks.temp_file_sets)
    in_allowlist = any(
        utils.is_in_or_equal(abs_path, allowed_path)
        for allowed_path in blocks.allowed_paths
    )
    was_uploaded = utils.is_in_or_equal(abs_path, app.uploaded_file_dir)
    is_cached_example = utils.is_in_or_equal(
        abs_path, utils.abspath(CACHED_FOLDER)
    )

    if not (
        created_by_app or in_allowlist or was_uploaded or is_cached_example
    ):
        raise HTTPException(403, f"File not allowed: {path_or_url}.")

    if not abs_path.exists():
        raise HTTPException(404, f"File not found: {path_or_url}.")

    range_val = request.headers.get("Range", "").strip()
    if range_val.startswith("bytes=") and "-" in range_val:
        range_val = range_val[6:]
        start, end = range_val.split("-")
        if start.isnumeric() and end.isnumeric():
            start = int(start)
            end = int(end)
            response = ranged_response.RangedFileResponse(
                abs_path,
                ranged_response.OpenRange(start, end),
                dict(request.headers),
                stat_result=os.stat(abs_path),
            )
            return response

    return FileResponse(abs_path, headers={"Accept-Ranges": "bytes"})
