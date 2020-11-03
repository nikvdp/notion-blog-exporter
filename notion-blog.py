from dataclasses import dataclass
import yaml
from datetime import datetime
import os
from textwrap import dedent
from textwrap import dedent
from os.path import join as join_path
from notion.client import NotionClient
from notion.block import PageBlock, ImageBlock, TextBlock, \
        CodeBlock, ImageBlock, NumberedListBlock, BulletedListBlock, \
        QuoteBlock, HeaderBlock, SubheaderBlock, SubsubheaderBlock, \
        CalloutBlock
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

blog_post = posts_to_publish[1]



def listblock_to_markdown_handler(block):
    prefix = "- " if isinstance(block, BulletedListBlock) else ""
    prefix = "1. " if isinstance(block, NumberedListBlock) else prefix

    lines = block.title.split("\n")
    output = ""
    for idx, line in enumerate(lines):
        if idx == 0:
            output = f"{output}{prefix}{line}\n"
        else:
            output = f"{output}{' ' * len(prefix)}{line}\n"

    return f"{output}\n"


def blocks_to_markdown(page):
    markdown_out = ""
    for block in blog_post.children:
        markdown_out += block_to_markdown(block) or ""

    with open("/tmp/out.md", "w") as fp:
        fp.write(markdown_out)
    print(markdown_out)
    return markdown_out


def block_to_markdown(block):
    default_handler = lambda block: f"\n{block.title}\n"

    handlers = {
        # TODO: list blocks need to handle indentation for continuing lines
        QuoteBlock: lambda block: "> "
        + "> ".join([f"{x}\n" for x in block.title.split("\n")]),
        NumberedListBlock: listblock_to_markdown_handler,
        BulletedListBlock: listblock_to_markdown_handler,
        HeaderBlock: lambda block: f"# {block.title}",
        SubheaderBlock: lambda block: f"## {block.title}",
        SubsubheaderBlock: lambda block: f"### {block.title}",
        CalloutBlock: lambda block: f"> {block.icon} "
        + "> ".join([f"{x}\n" for x in block.title.split("\n")]),
        # NumberedListBlock: lambda block: f"1. {block.title}\n",
        # BulletedListBlock: lambda block: f"- {block.title}\n",
        CodeBlock: lambda block: f"\n"
        f"```{block.language.lower()}\n"
        f"{block.title}\n"
        "```\n",
    }

    return handlers.get(type(block), default_handler)(block)

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
