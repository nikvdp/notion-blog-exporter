from dataclasses import dataclass
import yaml
from datetime import datetime
import os
from textwrap import dedent
from textwrap import dedent
from os.path import join as join_path
from notion.client import NotionClient
from notion.block import (
    PageBlock,
    ImageBlock,
    TextBlock,
    CodeBlock,
    ImageBlock,
    NumberedListBlock,
    BulletedListBlock,
    QuoteBlock,
    HeaderBlock,
    SubheaderBlock,
    SubsubheaderBlock,
    CalloutBlock,
)
from typing import List, Optional


# TODO: maybe use puppeteer to grab this going forward?
NOTION_TOKEN = "***REMOVED***"
HUGO_POSTS_LOCATION = (
    "***REMOVED***"
)

client = NotionClient(token_v2=NOTION_TOKEN)


def collect_notion_posts(
    source_block_or_page_id: str = "***REMOVED***",
) -> List[BlogPost]:
    """Retrieve the list of published posts from Notion

    Args:
        source_block_or_page_id (str): A block or page whose children are the
            blog posts you wish to publish.

    Returns:
        List[BlogPost]: A list of blog posts
    """
    # id of blog posts page: ***REMOVED***

    # find blog posts page
    blog_posts_page = client.get_block(source_block_or_page_id)

    notion_posts = []
    for post in blog_posts_page.children:
        notion_record = post.get()
        notion_posts.append(
            BlogPost(
                title=post.title,
                body=blocks_to_markdown(post.children),
                date=notion_record.get("created_time"),
            )
        )

    return notion_posts


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


def blocks_to_markdown(root_block):
    markdown_out = ""
    for block in root_block:
        markdown_out += block_to_markdown(block) or ""

    return markdown_out


def block_to_markdown(block):
    default_handler = lambda block: f"{block.title}\n"

    handlers = {
        # TODO: list blocks need to handle indentation for continuing lines
        QuoteBlock: lambda block: "> "
        + "> ".join([f"{x}\n" for x in block.title.split("\n")]),
        NumberedListBlock: listblock_to_markdown_handler,
        BulletedListBlock: listblock_to_markdown_handler,
        HeaderBlock: lambda block: f"\n# {block.title}\n",
        SubheaderBlock: lambda block: f"\n## {block.title}\n",
        SubsubheaderBlock: lambda block: f"\n### {block.title}\n",
        CalloutBlock: lambda block: f"> {block.icon} "
        + "> ".join([f"{x}\n" for x in block.title.split("\n")]),
        CodeBlock: lambda block: f"\n```{block.language.lower()}\n{block.title}\n```\n",
        ImageBlock: lambda block: f"\n `<an-image-goes-here>` \n",
    }

    return handlers.get(type(block), default_handler)(block)


def main():
    hugo_posts = collect_hugo_posts()
    hugo_published = [p for p in hugo_posts if not p.draft]

    notion_posts = collect_notion_posts()
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
class BlogPost:
    title: str
    date: datetime
    body: str
    draft: Optional[bool] = None
    last_edited: Optional[datetime] = None
    metadata: Optional[any] = None


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
