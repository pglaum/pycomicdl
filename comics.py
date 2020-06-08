#!/usr/bin/env python3

from helpers import page_downloader, single_chapter
import click
import os
import re
import traceback

basedir = os.path.abspath(os.path.dirname(__file__))


@click.group()
@click.option('--debug/--no-debug', default=False)
@click.pass_context
def cli(ctx, debug):

    ctx.ensure_object(dict)
    ctx.obj['DEBUG'] = debug


@cli.command('download')
@click.argument('url')
@click.option('--directory', '-d', default='downloads', help='The directory '
        'to download to')
@click.option('--keep/--no-keep', default=True, help='Keep raw image files '
        'after converting to pdf [Default: True]')
@click.option('--pdf/--no-pdf', default=True, help='Convert images to pdf '
        '[Default: True]')
@click.pass_context
def download(ctx, url, directory, keep, pdf):
    """Downloads a comicbook series or chapter.

    The URL can be a link to a chapter or series on readcomiconline.to.
    If URL leads to a series, all chapters will be downloaded.
    """

    comic_name = url.split('/')[4].strip()
    comic_name = re.sub(r'[0-9][a-z][A-Z]\ ', '', str(comic_name))
    comic_name = str(comic_name.title()).replace('-', ' ')

    url_split = str(url).split('/')

    if len(url_split) in [5]:
        # this is a comicbook series

        click.secho(f'Downloading "{comic_name}"...', fg='green')
        click.secho('All HTML downloads will take some time, because we have to '
                'fool CloudFlare.', fg='yellow')

        click.secho('Getting series url...', fg='green')
        soup, _ = page_downloader(url)

        all_links = []

        listings = soup.find_all('table', {'class': 'listing'})
        for elements in listings:
            links = elements.find_all('a')
            for link in links:
                all_links.append(str(link['href']).strip())

        all_links.reverse()

        for chapter_link in all_links:
            chapter_link = 'http://readcomiconline.to' + chapter_link

            try:
                single_chapter(chapter_link, comic_name, directory, keep, pdf)
            except Exception:
                click.secho('An exception ocurred while trying to download '
                    f'{chapter_link}.', fg='red')
                traceback.print_exc()

    else:

        click.secho(f'Downloading "{comic_name}"...', fg='green')
        click.secho('All HTML downloads will take some time, because we have '
                'to fool CloudFlare.', fg='yellow')

        if '&readType=0' in url:
            # All images on one page
            url = str(url).replace('&readType=0', '&readType=1')

        single_chapter(url, comic_name, directory, keep, pdf)


if __name__ == '__main__':
    cli()
