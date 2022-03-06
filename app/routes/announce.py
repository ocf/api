from ..utils.blog import get_blog_posts as real_get_blog_posts

from . import router


@router.get("/announce/blog")
def get_blog_posts():
    return real_get_blog_posts()
