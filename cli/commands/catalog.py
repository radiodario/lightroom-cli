import json

import click

from cli.decorators import json_input_options
from cli.helpers import execute_command
from cli.output import OutputFormatter


@click.group()
def catalog():
    """Catalog commands (list, search, find, get-selected, get-info, set-rating, add-keywords, etc.)"""
    pass


@catalog.command("get-selected")
@json_input_options
@click.pass_context
def get_selected(ctx, **kwargs):
    """Get currently selected photos"""
    execute_command(ctx, "catalog.getSelectedPhotos", {})


@catalog.command("list")
@click.option("--limit", default=50, type=int, help="Max photos to return")
@click.option("--offset", default=0, type=int, help="Offset for pagination")
@json_input_options
@click.pass_context
def list_photos(ctx, limit, offset, **kwargs):
    """List photos in catalog"""
    execute_command(ctx, "catalog.getAllPhotos", {"limit": limit, "offset": offset}, timeout=60.0)


@catalog.command("search")
@click.argument("query")
@click.option("--limit", default=50, type=int)
@click.option("--offset", default=0, type=int, help="Result offset for pagination")
@json_input_options
@click.pass_context
def search(ctx, query, limit, offset, **kwargs):
    """Search photos by keyword"""
    criteria = {"query": query}
    execute_command(ctx, "catalog.searchPhotos", {"criteria": criteria, "limit": limit, "offset": offset}, timeout=60.0)


@catalog.command("get-info")
@click.argument("photo_id")
@json_input_options
@click.pass_context
def get_info(ctx, photo_id, **kwargs):
    """Get detailed info for a photo"""
    execute_command(ctx, "catalog.getPhotoMetadata", {"photoId": photo_id})


@catalog.command("set-rating")
@click.argument("photo_id")
@click.argument("rating", type=click.IntRange(0, 5))
@click.option("--dry-run", is_flag=True, default=False, help="Preview without executing")
@json_input_options
@click.pass_context
def set_rating(ctx, photo_id, rating, dry_run, **kwargs):
    """Set photo rating (0-5)"""
    execute_command(ctx, "catalog.setRating", {"photoId": photo_id, "rating": rating})


@catalog.command("add-keywords")
@click.argument("photo_id")
@click.argument("keywords", nargs=-1, required=True)
@click.option("--dry-run", is_flag=True, default=False, help="Preview without executing")
@json_input_options
@click.pass_context
def add_keywords(ctx, photo_id, keywords, dry_run, **kwargs):
    """Add keywords to a photo"""
    execute_command(ctx, "catalog.addKeywords", {"photoId": photo_id, "keywords": list(keywords)})


@catalog.command("set-flag")
@click.argument("photo_id")
@click.argument("flag", type=click.Choice(["pick", "reject", "none"]))
@click.option("--dry-run", is_flag=True, default=False, help="Preview without executing")
@json_input_options
@click.pass_context
def set_flag(ctx, photo_id, flag, dry_run, **kwargs):
    """Set photo flag (pick/reject/none)"""
    flag_map = {"pick": 1, "reject": -1, "none": 0}
    execute_command(ctx, "catalog.setFlag", {"photoId": photo_id, "flag": flag_map[flag]})


@catalog.command("get-flag")
@click.argument("photo_id")
@json_input_options
@click.pass_context
def get_flag(ctx, photo_id, **kwargs):
    """Get photo flag status"""
    execute_command(ctx, "catalog.getFlag", {"photoId": photo_id})


@catalog.command("find")
@click.option("--flag", type=click.Choice(["pick", "reject", "none"]), help="Flag condition")
@click.option("--rating", type=int, help="Rating (0-5)")
@click.option(
    "--rating-op",
    default="==",
    type=click.Choice(["==", ">=", "<=", ">", "<"]),
    help="Rating comparison operator",
)
@click.option("--color-label", help="Color label (red/yellow/green/blue/purple/none)")
@click.option("--camera", help="Camera model name")
@click.option("--folder-path", help="Folder path (substring match)")
@click.option("--capture-date-from", help="Capture date from (YYYY-MM-DD or ISO 8601)")
@click.option("--capture-date-to", help="Capture date to (YYYY-MM-DD or ISO 8601, inclusive)")
@click.option("--file-format", help="File format (RAW/DNG/JPEG)")
@click.option("--keyword", "keyword_filter", help="Keyword (substring match)")
@click.option("--filename", help="Filename (substring match)")
@click.option("--limit", default=50, type=int, help="Max results")
@click.option("--offset", default=0, type=int, help="Offset for pagination")
@json_input_options
@click.pass_context
def find_photos(
    ctx,
    flag,
    rating,
    rating_op,
    color_label,
    camera,
    folder_path,
    capture_date_from,
    capture_date_to,
    file_format,
    keyword_filter,
    filename,
    limit,
    offset,
    **kwargs,
):
    """Find photos by structured criteria"""
    search_desc = {}
    if flag:
        search_desc["flag"] = flag
    if rating is not None:
        search_desc["rating"] = rating
        search_desc["ratingOp"] = rating_op
    if color_label:
        search_desc["colorLabel"] = color_label
    if camera:
        search_desc["camera"] = camera
    if folder_path:
        search_desc["folderPath"] = folder_path
    if capture_date_from:
        search_desc["captureDateFrom"] = capture_date_from
    if capture_date_to:
        search_desc["captureDateTo"] = capture_date_to
    if file_format:
        search_desc["fileFormat"] = file_format
    if keyword_filter:
        search_desc["keyword"] = keyword_filter
    if filename:
        search_desc["filename"] = filename

    execute_command(
        ctx,
        "catalog.findPhotos",
        {"searchDesc": search_desc, "limit": limit, "offset": offset},
    )


@catalog.command("select")
@click.argument("photo_ids", nargs=-1, required=True)
@click.option("--dry-run", is_flag=True, default=False, help="Preview without executing")
@json_input_options
@click.pass_context
def select_photos(ctx, photo_ids, dry_run, **kwargs):
    """Select photos by ID"""
    execute_command(ctx, "catalog.setSelectedPhotos", {"photoIds": list(photo_ids)})


@catalog.command("find-by-path")
@click.argument("path")
@json_input_options
@click.pass_context
def find_by_path(ctx, path, **kwargs):
    """Find photo by file path"""
    execute_command(ctx, "catalog.findPhotoByPath", {"path": path})


@catalog.command("collections")
@json_input_options
@click.pass_context
def collections(ctx, **kwargs):
    """List collections (with IDs and parent sets) and collection sets"""
    execute_command(ctx, "catalog.getCollections", {})


@catalog.command("collection-photos")
@click.argument("collection_id", type=int)
@click.option("--limit", default=500, type=int, help="Max photos to return")
@click.option("--offset", default=0, type=int, help="Offset for pagination")
@json_input_options
@click.pass_context
def collection_photos(ctx, collection_id, limit, offset, **kwargs):
    """Get photos from a specific collection"""
    execute_command(
        ctx,
        "catalog.getCollectionPhotos",
        {"collectionId": collection_id, "limit": limit, "offset": offset},
        timeout=60.0,
    )


@catalog.command("develop-presets")
@click.option("--query", default=None, help="Search query to filter presets by name")
@json_input_options
@click.pass_context
def develop_presets(ctx, query, **kwargs):
    """List or search develop presets"""
    params = {}
    if query:
        params["query"] = query
    execute_command(ctx, "catalog.getDevelopPresets", params)


@catalog.command("keywords")
@json_input_options
@click.pass_context
def keywords(ctx, **kwargs):
    """List keywords in catalog"""
    execute_command(ctx, "catalog.getKeywords", {})


@catalog.command("folders")
@click.option("--recursive", is_flag=True, help="Include subfolders")
@json_input_options
@click.pass_context
def folders(ctx, recursive, **kwargs):
    """List folders in catalog"""
    execute_command(ctx, "catalog.getFolders", {"includeSubfolders": recursive})


@catalog.command("set-title")
@click.argument("photo_id")
@click.argument("title")
@click.option("--dry-run", is_flag=True, default=False, help="Preview without executing")
@json_input_options
@click.pass_context
def set_title(ctx, photo_id, title, dry_run, **kwargs):
    """Set photo title"""
    execute_command(ctx, "catalog.setTitle", {"photoId": photo_id, "title": title})


@catalog.command("set-caption")
@click.argument("photo_id")
@click.argument("caption")
@click.option("--dry-run", is_flag=True, default=False, help="Preview without executing")
@json_input_options
@click.pass_context
def set_caption(ctx, photo_id, caption, dry_run, **kwargs):
    """Set photo caption"""
    execute_command(ctx, "catalog.setCaption", {"photoId": photo_id, "caption": caption})


@catalog.command("set-color-label")
@click.argument("photo_id")
@click.argument("label", type=click.Choice(["red", "yellow", "green", "blue", "purple", "none"]))
@click.option("--dry-run", is_flag=True, default=False, help="Preview without executing")
@json_input_options
@click.pass_context
def set_color_label(ctx, photo_id, label, dry_run, **kwargs):
    """Set photo color label"""
    execute_command(ctx, "catalog.setColorLabel", {"photoId": photo_id, "label": label})


@catalog.command("batch-metadata")
@click.argument("photo_ids", nargs=-1, required=True)
@click.option(
    "--keys",
    default="fileName,dateTimeOriginal,rating",
    help="Comma-separated metadata keys",
)
@json_input_options
@click.pass_context
def batch_metadata(ctx, photo_ids, keys, **kwargs):
    """Get formatted metadata for multiple photos"""
    execute_command(
        ctx,
        "catalog.batchGetFormattedMetadata",
        {"photoIds": list(photo_ids), "keys": keys.split(",")},
    )


@catalog.command("rotate-left")
@click.option("--dry-run", is_flag=True, default=False, help="Preview without executing")
@json_input_options
@click.pass_context
def rotate_left(ctx, dry_run, **kwargs):
    """Rotate selected photo left"""
    execute_command(ctx, "catalog.rotateLeft", {})


@catalog.command("rotate-right")
@click.option("--dry-run", is_flag=True, default=False, help="Preview without executing")
@json_input_options
@click.pass_context
def rotate_right(ctx, dry_run, **kwargs):
    """Rotate selected photo right"""
    execute_command(ctx, "catalog.rotateRight", {})


@catalog.command("create-virtual-copy")
@click.option("--dry-run", is_flag=True, default=False, help="Preview without executing")
@json_input_options
@click.pass_context
def create_virtual_copy(ctx, dry_run, **kwargs):
    """Create virtual copy of selected photo"""
    execute_command(ctx, "catalog.createVirtualCopy", {})


@catalog.command("set-metadata")
@click.argument("photo_id")
@click.argument("key")
@click.argument("value")
@click.option("--dry-run", is_flag=True, default=False, help="Preview without executing")
@json_input_options
@click.pass_context
def set_metadata(ctx, photo_id, key, value, dry_run, **kwargs):
    """Set arbitrary metadata key/value for a photo"""
    execute_command(ctx, "catalog.setMetadata", {"photoId": photo_id, "key": key, "value": value})


def _parent_option(func):
    """--parent-id / --parent-name options shared by collection commands"""
    func = click.option("--parent-name", default=None, help="Exact name of the parent collection set")(func)
    func = click.option("--parent-id", type=int, default=None, help="ID of the parent collection set")(func)
    return func


def _with_parent(params, parent_id, parent_name):
    if parent_id is not None:
        params["parentId"] = parent_id
    if parent_name is not None:
        params["parentName"] = parent_name
    return params


def _require_confirm(ctx, confirm, dry_run, example):
    """Return True when the command may proceed; otherwise print CONFIRMATION_REQUIRED and exit 2."""
    if confirm or dry_run:
        return True
    fmt = ctx.obj.get("output", "text") if ctx.obj else "text"
    click.echo(
        OutputFormatter.format_error(
            "This operation is irreversible. Pass --confirm to proceed.",
            fmt,
            code="CONFIRMATION_REQUIRED",
            suggestions=[
                f"Add --confirm flag: {example} --confirm",
                f"Use --dry-run first to preview: {example} --dry-run",
            ],
        ),
        err=True,
    )
    ctx.exit(2)
    return False


@catalog.command("create-collection")
@click.argument("name")
@_parent_option
@click.option("--dry-run", is_flag=True, default=False, help="Preview without executing")
@json_input_options
@click.pass_context
def create_collection(ctx, name, parent_id, parent_name, dry_run, **kwargs):
    """Create a collection, optionally inside a collection set (idempotent)"""
    execute_command(ctx, "catalog.createCollection", _with_parent({"name": name}, parent_id, parent_name))


@catalog.command("create-smart-collection")
@click.argument("name")
@click.option("--search-desc", default=None, help="JSON search descriptor")
@click.option("--dry-run", is_flag=True, default=False, help="Preview without executing")
@json_input_options
@click.pass_context
def create_smart_collection(ctx, name, search_desc, dry_run, **kwargs):
    """Create a smart collection"""
    params = {"name": name}
    if search_desc:
        try:
            params["searchDesc"] = json.loads(search_desc)
        except json.JSONDecodeError as e:
            click.echo(OutputFormatter.format_error(f"Invalid JSON for --search-desc: {e}"))
            ctx.exit(1)
            return
    execute_command(ctx, "catalog.createSmartCollection", params)


@catalog.command("create-collection-set")
@click.argument("name")
@_parent_option
@click.option("--dry-run", is_flag=True, default=False, help="Preview without executing")
@json_input_options
@click.pass_context
def create_collection_set(ctx, name, parent_id, parent_name, dry_run, **kwargs):
    """Create a collection set, optionally inside another set (idempotent)"""
    execute_command(ctx, "catalog.createCollectionSet", _with_parent({"name": name}, parent_id, parent_name))


def _collection_target_options(func):
    """--collection-id / --collection (+ parent) options for membership commands"""
    func = _parent_option(func)
    func = click.option("--collection", "collection_name", default=None, help="Exact collection name")(func)
    func = click.option("--collection-id", type=int, default=None, help="Collection ID")(func)
    return func


def _membership_params(photo_ids, collection_id, collection_name, parent_id, parent_name):
    params = {"photoIds": list(photo_ids)}
    if collection_id is not None:
        params["collectionId"] = collection_id
    if collection_name is not None:
        params["collectionName"] = collection_name
    return _with_parent(params, parent_id, parent_name)


@catalog.command("add-to-collection")
@click.argument("photo_ids", nargs=-1, required=True)
@_collection_target_options
@click.option("--dry-run", is_flag=True, default=False, help="Preview without executing")
@json_input_options
@click.pass_context
def add_to_collection(ctx, photo_ids, collection_id, collection_name, parent_id, parent_name, dry_run, **kwargs):
    """Add photos to a collection (--collection-id, or --collection NAME [--parent-name SET])"""
    execute_command(
        ctx,
        "catalog.addPhotosToCollection",
        _membership_params(photo_ids, collection_id, collection_name, parent_id, parent_name),
        timeout=60.0,
    )


@catalog.command("remove-from-collection")
@click.argument("photo_ids", nargs=-1, required=True)
@_collection_target_options
@click.option("--dry-run", is_flag=True, default=False, help="Preview without executing")
@json_input_options
@click.pass_context
def remove_from_collection(ctx, photo_ids, collection_id, collection_name, parent_id, parent_name, dry_run, **kwargs):
    """Remove photos from a collection (photos stay in the catalog)"""
    execute_command(
        ctx,
        "catalog.removePhotosFromCollection",
        _membership_params(photo_ids, collection_id, collection_name, parent_id, parent_name),
        timeout=60.0,
    )


@catalog.command("delete-collection")
@click.argument("collection_id", type=int)
@click.option("--confirm", is_flag=True, default=False, help="Required confirmation flag")
@click.option("--dry-run", is_flag=True, default=False, help="Preview without executing")
@json_input_options
@click.pass_context
def delete_collection(ctx, collection_id, confirm, dry_run, **kwargs):
    """Delete a collection (photos stay in the catalog, requires --confirm)"""
    if not _require_confirm(ctx, confirm, dry_run, f"lr catalog delete-collection {collection_id}"):
        return
    execute_command(ctx, "catalog.deleteCollection", {"collectionId": collection_id})


@catalog.command("delete-collection-set")
@click.argument("collection_set_id", type=int)
@click.option("--confirm", is_flag=True, default=False, help="Required confirmation flag")
@click.option("--dry-run", is_flag=True, default=False, help="Preview without executing")
@json_input_options
@click.pass_context
def delete_collection_set(ctx, collection_set_id, confirm, dry_run, **kwargs):
    """Delete an empty collection set (requires --confirm)"""
    if not _require_confirm(ctx, confirm, dry_run, f"lr catalog delete-collection-set {collection_set_id}"):
        return
    execute_command(ctx, "catalog.deleteCollectionSet", {"collectionSetId": collection_set_id})


@catalog.command("create-keyword")
@click.argument("keyword")
@click.option("--dry-run", is_flag=True, default=False, help="Preview without executing")
@json_input_options
@click.pass_context
def create_keyword(ctx, keyword, dry_run, **kwargs):
    """Create a keyword in catalog"""
    execute_command(ctx, "catalog.createKeyword", {"keyword": keyword})


@catalog.command("remove-keyword")
@click.argument("photo_id")
@click.argument("keyword")
@click.option("--dry-run", is_flag=True, default=False, help="Preview without executing")
@json_input_options
@click.pass_context
def remove_keyword(ctx, photo_id, keyword, dry_run, **kwargs):
    """Remove keyword from a photo"""
    execute_command(ctx, "catalog.removeKeyword", {"photoId": photo_id, "keyword": keyword})


@catalog.command("set-view-filter")
@click.option("--filter", "filter_json", required=True, help="JSON filter descriptor")
@click.option("--dry-run", is_flag=True, default=False, help="Preview without executing")
@json_input_options
@click.pass_context
def set_view_filter(ctx, filter_json, dry_run, **kwargs):
    """Set view filter"""
    try:
        filter_data = json.loads(filter_json)
    except json.JSONDecodeError as e:
        click.echo(OutputFormatter.format_error(f"Invalid JSON for --filter: {e}"))
        ctx.exit(1)
        return
    execute_command(ctx, "catalog.setViewFilter", {"filter": filter_data})


@catalog.command("get-view-filter")
@json_input_options
@click.pass_context
def get_view_filter(ctx, **kwargs):
    """Get current view filter"""
    execute_command(ctx, "catalog.getCurrentViewFilter", {})


@catalog.command("remove-from-catalog")
@click.argument("photo_id")
@click.option(
    "--confirm",
    is_flag=True,
    default=False,
    help="Required confirmation flag (this operation is irreversible)",
)
@click.option("--dry-run", is_flag=True, default=False, help="Preview without executing")
@json_input_options
@click.pass_context
def remove_from_catalog(ctx, photo_id, confirm, dry_run, **kwargs):
    """Remove photo from catalog (irreversible, requires --confirm)"""
    if not confirm and not dry_run:
        fmt = ctx.obj.get("output", "text") if ctx.obj else "text"
        click.echo(
            OutputFormatter.format_error(
                "This operation is irreversible. Pass --confirm to proceed.",
                fmt,
                code="CONFIRMATION_REQUIRED",
                suggestions=[
                    "Add --confirm flag: lr catalog remove-from-catalog PHOTO_ID --confirm",
                    "Use --dry-run first to preview: lr catalog remove-from-catalog PHOTO_ID --dry-run",
                ],
            ),
            err=True,
        )
        ctx.exit(2)
        return
    execute_command(ctx, "catalog.removeFromCatalog", {"photoId": photo_id})
