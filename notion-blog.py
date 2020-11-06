#!/usr/bin/env python3
import click
import re
from dataclasses import dataclass, asdict
import yaml
from datetime import datetime
import os
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

from textwrap import dedent
from os.path import join as join_path
from typing import List, Optional
import sys


# TODO: maybe use puppeteer to grab this going forward?
config = None


@dataclass
class GlobalConfigContainer:
    notion_token: str
    hugo_posts_location: str
    notion_client: NotionClient


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
    body: str
    draft: Optional[bool] = False
    aliases: Optional[List[str]] = None

    @classmethod
    def from_blog_post(cls, post: BlogPost):
        field_map = dict(
            title="title", date="date", draft="draft", body="body"
        )

        output = {}
        for k, v in asdict(post).items():
            if k in field_map:
                output[field_map[k]] = v

        return cls(**output)

    def to_hugo(self) -> str:
        front_matter = {
            k: v
            for k, v in asdict(self).items()
            if v is not None and k != "body"
        }
        # TODO: consider supporting non-yaml frontmatter
        as_yaml = yaml.dump(front_matter, default_flow_style=False)
        output = f"---\n{as_yaml}\n---{self.body}"
        return output


def to_valid_filename(string):
    """Converts a string into something usable as a filename

    Adapted from django's get_valid_filename.

    see: https://github.com/django/django/blob/0382ecfe020b4c51b4c01e4e9a21892771e66941/django/utils/text.py#L221-L232
    """

    string = str(string).strip().replace(" ", "_")
    return re.sub(r"(?u)[^-\w.]", "", string)


def collect_notion_posts(
    source_block_or_page_id: str,
) -> List[BlogPost]:
    """Retrieve the list of published posts from Notion

    Args:
        source_block_or_page_id (str): A block or page whose children are the
            blog posts you wish to publish.

    Returns:
        List[BlogPost]: A list of blog posts
    """

    blog_posts_page = config.notion_client.get_block(source_block_or_page_id)

    notion_posts = []
    for post in blog_posts_page.children:
        notion_record = post.get()
        notion_posts.append(
            BlogPost(
                title=post.title,
                body=blocks_to_markdown(post.children),
                date=datetime.fromtimestamp(
                    int(notion_record.get("created_time")) / 1000
                ),
                last_edited=datetime.fromtimestamp(
                    int(notion_record.get("last_edited_time")) / 1000
                ),
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


def collect_hugo_posts():
    md_post_files = [
        p
        for p in os.listdir(config.hugo_posts_location)
        if p.lower().endswith(".md")
    ]

    posts = []
    for post_file in md_post_files:
        with open(join_path(config.hugo_posts_location, post_file)) as pf:
            content = pf.read()
        posts.append(parse_post(content))
    return posts


def parse_post(content) -> HugoPost:
    content = content.split("---")

    front_matter = yaml.safe_load(content[1])

    # join in case there were any other '---' later in file
    body = "\n".join(content[2:])

    return HugoPost(**front_matter, body=body)


class ClickTokenType(click.types.StringParamType):
    """helper to make click show NOTION_TOKEN for
    the argument type when called with -h/--help"""

    name = "notion_token"


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "-p",
    "--hugo-posts-folder",
    prompt="Hugo posts folder",
    envvar="HUGO_POSTS_FOLDER",
    type=click.Path(exists=True, file_okay=False),
)
@click.option(
    "-n",
    "--notion-token",
    prompt="Notion token",
    type=ClickTokenType(),
    envvar="NOTION_TOKEN",
)
@click.option(
    "--notion-root-block",
    prompt="Notion root block to collect blog posts from:",
    envvar="NOTION_ROOT_BLOCK",
)
def main(hugo_posts_folder, notion_token, notion_root_block):

    notion_client = NotionClient(token_v2=notion_token)

    global config
    config = GlobalConfigContainer(
        hugo_posts_location=hugo_posts_folder,
        notion_token=notion_token,
        notion_client=notion_client,
    )

    # TODO: store notion ids as extra metadata in the hugo frontmatter
    #       and use them to to intelligently update even if the title has
    #       changed
    hugo_posts = collect_hugo_posts()
    hugo_published = [p for p in hugo_posts if not p.draft]

    notion_posts = collect_notion_posts(notion_root_block)

    for blog_post in notion_posts:

        # skip empty blocks
        if not blog_post.title:
            continue

        hugo_post = HugoPost.from_blog_post(blog_post)
        blog_output = hugo_post.to_hugo()

        safe_title = f"{to_valid_filename(hugo_post.title)}.md"
        with open(join_path(hugo_posts_folder, safe_title), "w") as fp:
            fp.write(blog_output)

        print(f"Wrote '{safe_title}' to '{hugo_posts_folder}'")


if __name__ == "__main__":
    main()
