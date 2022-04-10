from routes import router
from utils.blog import get_blog_posts as real_get_blog_posts


@router.get("/announce/blog", tags=["misc"])
async def get_blog_posts():
    return real_get_blog_posts()
