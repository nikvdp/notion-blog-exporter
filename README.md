# README.md

I host [my blog](https://nikvdp.com/post) as a static site powered by Hugo, but got tired of writing in markdown files directly.

This tool lets you extracts any pages nested under a page/block of your choice in Notion and converts them into Hugo compatible markdown files.

I use it with a cronjob to automatically post any new or updated blog posts from Notion automatically. 

Proper documentation coming soon. In the meantime, here's how to use it:

You'll need to retrieve your Notion token by inspecting cookies via Chrome dev tools while browsing [notion.so](https://notion.so). The short version: pick a request in the network tab, check the headers it sent, look for the cookie header, and look for `token_v2=` followed by 150 or so letters and numbers.

You'll also need to get the block/page ID for the block or page in notion that you'll be nesting your posts under.

- Then, tell `notion-blog-exporter` how to use them by exporting env vars:

    ```bash
    export NOTION_TOKEN="<your-token>"

    export HUGO_POSTS_FOLDER="<path-to-hugo-folder-with-markdown-files>"

    export NOTION_ROOT_BLOCK="<notion-id-of-block-or-page-with-your-posts>"
    ```

- Install deps using [poetry](https://python-poetry.org/) and activate the virtualenv:

    ```bash
    poetry install && poetry shell
    ```

Now you can run it with `python notion-blog.py`. Markdown files will be written to `HUGO_POSTS_FOLDER`, which you can then deploy however you normally deploy your hugo site.
