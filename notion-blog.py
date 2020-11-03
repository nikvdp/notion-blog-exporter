from dataclasses import dataclass
import yaml
from datetime import datetime
import os
from textwrap import dedent
from textwrap import dedent
from os.path import join as join_path
from notion.client import NotionClient
from notion.block import PageBlock, ImageBlock, TextBlock, CodeBlock, ImageBlock
from typing import List, Optional

# TODO: maybe use puppeteer to grab this going forward?
NOTION_TOKEN = "***REMOVED***"
HUGO_POSTS_LOCATION = (
    "***REMOVED***"
)

client = NotionClient(token_v2=NOTION_TOKEN)

# id of blog posts page: ***REMOVED***

BLOG_POST_PAGE_ID = "***REMOVED***"
# find blog posts page
blog_posts_page = client.get_block(BLOG_POST_PAGE_ID)

published = next(
    filter(lambda x: x.title == "Published", blog_posts_page.children), None
)

posts_to_publish = blog_posts_page.children[0].children

sway_i3 = posts_to_publish[0]

img = sway_i3.children[0]

img.download_file("/tmp/Untitled.png")


def block_to_markdown(block):
    markdown = ""
    if isinstance(block, TextBlock):
        markdown = f"\n{block.title}\n"
    if isinstance(block, CodeBlock):
        markdown = f"\n" \
        f"```{block.language.lower()}\n" \
        f"{block.title}\n" \
        "```"

    return markdown

def read_post():
    published_posts = blog_posts_page.children[0].children

def main():
    hugo_posts = collect_hugo_posts()
    hugo_published = [p for p in hugo_posts if not p.draft]
    # import IPython;IPython.embed()

    # TODO:
    # workflow:
    #   scope:
    #     one way data movement, from notion to hugo
    #     after writing to hugo, need to save an id somewhere. in hugo frontmatter?
    # - iterate over published block in notion
    # - iterate over published files in hugo
    # - if any pages in notion are not published, retrieve from notion and write as hugo
    # - then push the hugo repo


@dataclass
class HugoPost:
    title: str
    date: datetime
    draft: bool
    body: str
    aliases: Optional[List[str]] = None


def collect_hugo_posts():
    md_post_files = [
        p for p in os.listdir(HUGO_POSTS_LOCATION) if p.lower().endswith(".md")
    ]

    posts = []
    for post_file in md_post_files:
        with open(join_path(HUGO_POSTS_LOCATION, post_file)) as pf:
            content = pf.read()
        posts.append(parse_post(content))
    return posts


def parse_post(content) -> HugoPost:
    content = content.split("---")

    front_matter = yaml.safe_load(content[1])

    # join in case there were any other '---' later in file
    body = "\n".join(content[2:])

    return HugoPost(**front_matter, body=body)


main()
